"""Tests for AIPresenter.summarize_file — pure Python, no Qt."""
from __future__ import annotations

import time
from pathlib import Path


from biome_fm.models.file_item import FileItem
from biome_fm.presenters.ai_presenter import AIPresenter


class _Provider:
    available = True
    models = ["m"]
    active_model = "m"

    def __init__(self):
        self.calls = 0

    def chat_stream(self, messages, system=""):
        self.calls += 1
        yield "Summary text"

    def set_model(self, m):
        pass


class _View:
    def __init__(self):
        self.messages: list[tuple[str, str]] = []
        self.busy: list[bool] = []
        self.tokens: list[str] = []
        self.finalized = 0
        self.last_user_message: str | None = None

    def append_message(self, role, content):
        self.messages.append((role, content))
        if role == "user":
            self.last_user_message = content

    def set_busy(self, b):
        self.busy.append(b)

    def append_token(self, t):
        self.tokens.append(t)

    def finalize_stream(self):
        self.finalized += 1

    def discard_stream(self):
        pass

    def clear_attachment_chips(self):
        pass

    def add_attachment_chip(self, name):
        pass

    def set_provider_list(self, *a):
        pass

    def append_tool_event(self, desc):
        pass


def _make_item(path: Path) -> FileItem:
    s = path.stat()
    return FileItem(name=path.name, path=path, is_dir=False,
                    size=s.st_size, modified=s.st_mtime)


def _make(provider=None):
    p = provider or _Provider()
    view = _View()
    presenter = AIPresenter(view, {"mock": p}, "mock")
    return presenter, view, p


def _drain_until_idle(p: AIPresenter, timeout: float = 5.0) -> None:
    """Two-stage drain for async summarize: wait for build, then wait for stream."""
    # Stage 1: wait for _build_summarize_prompt to enqueue summarize_ready
    deadline = time.monotonic() + timeout
    while p._events.empty() and time.monotonic() < deadline:
        time.sleep(0.005)
    p.drain()  # processes summarize_ready → calls send() → starts _run_stream
    # Stage 2: poll until stream completes (done/error puts _draining=False via _notify_idle)
    deadline2 = time.monotonic() + timeout
    while p._draining and time.monotonic() < deadline2:
        p.drain()
        time.sleep(0.005)


# ── new tests (RED before implementation) ────────────────────────────────────

def test_summarize_file_sends_content(tmp_path: Path):
    """File content must be included in the prompt sent to the AI."""
    f = tmp_path / "notes.txt"
    f.write_text("Hello world from notes")
    item = _make_item(f)
    presenter, view, _ = _make()
    presenter.summarize_file(item)
    _drain_until_idle(presenter)
    assert view.last_user_message is not None
    assert "Hello world from notes" in view.last_user_message


def test_summarize_file_cache_hit(tmp_path: Path):
    """Cache hit skips file read and stream; appends cached text immediately."""
    f = tmp_path / "doc.md"
    f.write_text("x")
    item = _make_item(f)
    presenter, view, provider = _make()
    key = (item.path, item.modified)
    presenter._summary_cache[key] = "Cached summary"
    presenter.summarize_file(item)
    assert view.messages[-1] == ("assistant", "Cached summary")
    assert provider.calls == 0  # no async dispatch


def test_pending_summary_key_set_after_send(tmp_path: Path):
    """_pending_summary_key must be set AFTER send() so 'done' populates cache."""
    f = tmp_path / "a.py"
    f.write_text("code")
    item = _make_item(f)
    presenter, view, _ = _make()
    presenter.summarize_file(item)
    _drain_until_idle(presenter)
    # Simulate a 'done' arriving AFTER drain (shouldn't happen in practice but guards the ordering)
    key = (item.path, item.modified)
    assert key in presenter._summary_cache, "cache must be populated after full drain"


def test_summarize_file_read_error(tmp_path: Path):
    """OSError during file read must produce graceful fallback, not crash."""
    p = tmp_path / "ghost.bin"  # does not exist
    item = FileItem(name="ghost.bin", path=p, is_dir=False, size=0, modified=0.0)
    presenter, view, _ = _make()
    presenter.summarize_file(item)
    _drain_until_idle(presenter)
    assert view.last_user_message is not None
    assert "ghost.bin" in view.last_user_message


# ── existing tests — updated to two-stage drain ──────────────────────────────

def test_summarize_sends_prompt(tmp_path: Path):
    f = tmp_path / "file.txt"
    f.write_text("content")
    item = _make_item(f)
    presenter, view, provider = _make()
    presenter.summarize_file(item)
    _drain_until_idle(presenter)
    assert any("ummariz" in m[1] for m in view.messages)
    assert provider.calls == 1


def test_summarize_uses_cache(tmp_path: Path):
    f = tmp_path / "file.txt"
    f.write_text("content")
    item = _make_item(f)
    presenter, view, provider = _make()
    presenter.summarize_file(item)
    _drain_until_idle(presenter)
    first_calls = provider.calls

    # second call — same (path, mtime) must hit cache
    presenter.summarize_file(item)
    assert provider.calls == first_calls  # no extra AI call


def test_summarize_no_provider_no_crash(tmp_path: Path):
    f = tmp_path / "file.txt"
    f.write_text("x")
    item = _make_item(f)
    view = _View()
    presenter = AIPresenter(view, {}, "none")
    # must not raise
    presenter.summarize_file(item)
    # allow background thread to finish without hanging
    presenter._pool.shutdown(wait=True)
