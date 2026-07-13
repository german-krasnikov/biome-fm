"""TDD: ManagerPresenter confirm guard — no Qt."""
from pathlib import Path
from unittest.mock import MagicMock, call

import pytest

from biome_fm.presenters.manager_presenter import ConfirmSpec, ManagerPresenter


# ── helpers ──────────────────────────────────────────────────────────────────

def _make(tmp_path: Path, confirm=None):
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "right"
    right.current_path.mkdir(exist_ok=True)
    left.current_path = tmp_path / "left"
    left.current_path.mkdir(exist_ok=True)
    vfs = MagicMock()
    history = MagicMock()
    kw = {"confirm": confirm} if confirm is not None else {}
    m = ManagerPresenter(left, right, vfs, history=history, **kw)
    return m, left, right, vfs, history


def _files(tmp_path: Path, n: int = 1):
    paths = []
    for i in range(n):
        p = tmp_path / f"file{i}.txt"
        p.write_text("x")
        paths.append(p)
    return paths


def _items(paths):
    items = []
    for p in paths:
        fi = MagicMock()
        fi.path = p
        items.append(fi)
    return items


# ── confirm called correctly ──────────────────────────────────────────────────

def test_copy_confirm_called(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    srcs = _files(tmp_path)
    m.copy_selected(_items(srcs))
    confirm.assert_called_once()
    spec: ConfirmSpec = confirm.call_args[0][0]
    assert spec.op == "copy"
    assert spec.sources == srcs
    assert spec.dest == right.current_path


def test_move_confirm_called(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    srcs = _files(tmp_path)
    m.move_selected(_items(srcs))
    spec: ConfirmSpec = confirm.call_args[0][0]
    assert spec.op == "move"
    assert spec.sources == srcs
    assert spec.dest == right.current_path


def test_delete_confirm_called(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    srcs = _files(tmp_path)
    m.delete_selected(_items(srcs))
    spec: ConfirmSpec = confirm.call_args[0][0]
    assert spec.op == "delete"
    assert spec.sources == srcs
    assert spec.dest is None


def test_drop_copy_confirm_called(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    src = tmp_path / "f.txt"
    src.write_text("x")
    m.drop_files([src], "right", move=False)
    spec: ConfirmSpec = confirm.call_args[0][0]
    assert spec.op == "copy"


def test_drop_move_confirm_called(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    src = tmp_path / "f.txt"
    src.write_text("x")
    m.drop_files([src], "right", move=True)
    spec: ConfirmSpec = confirm.call_args[0][0]
    assert spec.op == "move"


# ── cancel blocks operation ───────────────────────────────────────────────────

def test_copy_blocked_on_cancel(tmp_path):
    confirm = MagicMock(return_value=False)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    m.copy_selected(_items(_files(tmp_path)))
    history.execute.assert_not_called()


def test_move_blocked_on_cancel(tmp_path):
    confirm = MagicMock(return_value=False)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    m.move_selected(_items(_files(tmp_path)))
    history.execute.assert_not_called()


def test_delete_blocked_on_cancel(tmp_path):
    confirm = MagicMock(return_value=False)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    m.delete_selected(_items(_files(tmp_path)))
    history.execute.assert_not_called()


def test_drop_blocked_on_cancel(tmp_path):
    confirm = MagicMock(return_value=False)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    src = tmp_path / "f.txt"
    src.write_text("x")
    m.drop_files([src], "right", move=False)
    history.execute.assert_not_called()


# ── edge cases ────────────────────────────────────────────────────────────────

def test_empty_selection_no_confirm(tmp_path):
    confirm = MagicMock(return_value=True)
    m, *_ = _make(tmp_path, confirm)
    m.copy_selected([])
    confirm.assert_not_called()


def test_delete_empty_no_confirm(tmp_path):
    confirm = MagicMock(return_value=True)
    m, *_ = _make(tmp_path, confirm)
    m.delete_selected([])
    confirm.assert_not_called()


def test_undo_no_confirm(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    m.undo()
    confirm.assert_not_called()


def test_redo_no_confirm(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    m.redo()
    confirm.assert_not_called()


def test_default_confirm_allows_op(tmp_path):
    """No confirm kwarg — operation proceeds."""
    m, left, right, vfs, history = _make(tmp_path)
    m.copy_selected(_items(_files(tmp_path)))
    history.execute.assert_called_once()


def test_confirm_receives_all_paths(tmp_path):
    confirm = MagicMock(return_value=True)
    m, left, right, vfs, history = _make(tmp_path, confirm)
    srcs = _files(tmp_path, n=3)
    m.copy_selected(_items(srcs))
    spec: ConfirmSpec = confirm.call_args[0][0]
    assert len(spec.sources) == 3


# ── pure helpers ──────────────────────────────────────────────────────────────

from biome_fm.views.confirm_dialog import _heading, _format_paths  # noqa: E402


def test_body_single_delete():
    h = _heading("delete", 1)
    assert "Delete" in h
    assert "1" in h


def test_body_multi_copy():
    h = _heading("copy", 5)
    assert "Copy" in h
    assert "5" in h
    paths = [Path(f"/a/f{i}.txt") for i in range(7)]
    lines = _format_paths(paths, max_shown=5)
    assert len(lines) == 6  # 5 shown + 1 overflow
    assert "2 more" in lines[-1]
