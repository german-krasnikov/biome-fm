"""Test that _start_op wires a real progress callback."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.event_bus import AsyncOpSubmitted, EventBus
from biome_fm.models.file_item import FileItem
from biome_fm.operations.task import OpProgress
from biome_fm.presenters.manager_presenter import ManagerPresenter


def _make_manager(tmp_path: Path):
    left = MagicMock()
    right = MagicMock()
    right.current_path = tmp_path / "dst"
    (tmp_path / "dst").mkdir()
    vfs = MagicMock()
    op_queue = MagicMock()
    op_queue.next_task_id.return_value = 7
    m = ManagerPresenter(left, right, vfs, op_queue=op_queue)
    m.set_active_pane("left")
    return m, op_queue


def test_progress_callback_puts_op_progress(tmp_path):
    """The report callback passed to ProgressCopyCmd must emit OpProgress."""
    m, op_queue = _make_manager(tmp_path)

    src = tmp_path / "a.txt"
    src.write_bytes(b"x")
    item = FileItem(name="a.txt", path=src, is_dir=False, size=1, modified=0.0)

    m.copy_selected([item])

    # op_queue.submit was called; extract the cmd
    assert op_queue.submit.called
    cmd = op_queue.submit.call_args[0][0]  # first positional arg

    # Simulate the callback being invoked (as ProgressCopyCmd._copy_file does)
    # The callback is cmd._report — we need to call it and see put_event fires
    # op_queue._op_queue on the manager holds a mock; the closure calls put_event on it
    cmd._report(1, 1, 100, 100, "a.txt")

    op_queue.put_event.assert_called_once()
    ev = op_queue.put_event.call_args[0][0]
    assert isinstance(ev, OpProgress)
    assert ev.task_id == 7
    assert ev.files_done == 1
    assert ev.current_file == "a.txt"
