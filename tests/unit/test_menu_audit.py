"""Menu and settings audit — TDD for Issue 8."""
from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def _menu_action_texts(menu) -> list[str]:
    """Return stripped text of all actions in a QMenu (drops accelerator tabs)."""
    return [a.text().split("\t")[0].replace("&", "") for a in menu.actions()]


def _find_top_menu(window, title: str):
    """Return (action, QMenu) from menubar by title (no ampersand), keeping the action alive."""
    for action in window.menuBar().actions():
        if action.text().replace("&", "") == title:
            return action, action.menu()
    return None, None


def test_file_menu_has_duplicate_tab(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, fm = _find_top_menu(w, "File")
    assert fm is not None
    assert "Duplicate Tab" in _menu_action_texts(fm)


def test_file_menu_has_save_session(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, fm = _find_top_menu(w, "File")
    assert "Save Session" in _menu_action_texts(fm)


def test_file_menu_has_restore_session(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, fm = _find_top_menu(w, "File")
    assert "Restore Session" in _menu_action_texts(fm)


def test_edit_menu_has_select_pattern(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, em = _find_top_menu(w, "Edit")
    assert em is not None
    assert "Select by Pattern" in _menu_action_texts(em)


def test_edit_menu_has_select_criteria(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, em = _find_top_menu(w, "Edit")
    assert "Select by Criteria" in _menu_action_texts(em)


def test_edit_menu_has_copy_path(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, em = _find_top_menu(w, "Edit")
    assert "Copy Path" in _menu_action_texts(em)


def test_edit_menu_has_copy_names(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, em = _find_top_menu(w, "Edit")
    assert "Copy File Names" in _menu_action_texts(em)


def test_edit_menu_has_bulk_rename(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, em = _find_top_menu(w, "Edit")
    assert "Bulk Rename Editor" in _menu_action_texts(em)


def test_navigate_menu_has_quick_cd(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, nm = _find_top_menu(w, "Navigate")
    assert nm is not None
    assert "Quick CD" in _menu_action_texts(nm)


def test_navigate_menu_has_jump(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, nm = _find_top_menu(w, "Navigate")
    assert "Jump to Frecent" in _menu_action_texts(nm)


def test_navigate_menu_has_bookmarks(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, nm = _find_top_menu(w, "Navigate")
    assert "Bookmarks..." in _menu_action_texts(nm)


def test_navigate_menu_has_swap_panes(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, nm = _find_top_menu(w, "Navigate")
    assert "Swap Panes" in _menu_action_texts(nm)


def test_view_menu_has_zoom(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, vm = _find_top_menu(w, "View")
    assert vm is not None
    assert "Zoom In" in _menu_action_texts(vm)


def test_view_menu_has_fullscreen(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, vm = _find_top_menu(w, "View")
    assert "Fullscreen" in _menu_action_texts(vm)


def test_tools_menu_has_treemap(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, tm = _find_top_menu(w, "Tools")
    assert tm is not None
    assert "Storage Treemap" in _menu_action_texts(tm)


def test_tools_menu_has_large_files(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, tm = _find_top_menu(w, "Tools")
    assert "Large File Finder" in _menu_action_texts(tm)


def test_tools_menu_has_task_runner(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, tm = _find_top_menu(w, "Tools")
    assert "Task Runner" in _menu_action_texts(tm)


def test_tools_menu_has_permissions(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, tm = _find_top_menu(w, "Tools")
    assert "Permissions Editor" in _menu_action_texts(tm)


def test_help_menu_exists(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, hm = _find_top_menu(w, "Help")
    assert hm is not None
    assert "Keyboard Shortcuts" in _menu_action_texts(hm)


def test_help_menu_has_about(qtbot):
    from biome_fm.views.main_window import MainWindow
    w = MainWindow()
    qtbot.addWidget(w)
    _, hm = _find_top_menu(w, "Help")
    assert "About" in _menu_action_texts(hm)


def test_settings_has_editor_cmd(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    assert hasattr(d, "_editor_cmd")
    d.set_editor_cmd("vim")
    assert d.get_editor_cmd() == "vim"


def test_settings_has_global_hotkey(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    assert hasattr(d, "_global_hotkey")
    d.set_global_hotkey("<ctrl>+<alt>+b")
    assert d.get_global_hotkey() == "<ctrl>+<alt>+b"


def test_settings_has_follow_system_theme(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    assert hasattr(d, "_follow_system_theme_cb")
    d.set_follow_system_theme(True)
    assert d.get_follow_system_theme() is True


def test_settings_has_serial_ops(qtbot):
    from biome_fm.views.settings_dialog import SettingsDialog
    d = SettingsDialog()
    qtbot.addWidget(d)
    assert hasattr(d, "_serial_ops_cb")
    d.set_serial_ops(True)
    assert d.get_serial_ops() is True


def test_mainwindow_has_all_new_signals():
    from biome_fm.views.main_window import MainWindow
    for sig in [
        "dup_tab_requested", "save_session_requested", "restore_session_requested",
        "select_pattern_requested", "select_criteria_requested",
        "copy_path_requested", "copy_names_requested", "bulk_rename_requested",
        "quick_cd_requested", "jump_requested", "bookmarks_requested",
        "bookmark_toggle_requested", "swap_requested", "target_eq_source_requested",
        "zoom_in_requested", "zoom_out_requested", "zoom_reset_requested",
        "fullscreen_requested", "treemap_requested", "large_files_requested",
        "task_runner_requested", "permissions_requested",
        "shortcuts_help_requested", "about_requested",
    ]:
        assert hasattr(MainWindow, sig), f"Missing signal: {sig}"
