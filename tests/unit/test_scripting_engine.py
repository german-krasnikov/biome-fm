"""TDD: ScriptingEngine + BiomeContext — pure Python, no Qt."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from biome_fm.scripting.context import BiomeContext
from biome_fm.scripting.engine import ScriptError, ScriptingEngine


@pytest.fixture
def pane():
    m = MagicMock()
    m.current_path = Path("/home/user")
    return m


@pytest.fixture
def registry():
    return MagicMock()


@pytest.fixture
def ctx(pane, registry):
    return BiomeContext(pane, registry)


@pytest.fixture
def engine(ctx):
    return ScriptingEngine(ctx)


def test_navigate_calls_pane(engine, pane):
    engine.exec_code("biome.navigate('/tmp')")
    pane.navigate.assert_called_once_with(Path("/tmp"))


def test_syntax_error_raises_script_error(engine):
    with pytest.raises(ScriptError, match="Syntax error"):
        engine.exec_code("x = 1 +")


def test_runtime_error_raises_script_error(engine):
    with pytest.raises(ScriptError, match="test"):
        engine.exec_code("raise ValueError('test')")


def test_current_path_accessible(engine):
    engine.exec_code("result = biome.current_path")  # must not raise


def test_selected_returns_paths(ctx, pane):
    item1, item2 = MagicMock(), MagicMock()
    item1.path = Path("/a/b")
    item2.path = Path("/a/c")
    pane.marked_items.return_value = [item1, item2]
    assert ctx.selected == [Path("/a/b"), Path("/a/c")]


def test_execute_calls_registry(engine, registry):
    engine.exec_code("biome.execute('copy')")
    registry.execute.assert_called_once_with("copy")
