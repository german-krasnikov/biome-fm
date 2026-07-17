"""I3: ManagerPresenter calls before_file_operation (veto) and on_file_operation hooks."""
from __future__ import annotations

from pathlib import Path

import pluggy

from biome_fm.commands.base import Command, CommandHistory
from biome_fm.event_bus import EventBus
from biome_fm.plugins.manager import PluginManager
from biome_fm.presenters.manager_presenter import ManagerPresenter, _OpSpec

hookimpl = pluggy.HookimplMarker("biome_fm")


class _FakeVFS:
    def listdir(self, path):
        return []


class _FakePane:
    current_path = Path("/tmp")

    def refresh(self) -> None:
        pass

    def navigate_to(self, path: Path) -> None:
        pass


class _TrackCmd(Command):
    undoable = False

    def __init__(self) -> None:
        self.executed = False

    def execute(self) -> None:
        self.executed = True

    def undo(self) -> None:
        pass


class _VetoPlugin:
    @hookimpl
    def before_file_operation(self, op, src, dst):
        return False


class _TrackPlugin:
    def __init__(self) -> None:
        self.calls: list[tuple] = []

    @hookimpl
    def on_file_operation(self, op, src, dst):
        self.calls.append((op, src, dst))


def _make_manager(plugins: PluginManager) -> ManagerPresenter:
    return ManagerPresenter(
        left=_FakePane(),
        right=_FakePane(),
        vfs=_FakeVFS(),
        history=CommandHistory(),
        bus=EventBus(),
        plugins=plugins,
    )


def test_before_hook_veto_blocks_run():
    """A plugin returning False from before_file_operation prevents cmd.execute()."""
    pm = PluginManager()
    pm.register_plugin(_VetoPlugin())
    m = _make_manager(pm)
    cmd = _TrackCmd()
    m._run(cmd, "test", _OpSpec("copy", Path("/a"), Path("/b")))
    assert not cmd.executed


def test_after_hook_called_on_success():
    """on_file_operation is called after successful _run()."""
    pm = PluginManager()
    tracker = _TrackPlugin()
    pm.register_plugin(tracker)
    m = _make_manager(pm)
    cmd = _TrackCmd()
    m._run(cmd, "test", _OpSpec("copy", Path("/a"), Path("/b")))
    assert cmd.executed
    assert len(tracker.calls) == 1
    assert tracker.calls[0] == ("copy", Path("/a"), Path("/b"))


def test_delete_multi_fires_all():
    """on_file_operation fires once per deleted path, not just paths[0]."""
    pm = PluginManager()
    tracker = _TrackPlugin()
    pm.register_plugin(tracker)
    m = _make_manager(pm)
    paths = [Path("/a"), Path("/b"), Path("/c")]
    m._run(_TrackCmd(), "Delete", _OpSpec("delete", paths[0], sources=paths))
    assert len(tracker.calls) == 3
    assert [c[1] for c in tracker.calls] == paths


def test_sync_copy_fires_per_source():
    """on_file_operation fires once per source for multi-source copy via _run with sources."""
    pm = PluginManager()
    tracker = _TrackPlugin()
    pm.register_plugin(tracker)
    m = _make_manager(pm)
    sources = [Path("/a"), Path("/b")]
    m._run(_TrackCmd(), "Copy", _OpSpec("copy", dst=Path("/dst"), sources=sources))
    assert len(tracker.calls) == 2
    assert [c[1] for c in tracker.calls] == sources
    assert all(c[2] == Path("/dst") for c in tracker.calls)


def test_fire_op_done_fires_hooks():
    """fire_op_done fires on_file_operation for all sources of a pending async op."""
    pm = PluginManager()
    tracker = _TrackPlugin()
    pm.register_plugin(tracker)
    m = _make_manager(pm)
    m._pending_specs[42] = _OpSpec("move", dst=Path("/dst"), sources=[Path("/x"), Path("/y")])
    m.fire_op_done(42)
    assert len(tracker.calls) == 2
    assert tracker.calls[0] == ("move", Path("/x"), Path("/dst"))
    assert tracker.calls[1] == ("move", Path("/y"), Path("/dst"))


def test_single_src_none_still_fires():
    """mkdir/_run with src=None, no sources still fires on_file_operation(src=None)."""
    pm = PluginManager()
    tracker = _TrackPlugin()
    pm.register_plugin(tracker)
    m = _make_manager(pm)
    m._run(_TrackCmd(), "mkdir", _OpSpec("mkdir", dst=Path("/newdir")))
    assert len(tracker.calls) == 1
    assert tracker.calls[0] == ("mkdir", None, Path("/newdir"))


def test_fire_op_done_clears_spec():
    """fire_op_done removes the spec so a second call is a no-op."""
    pm = PluginManager()
    tracker = _TrackPlugin()
    pm.register_plugin(tracker)
    m = _make_manager(pm)
    m._pending_specs[7] = _OpSpec("copy", dst=Path("/d"), sources=[Path("/s")])
    m.fire_op_done(7)
    m.fire_op_done(7)  # second call — no spec, should not raise or double-fire
    assert len(tracker.calls) == 1
