"""Tests for AIPresenter — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.ai_presenter import AIPresenter

# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _MockProvider:
    def __init__(self, response: str = "ok", raises: Exception | None = None):
        self.available = True
        self.calls: list[tuple] = []
        self._response = response
        self._raises = raises

    def chat(self, messages, system=""):
        self.calls.append((messages, system))
        if self._raises:
            raise self._raises
        return self._response


class _MockView:
    def __init__(self):
        self.messages: list[tuple[str, str]] = []
        self.busy_states: list[bool] = []

    def append_message(self, role, content):
        self.messages.append((role, content))

    def set_busy(self, busy):
        self.busy_states.append(busy)


def _item(name: str = "file.txt", size: int = 42) -> FileItem:
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=size, modified=0.0)


def _make(response: str = "ok", raises: Exception | None = None):
    provider = _MockProvider(response=response, raises=raises)
    view = _MockView()
    presenter = AIPresenter(view, provider)
    return presenter, view, provider


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_noop_provider_shows_not_configured():
    provider = _MockProvider()
    provider.available = False
    view = _MockView()
    presenter = AIPresenter(view, provider)

    presenter.send("hello")

    assert any("not configured" in m[1].lower() for m in view.messages)
    assert provider.calls == []


def test_send_appends_user_message_immediately():
    presenter, view, _ = _make()

    presenter.send("hello")
    presenter.shutdown()

    # user message must appear before drain
    assert ("user", "hello") in view.messages


def test_drain_delivers_response():
    presenter, view, _ = _make(response="nice response")

    presenter.send("hello")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    roles = [m[0] for m in view.messages]
    contents = [m[1] for m in view.messages]
    assert "assistant" in roles
    assert "nice response" in contents


def test_drain_delivers_error():
    presenter, view, _ = _make(raises=RuntimeError("boom"))

    presenter.send("hello")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    roles = [m[0] for m in view.messages]
    contents = [m[1] for m in view.messages]
    assert "error" in roles
    assert any("boom" in c for c in contents)


def test_set_context_in_system():
    presenter, _view, provider = _make()

    presenter.set_context(Path("/home/user/docs"), [_item("report.pdf")])
    presenter.send("help")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    assert provider.calls, "chat() was not called"
    _, system = provider.calls[0]
    assert "/home/user/docs" in system
    assert "report.pdf" in system


def test_suggest_rename_includes_filename():
    presenter, view, _provider = _make()

    presenter.suggest_rename(_item("old_name.txt"))
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    all_content = " ".join(m[1] for m in view.messages)
    assert "old_name.txt" in all_content


def test_explain_file_includes_name_and_size():
    presenter, view, _provider = _make()

    presenter.explain_file(_item("data.csv", size=1234))
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    all_content = " ".join(m[1] for m in view.messages)
    assert "data.csv" in all_content
    assert "1234" in all_content


def test_history_accumulates():
    """Second send must include prior user+assistant exchange in messages."""
    provider = _MockProvider(response="first answer")
    view = _MockView()
    presenter = AIPresenter(view, provider)

    presenter.send("first question")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    # Reset pool for second send
    from concurrent.futures import ThreadPoolExecutor
    presenter._pool = ThreadPoolExecutor(max_workers=1)

    presenter.send("second question")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    assert len(provider.calls) == 2
    second_messages = provider.calls[1][0]
    # user, assistant, user
    assert len(second_messages) == 3
    assert second_messages[0]["role"] == "user"
    assert second_messages[1]["role"] == "assistant"
    assert second_messages[2]["role"] == "user"


def test_set_busy_true_before_drain_false_after():
    presenter, view, _ = _make()

    presenter.send("hi")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    assert True in view.busy_states
    assert False in view.busy_states
    # busy=True must come before busy=False
    first_true = view.busy_states.index(True)
    first_false = view.busy_states.index(False)
    assert first_true < first_false
