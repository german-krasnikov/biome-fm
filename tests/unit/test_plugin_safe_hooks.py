"""Unit tests — safe hook delegates in PluginManager.

Each test registers a crash plugin, calls the safe delegate,
and verifies the safe default is returned without raising.
"""
from __future__ import annotations

import logging
from pathlib import Path


from biome_fm.plugins.manager import PluginManager
from biome_fm.plugins.hookspecs import hookimpl


class _CrashPlugin:
    @hookimpl
    def before_file_operation(self, op, src, dst):
        raise RuntimeError("boom")

    @hookimpl
    def context_menu_actions(self, items, pane_id):
        raise RuntimeError("boom")

    @hookimpl
    def extra_columns(self):
        raise RuntimeError("boom")

    @hookimpl
    def extra_archive_extensions(self):
        raise RuntimeError("boom")

    @hookimpl
    def provide_vfs(self, path):
        raise RuntimeError("boom")

    @hookimpl
    def provide_theme(self, name):
        raise RuntimeError("boom")

    @hookimpl
    def column_value(self, item, column_id):
        raise RuntimeError("boom")

    @hookimpl
    def register_commands(self, registry):
        raise RuntimeError("boom")


def _pm() -> PluginManager:
    pm = PluginManager()
    pm.register_plugin(_CrashPlugin())
    return pm


def test_crashing_before_file_op_allows():
    result = _pm().before_file_operation("copy", Path("/a"), Path("/b"))
    assert result is None  # None = allow, not False = veto


def test_crashing_context_menu_returns_empty():
    assert _pm().context_menu_actions([], "left") == []


def test_crashing_extra_columns_returns_empty():
    assert _pm().extra_columns() == []


def test_crashing_extra_archive_exts_returns_empty():
    assert _pm().extra_archive_extensions() == []


def test_crashing_provide_vfs_returns_none():
    assert _pm().provide_vfs("/some/path") is None


def test_crashing_provide_theme_returns_none():
    assert _pm().provide_theme("dark") is None


def test_crashing_column_value_returns_none():
    assert _pm().column_value(object(), "git.status") is None


def test_crashing_register_commands_does_not_raise():
    _pm().call_register_commands(registry=object())  # must not raise


def test_crash_is_logged(caplog):
    pm = _pm()
    with caplog.at_level(logging.ERROR):
        pm.before_file_operation("copy", Path("/a"), None)
    assert "before_file_operation" in caplog.text
