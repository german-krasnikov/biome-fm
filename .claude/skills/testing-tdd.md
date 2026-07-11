---
name: testing-tdd
description: "TDD workflow — Red-Green-Refactor, pytest + pytest-qt patterns, MVP testing."
user-invocable: false
globs:
  - "tests/**/*.py"
  - "src/**/*.py"
---

# TDD: pytest + pytest-qt

## Red-Green-Refactor

```
1. RED: Write failing test first → Run → MUST FAIL
2. GREEN: Minimal code to pass → Run → MUST PASS
3. REFACTOR: Clean up → Run ALL tests → MUST STAY GREEN
```

## Unit Tests (80% — no Qt dependency)

```python
# Test Presenter without Qt
def test_pane_presenter_navigates_to_directory(tmp_path):
    view = MockPaneView()
    vfs = LocalVFS()
    presenter = PanePresenter(view, vfs)
    presenter.navigate(tmp_path)
    assert view.displayed_path == tmp_path

# Test Command with undo
def test_rename_command_undo(tmp_path):
    src = tmp_path / "old.txt"
    src.write_text("data")
    cmd = RenameCommand(src, tmp_path / "new.txt")
    cmd.execute()
    assert (tmp_path / "new.txt").exists()
    cmd.undo()
    assert src.exists()
```

## Integration Tests (pytest-qt)

```python
# conftest.py
import pytest
from PySide6.QtWidgets import QApplication

@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance() or QApplication([])
    yield app

# Test with qtbot
def test_f5_triggers_copy(qtbot, qapp):
    window = MainWindow()
    qtbot.addWidget(window)
    qtbot.keyPress(window, Qt.Key.Key_F5)
    qtbot.waitSignal(window.copy_requested, timeout=1000)

# Test model
def test_directory_model_lists_files(qtbot, tmp_path):
    (tmp_path / "a.txt").touch()
    (tmp_path / "b.txt").touch()
    model = DirectoryModel()
    model.set_directory(tmp_path)
    assert model.rowCount() == 2
```

## Property-Based Tests (Hypothesis)

```python
from hypothesis import given, strategies as st

@given(st.text(min_size=1, alphabet=st.characters(blacklist_categories=('Cs',))))
def test_sanitize_filename_never_contains_illegal_chars(name):
    result = sanitize_filename(name)
    assert all(c not in result for c in '<>:"/\\|?*')
    assert len(result) <= 255
```

## Mocking Filesystem (pyfakefs)

```python
def test_copy_command_with_fake_fs(fs):
    fs.create_file("/src/file.txt", contents="hello")
    cmd = CopyCommand(Path("/src/file.txt"), Path("/dst/file.txt"))
    cmd.execute()
    assert Path("/dst/file.txt").read_text() == "hello"
```

## Test Commands

```bash
uv run pytest tests/unit/ -q                    # fastest, no Qt
uv run pytest tests/integration/ -q              # Qt offscreen
uv run pytest tests/ -x -v -k "test_specific"   # one test
uv run pytest tests/ --cov=src/biome_fm          # coverage
```

## Anti-Patterns

- Testing view logic instead of presenter logic
- Skipping undo tests for Commands
- Using real filesystem when pyfakefs suffices
- Running full suite to check one fix
- Hardcoded paths in tests (use tmp_path)
