"""F9 shortcut label regression tests — no Qt needed."""
import pathlib

from biome_fm.views.shortcut_help_dialog import SHORTCUTS


def _all_entries():
    return {k: v for section in SHORTCUTS.values() for k, v in section.items()}


def test_f9_is_rename():
    assert _all_entries()["F9"] == "Rename"


def test_f9_not_terminal():
    assert "terminal" not in _all_entries()["F9"].lower()


def test_open_terminal_label_has_no_f9():
    src = (pathlib.Path(__file__).parents[2] / "src/biome_fm/views/pane_view.py").read_text()
    assert "Open Terminal Here\tF9" not in src


def test_app_no_f9_open_terminal_shortcut():
    src = (pathlib.Path(__file__).parents[2] / "src/biome_fm/app.py").read_text()
    # F9 shortcut must not point to open_terminal
    lines = src.splitlines()
    for i, line in enumerate(lines):
        if 'QShortcut(QKeySequence("F9")' in line:
            context = "\n".join(lines[max(0, i - 1): i + 3])
            assert "open_terminal" not in context, f"F9 still wired to open_terminal:\n{context}"
