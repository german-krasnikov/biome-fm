"""Tests for AIPresenter — pure Python, no Qt."""
from __future__ import annotations

import base64
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from biome_fm.models.file_item import FileItem
from biome_fm.presenters.ai_presenter import (
    AIPresenter,
    Attachment,
    MAX_FILE_BYTES,
    MAX_ATTACHMENTS,
)


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------

class _MockProvider:
    name = "mock"
    models = ["mock-model"]
    active_model = "mock-model"

    def __init__(self, tokens=("ok",), raises=None):
        self.available = True
        self.stream_calls: list[tuple] = []
        self._tokens = tokens
        self._raises = raises
        self._model = "mock-model"

    def chat(self, messages, system=""):
        return " ".join(self._tokens)

    def chat_stream(self, messages, system=""):
        self.stream_calls.append((messages, system))
        if self._raises:
            raise self._raises
        yield from self._tokens

    def set_model(self, model):
        self._model = model


class _MockView:
    def __init__(self):
        self.messages: list[tuple[str, str]] = []
        self.busy_states: list[bool] = []
        self.tokens: list[str] = []
        self.finalized: int = 0
        self.chips: list[str] = []
        self.chips_cleared: int = 0
        self.provider_lists: list[tuple] = []

    def append_message(self, role, content):
        self.messages.append((role, content))

    def set_busy(self, busy):
        self.busy_states.append(busy)

    def append_token(self, token):
        self.tokens.append(token)

    def finalize_stream(self):
        self.finalized += 1

    def add_attachment_chip(self, name):
        self.chips.append(name)

    def clear_attachment_chips(self):
        self.chips_cleared += 1
        self.chips.clear()

    def set_provider_list(self, providers, active, models, active_model):
        self.provider_lists.append((providers, active, models, active_model))


def _item(name="file.txt", size=42):
    return FileItem(name=name, path=Path(f"/tmp/{name}"), is_dir=False, size=size, modified=0.0)


def _make(tokens=("ok",), raises=None):
    provider = _MockProvider(tokens=tokens, raises=raises)
    view = _MockView()
    presenter = AIPresenter(view, {"mock": provider}, "mock")
    return presenter, view, provider


def _drain_after(presenter):
    presenter._pool.shutdown(wait=True)
    presenter.drain()


# ---------------------------------------------------------------------------
# Original tests (adapted to new interface)
# ---------------------------------------------------------------------------

def test_noop_provider_shows_not_configured():
    provider = _MockProvider()
    provider.available = False
    view = _MockView()
    presenter = AIPresenter(view, {"mock": provider}, "mock")

    presenter.send("hello")

    assert any("not configured" in m[1].lower() for m in view.messages)
    assert provider.stream_calls == []


def test_send_appends_user_message_immediately():
    presenter, view, _ = _make()

    presenter.send("hello")
    presenter.shutdown()

    assert ("user", "hello") in view.messages


def test_drain_delivers_response():
    presenter, view, _ = _make(tokens=("nice response",))

    presenter.send("hello")
    _drain_after(presenter)

    assert "nice response" in view.tokens


def test_drain_delivers_error():
    presenter, view, _ = _make(raises=RuntimeError("boom"))

    presenter.send("hello")
    _drain_after(presenter)

    roles = [m[0] for m in view.messages]
    contents = [m[1] for m in view.messages]
    assert "error" in roles
    assert any("boom" in c for c in contents)


def test_set_context_in_system():
    presenter, _view, provider = _make()

    presenter.set_context(Path("/home/user/docs"), [_item("report.pdf")])
    presenter.send("help")
    _drain_after(presenter)

    assert provider.stream_calls, "chat_stream() was not called"
    _, system = provider.stream_calls[0]
    assert "/home/user/docs" in system
    assert "report.pdf" in system


def test_suggest_rename_includes_filename():
    presenter, view, _ = _make()

    presenter.suggest_rename(_item("old_name.txt"))
    _drain_after(presenter)

    all_content = " ".join(m[1] for m in view.messages)
    assert "old_name.txt" in all_content


