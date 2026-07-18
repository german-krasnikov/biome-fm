"""F227 — Smart Folders (search bookmarks) tests."""
from __future__ import annotations

from pathlib import Path

from biome_fm.models.bookmark_node import BookmarkNode, parse_search_uri


def test_search_bookmark_roundtrip() -> None:
    node = BookmarkNode(
        kind="search",
        path=Path("search://name=*.py&content=TODO"),
        name="Find TODOs",
    )
    assert node.kind == "search"
    params = parse_search_uri(str(node.path))
    assert params["name"] == "*.py"
    assert params["content"] == "TODO"


def test_search_uri_parsing() -> None:
    uri = "search://name=*.txt&content=FIXME"
    params = parse_search_uri(uri)
    assert params["name"] == "*.txt"
    assert params["content"] == "FIXME"
