# Plan: Issues 5-12 — Master Implementation Plan

**Branch:** `feature/issues-5-12-fixes`  
**Created:** 2026-07-24  
**Status:** Complete — awaiting code review  

## Execution Order (by risk/dependency)

| # | Issue | Complexity | Files | Status |
|---|-------|-----------|-------|--------|
| 1 | **10: Fix KeyError 'info'** | Trivial | panel_manager.py, panel_coordinator.py | ✅ Done |
| 2 | **6: Remove Alt+F4 button** | Trivial | action_bar.py, app.py | ✅ Done |
| 3 | **5: F4 EditorDialog + Shift+F4 external** | Small | app.py | ✅ Done |
| 4 | **11: F10 AI button** | Small | action_bar.py, app.py | ✅ Done |
| 5 | **7: Workspaces → menu** | Small | main_window.py | ✅ Done |
| 6 | **9: Highlight presets** | Medium | highlight_rules.py, highlight_rules_dialog.py, app.py | ✅ Done |
| 7 | **8: Menu/settings audit** | Large | main_window.py, settings_dialog.py, settings_presenter.py, app.py | ✅ Done |
| 8 | **12: AI model dropdown** | None | Already implemented | ✅ Done |

## Issue 10: Fix KeyError 'info'

**Root cause:** `PanelManager.PANELS = ('preview','ai','search','terminal')` — missing `'info'`. But `PanelCoordinator` is constructed with 5 panels including `'info'`.

**Fix:**
- `panel_manager.py:22` — add `'info'` to `PANELS` tuple
- `panel_coordinator.py:175` — add `'info': 6` to `_overlay_index()` base dict + adjustment conditions

**Tests:** state('info') no KeyError, toggle('info') works, save_state includes info

## Issue 6: Remove Alt+F4 button

**Fix:**
- `action_bar.py:17` — delete `exit_requested = Signal()`
- `action_bar.py:27` — delete `('Alt+F4 Exit', 'exit_requested', ...)`
- `app.py:1752` — delete `bar.exit_requested.connect(window.close)`

## Issue 5: F4 EditorDialog, Shift+F4 external

**Current:** F4 calls `open_in_editor()` (external). `bar.edit_requested` signal never connected.

**Fix:**
- `app.py _open_in_editor_f4()` — change to open EditorDialog
- Add Shift+F4 shortcut for external editor
- Connect `bar.edit_requested` signal

## Issue 11: F10 AI button

**Fix:**
- `action_bar.py` — add `ai_requested = Signal()`, add `('F10 AI', 'ai_requested', ...)` to `_BUTTONS`
- `app.py` — wire `bar.ai_requested` + F10 shortcut to `coord.toggle('ai', ...)`

## Issue 7: Workspaces → app menu

**Fix:**
- `main_window.py _setup_ui()` — remove `_ws_btn` QToolButton
- `main_window.py _build_menubar()` — replace Workspaces QAction with submenu `vm.addMenu('&Workspaces')`, assign to `self.workspace_menu`
- App.py untouched (attribute name preserved)

## Issue 9: File highlight presets

**Presets:**
- Default: no rules (empty)
- Dark: light tones (green archives, blue executables, pink media, purple docs, yellow code, orange config)
- Light: dark tones (inverted)

**Changes:**
- `highlight_rules.py` — add `HIGHLIGHT_PRESETS` dict + `expand_rules()` helper
- `highlight_rules_dialog.py` — add preset QComboBox above table
- `app.py _apply_highlight_rules()` — use `expand_rules()`
- `settings_dialog.py` — add highlight preset combo to Appearance tab

## Issue 8: Menu/settings audit

**Missing menu entries (31):**
- Edit: Select by Pattern, Select by Criteria, Copy Path, Bulk Rename in Editor
- Navigate: Quick CD, Jump to Frecent, Bookmarks, Swap Panes
- View: Zoom In/Out/Reset, Fullscreen
- File: Duplicate Tab, Save Session, Restore Session
- Tools: Storage Treemap, Large Files, Task Runner, Permissions
- Help (NEW): Keyboard Shortcuts, About

**Missing settings (6):**
- editor_cmd, global_hotkey, follow_system_theme, serial_ops, toolbar_visible, toolbar_actions

## Issue 12: AI model dropdown — ALREADY DONE

Architect confirmed: `AIChatPanel` has `_provider_combo` + `_model_combo`, wired in `app.py:609+616`. All 3 CLI backends registered in `backend_def.py`.