def test_explain_file_includes_name_and_size():
    presenter, view, _ = _make()

    presenter.explain_file(_item("data.csv", size=1234))
    _drain_after(presenter)

    all_content = " ".join(m[1] for m in view.messages)
    assert "data.csv" in all_content
    assert "1234" in all_content


def test_history_accumulates():
    """Second send must include prior user+assistant exchange in messages."""
    provider = _MockProvider(tokens=("first answer",))
    view = _MockView()
    presenter = AIPresenter(view, {"mock": provider}, "mock")

    presenter.send("first question")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    presenter._pool = ThreadPoolExecutor(max_workers=2)

    presenter.send("second question")
    presenter._pool.shutdown(wait=True)
    presenter.drain()

    assert len(provider.stream_calls) == 2
    second_messages = provider.stream_calls[1][0]
    assert len(second_messages) == 3
    assert second_messages[0]["role"] == "user"
    assert second_messages[1]["role"] == "assistant"
    assert second_messages[2]["role"] == "user"


def test_set_busy_true_before_drain_false_after():
    presenter, view, _ = _make()

    presenter.send("hi")
    _drain_after(presenter)

    assert True in view.busy_states
    assert False in view.busy_states
    assert view.busy_states.index(True) < view.busy_states.index(False)


# ---------------------------------------------------------------------------
# Streaming tests
# ---------------------------------------------------------------------------

def test_streaming_tokens_delivered():
    presenter, view, _ = _make(tokens=("hello", " ", "world"))

    presenter.send("hi")
    _drain_after(presenter)

    assert view.tokens == ["hello", " ", "world"]


def test_streaming_done_finalizes():
    presenter, view, _ = _make(tokens=("x",))

    presenter.send("hi")
    _drain_after(presenter)

    assert view.finalized == 1
    assert False in view.busy_states


def test_streaming_history_saved():
    presenter, view, _ = _make(tokens=("hello", " world"))

    presenter.send("hi")
    _drain_after(presenter)

    assistant_history = [h for h in presenter._history if h["role"] == "assistant"]
    assert assistant_history
    assert assistant_history[0]["content"] == "hello world"


def test_cancel_stops_stream():
    started = threading.Event()

    class _SlowProvider(_MockProvider):
        def chat_stream(self, messages, system=""):
            self.stream_calls.append((messages, system))
            started.set()
            for i in range(200):
                time.sleep(0.002)
                yield str(i)

    provider = _SlowProvider()
    view = _MockView()
    presenter = AIPresenter(view, {"mock": provider}, "mock")
    presenter.send("hi")
    started.wait(timeout=1.0)
    presenter.cancel()
    presenter.shutdown()
    presenter.drain()
    assert len(view.tokens) < 200


# ---------------------------------------------------------------------------
# Attachment tests
# ---------------------------------------------------------------------------

def test_add_attachment_text_file(tmp_path):
    p = tmp_path / "hello.txt"
    p.write_text("hello world")
    presenter, view, _ = _make()
    presenter.add_attachment(p)
    _drain_after(presenter)
    assert len(presenter._pending_attachments) == 1
    assert presenter._pending_attachments[0].kind == "text"
    assert view.chips == ["hello.txt"]


def test_add_attachment_image(tmp_path):
    p = tmp_path / "img.png"
    p.write_bytes(b"\x89PNG")
    presenter, view, _ = _make()
    presenter.add_attachment(p)
    _drain_after(presenter)
    assert presenter._pending_attachments[0].kind == "image"


def test_add_attachment_folder(tmp_path):
    (tmp_path / "file1.txt").write_text("a")
    presenter, view, _ = _make()
    presenter.add_attachment(tmp_path)
    _drain_after(presenter)
    att = presenter._pending_attachments[0]
    assert att.kind == "folder"
    assert "file1.txt" in att.content


