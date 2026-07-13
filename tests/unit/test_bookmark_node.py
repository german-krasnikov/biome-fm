"""Unit tests for BookmarkNode dataclass and display_label(). No Qt."""
from __future__ import annotations

from pathlib import Path

import pytest

from biome_fm.models.bookmark_node import BookmarkNode, display_label


class TestBookmarkNode:
    def test_dir_with_custom_name(self):
        n = BookmarkNode(kind="dir", path=Path("/home/user"), name="Home")
        assert display_label(n) == "Home"

    def test_dir_without_name_uses_path_name(self):
        n = BookmarkNode(kind="dir", path=Path("/home/user/Documents"))
        assert display_label(n) == "Documents"

    def test_dir_root_path_fallback(self):
        n = BookmarkNode(kind="dir", path=Path("/"))
        assert display_label(n) == "/"

    def test_dir_empty_name_uses_path_name(self):
        n = BookmarkNode(kind="dir", path=Path("/tmp/work"), name="")
        assert display_label(n) == "work"

    def test_submenu_returns_name(self):
        n = BookmarkNode(kind="submenu", name="Projects")
        assert display_label(n) == "Projects"

    def test_separator_returns_dashes(self):
        n = BookmarkNode(kind="separator")
        assert display_label(n) == "──────────"

    def test_dataclass_equality(self):
        a = BookmarkNode(kind="dir", path=Path("/a"), name="A")
        b = BookmarkNode(kind="dir", path=Path("/a"), name="A")
        assert a == b

    def test_submenu_children_default_empty(self):
        n = BookmarkNode(kind="submenu", name="Grp")
        assert n.children == []

    def test_children_not_shared_between_instances(self):
        a = BookmarkNode(kind="submenu", name="A")
        b = BookmarkNode(kind="submenu", name="B")
        a.children.append(BookmarkNode(kind="separator"))
        assert b.children == []
