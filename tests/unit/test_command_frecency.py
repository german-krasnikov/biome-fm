"""Unit tests for frecency ranking in CommandRegistry."""
from biome_fm.commands.registry import CommandEntry, CommandRegistry


def _entry(name: str) -> CommandEntry:
    return CommandEntry(name=name, shortcut="", callback=lambda: None)


def test_search_empty_query_sorted_by_hits() -> None:
    reg = CommandRegistry()
    reg.register(_entry("Alpha"))
    reg.register(_entry("Beta"))
    reg.record_hit("Beta")
    result = reg.search("")
    assert result[0].name == "Beta"


def test_search_with_query_sorted_by_hits() -> None:
    reg = CommandRegistry()
    reg.register(_entry("Copy Files"))
    reg.register(_entry("Copy Link"))
    for _ in range(3):
        reg.record_hit("Copy Link")
    result = reg.search("copy")
    assert result[0].name == "Copy Link"


def test_record_hit_increments() -> None:
    reg = CommandRegistry()
    reg.register(_entry("Open"))
    reg.record_hit("Open")
    reg.record_hit("Open")
    assert reg._hits["Open"] == 2


def test_no_hits_preserves_order() -> None:
    reg = CommandRegistry()
    reg.register(_entry("Zebra"))
    reg.register(_entry("Apple"))
    result = reg.search("")
    assert [e.name for e in result] == ["Zebra", "Apple"]