def test_add_attachment_truncation(tmp_path):
    p = tmp_path / "big.txt"
    p.write_bytes(b"x" * (MAX_FILE_BYTES + 1))
    presenter, view, _ = _make()
    presenter.add_attachment(p)
    _drain_after(presenter)
    assert presenter._pending_attachments[0].truncated


def test_max_attachments_limit(tmp_path):
    presenter, view, _ = _make()
    for i in range(MAX_ATTACHMENTS):
        presenter._pending_attachments.append(
            Attachment(tmp_path / f"f{i}.txt", "text", "x")
        )
    p = tmp_path / "extra.txt"
    p.write_text("extra")
    presenter.add_attachment(p)
    _drain_after(presenter)
    assert len(presenter._pending_attachments) == MAX_ATTACHMENTS


def test_send_clears_attachments(tmp_path):
    presenter, view, _ = _make()
    p = tmp_path / "f.txt"
    p.write_text("hello")
    presenter.add_attachment(p)
    presenter._pool.shutdown(wait=True)
    presenter.drain()
    assert len(presenter._pending_attachments) == 1

    presenter._pool = ThreadPoolExecutor(max_workers=2)
    presenter.send("go")
    presenter._pool.shutdown(wait=True)
    presenter.drain()
    assert len(presenter._pending_attachments) == 0
    assert view.chips_cleared >= 1


# ---------------------------------------------------------------------------
# Content blocks tests
# ---------------------------------------------------------------------------

def test_build_content_blocks_text():
    presenter, _, _ = _make()
    att = Attachment(Path("/tmp/f.txt"), "text", "hello content")
    blocks = presenter._build_content_blocks("my question", [att])
    texts = [b["text"] for b in blocks if b["type"] == "text"]
    assert any("hello content" in t for t in texts)
    assert any("my question" in t for t in texts)


def test_build_content_blocks_image():
    presenter, _, _ = _make()
    att = Attachment(Path("/tmp/img.png"), "image", b"\x89PNG")
    blocks = presenter._build_content_blocks("describe", [att])
    img_blocks = [b for b in blocks if b["type"] == "image"]
    assert len(img_blocks) == 1
    assert img_blocks[0]["source"]["media_type"] == "image/png"
    assert img_blocks[0]["source"]["data"] == base64.b64encode(b"\x89PNG").decode()


# ---------------------------------------------------------------------------
# Provider switching tests
# ---------------------------------------------------------------------------

def test_switch_provider():
    p1 = _MockProvider(tokens=("from-p1",))
    p2 = _MockProvider(tokens=("from-p2",))
    p2.name = "other"
    p2.models = ["other-model"]
    p2.active_model = "other-model"
    view = _MockView()
    presenter = AIPresenter(view, {"mock": p1, "other": p2}, "mock")
    presenter.switch_provider("other")
    assert presenter._active_key == "other"
    assert view.provider_lists


def test_switch_model():
    presenter, _, provider = _make()
    presenter.switch_model("new-model")
    assert provider._model == "new-model"


def test_noop_fallback_when_unknown_provider():
    view = _MockView()
    presenter = AIPresenter(view, {}, "none")
    presenter.send("hi")
    assert any("not configured" in m[1].lower() for m in view.messages)


def test_remove_attachment_by_index(tmp_path):
    """remove_attachment(index) removes the correct attachment from pending."""
    presenter, view, _ = _make()
    f1 = tmp_path / "a.txt"
    f2 = tmp_path / "b.txt"
    f1.write_text("aaa")
    f2.write_text("bbb")
    presenter.add_attachment(f1)
    presenter.add_attachment(f2)
    presenter._pool.shutdown(wait=True)
    presenter._pool = ThreadPoolExecutor(max_workers=2)
    presenter.drain()
    assert len(presenter._pending_attachments) == 2
    presenter.remove_attachment(0)
    assert len(presenter._pending_attachments) == 1
    assert presenter._pending_attachments[0].path == f2
