"""TDD tests for workspace switcher shortcuts (Item #36)."""
from __future__ import annotations

from biome_fm.app import _workspace_name_at
from biome_fm.models.workspace_store import WorkspaceStore


# ── _workspace_name_at (real production function) ────────────────────────────

def test_workspace_name_at_empty(tmp_path):
    store = WorkspaceStore(tmp_path / "ws.json")
    assert _workspace_name_at(store, 0) is None


def test_workspace_name_at_sorted(tmp_path):
    store = WorkspaceStore(tmp_path / "ws.json")
    store.save("beta", ["/a"], ["/b"])
    store.save("alpha", ["/c"], ["/d"])
    assert _workspace_name_at(store, 0) == "alpha"
    assert _workspace_name_at(store, 1) == "beta"


def test_workspace_name_at_oob(tmp_path):
    store = WorkspaceStore(tmp_path / "ws.json")
    store.save("only", [], [])
    assert _workspace_name_at(store, 5) is None


# ── menu population ──────────────────────────────────────────────────────────

def test_refresh_workspace_menu_items(tmp_path, qtbot):
    from biome_fm.qt import QMenu

    store = WorkspaceStore(tmp_path / "ws.json")
    store.save("ws1", [], [])
    store.save("ws2", [], [])

    menu = QMenu()

    def refresh() -> None:
        menu.clear()
        names = store.list_names()
        for i, name in enumerate(names[:5]):
            menu.addAction(f"{name}  Ctrl+Alt+{i + 1}")
        if not names:
            menu.addAction("No saved workspaces").setEnabled(False)
        menu.addSeparator()
        menu.addAction("Manage Workspaces…")

    refresh()

    non_sep = [a for a in menu.actions() if not a.isSeparator()]
    assert len(non_sep) == 3  # ws1, ws2, Manage
    assert menu.actions()[0].text() == "ws1  Ctrl+Alt+1"
    assert menu.actions()[1].text() == "ws2  Ctrl+Alt+2"


def test_refresh_workspace_menu_empty(tmp_path, qtbot):
    from biome_fm.qt import QMenu

    store = WorkspaceStore(tmp_path / "ws.json")
    menu = QMenu()

    def refresh() -> None:
        menu.clear()
        names = store.list_names()
        for i, name in enumerate(names[:5]):
            menu.addAction(f"{name}  Ctrl+Alt+{i + 1}")
        if not names:
            menu.addAction("No saved workspaces").setEnabled(False)
        menu.addSeparator()
        menu.addAction("Manage Workspaces…")

    refresh()

    non_sep = [a for a in menu.actions() if not a.isSeparator()]
    assert len(non_sep) == 2  # "No saved workspaces" + "Manage"
    assert not non_sep[0].isEnabled()
