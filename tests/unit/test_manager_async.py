"""Tests for ManagerPresenter async op submission."""
from pathlib import Path
from unittest.mock import MagicMock

from biome_fm.event_bus import AsyncOpSubmitted, EventBus
from biome_fm.models.file_item import FileItem
from biome_fm.presenters.manager_presenter import ManagerPresenter


def test_sync_fallback_when_no_queue():
    """Without op_queue, copy_selected uses sync path."""
    left = MagicMock()
    right = MagicMock()
    right.current_path = Path("/dst")
    vfs = MagicMock()
    history = MagicMock()
    m = ManagerPresenter(left, right, vfs, history=history)
    m.set_active_pane("left")
    item = FileItem(name="f.txt", path=Path("/src/f.txt"), is_dir=False, size=10, modified=0.0)
    m.copy_selected([item])
    history.execute.assert_called_once()


def test_async_submit_publishes_event():
    """With op_queue, copy_selected publishes AsyncOpSubmitted."""
    bus = EventBus()
    received = []
    bus.subscribe(AsyncOpSubmitted, received.append)
    left = MagicMock()
    right = MagicMock()
    right.current_path = Path("/dst")
    vfs = MagicMock()
    op_queue = MagicMock()
    op_queue.next_task_id.return_value = 42
    m = ManagerPresenter(left, right, vfs, bus=bus, op_queue=op_queue)
    m.set_active_pane("left")
    item = FileItem(name="f.txt", path=Path("/src/f.txt"), is_dir=False, size=10, modified=0.0)
    m.copy_selected([item])
    assert len(received) == 1
    assert received[0].task_id == 42
    assert received[0].description == "Copy"


def test_pop_pending_cmd():
    m = ManagerPresenter(MagicMock(), MagicMock(), MagicMock())
    assert m.pop_pending_cmd(999) is None
