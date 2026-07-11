"""Unit tests for CommandRegistry — pure Python, no Qt."""
from biome_fm.commands.registry import CommandEntry, CommandRegistry


def _reg(*names: str) -> CommandRegistry:
    r = CommandRegistry()
    for n in names:
        r.register(CommandEntry(n, "", lambda: None))
    return r


def test_empty_query_returns_all():
    r = _reg("Copy", "Move", "Delete")
    assert len(r.search("")) == 3


def test_filters_by_substring():
    r = _reg("Copy Files", "Move Files", "Delete")
    result = r.search("files")
    assert len(result) == 2
    assert all("Files" in e.name for e in result)


def test_case_insensitive():
    r = _reg("Copy")
    assert r.search("COPY") == r.search("copy")
    assert len(r.search("copy")) == 1


def test_no_match_returns_empty():
    r = _reg("Copy", "Move")
    assert r.search("zzz") == []


def test_register_preserves_order():
    r = _reg("Undo", "Redo", "Copy")
    names = [e.name for e in r.search("")]
    assert names == ["Undo", "Redo", "Copy"]


def test_callback_is_stored():
    called = []
    r = CommandRegistry()
    r.register(CommandEntry("Test", "Ctrl+T", lambda: called.append(1)))
    r.search("Test")[0].callback()
    assert called == [1]
