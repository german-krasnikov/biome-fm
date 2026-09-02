"""Unit tests for Sprint 1 critical stability fixes."""
from __future__ import annotations

import sqlite3
import stat
import tempfile
from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Fix #1 — SFTPVfs.listdir: modified must be float
# ---------------------------------------------------------------------------

def _make_sftp_vfs():
    from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs
    return SFTPVfs(SFTPSession(host="localhost"))


def test_sftp_listdir_modified_is_float():
    vfs = _make_sftp_vfs()
    attr = MagicMock()
    attr.filename = "file.txt"
    attr.st_mode = stat.S_IFREG | 0o644
    attr.st_size = 100
    attr.st_mtime = 1700000000.5

    fake_sftp = MagicMock()
    fake_sftp.listdir_attr.return_value = [attr]

    with patch.object(vfs, "_with_reconnect", side_effect=lambda fn, *args: fn(fake_sftp, *args)):
        items = vfs.listdir(PurePosixPath("/remote"))

    assert len(items) == 1
    assert items[0].modified == 1700000000.5
    assert isinstance(items[0].modified, float)


def test_sftp_listdir_modified_none_mtime():
    vfs = _make_sftp_vfs()
    attr = MagicMock()
    attr.filename = "file.txt"
    attr.st_mode = stat.S_IFREG | 0o644
    attr.st_size = 0
    attr.st_mtime = None

    fake_sftp = MagicMock()
    fake_sftp.listdir_attr.return_value = [attr]

    with patch.object(vfs, "_with_reconnect", side_effect=lambda fn, *args: fn(fake_sftp, *args)):
        items = vfs.listdir(PurePosixPath("/remote"))

    assert items[0].modified == 0.0
    assert isinstance(items[0].modified, float)


# ---------------------------------------------------------------------------
# Fix #2 — SFTPVfs.delete (renamed from remove)
# ---------------------------------------------------------------------------

def test_sftp_has_delete_not_remove():
    from biome_fm.models.sftp_vfs import SFTPVfs
    assert hasattr(SFTPVfs, "delete")
    assert not hasattr(SFTPVfs, "remove")


def test_sftp_delete_file():
    vfs = _make_sftp_vfs()
    fake_sftp = MagicMock()

    with patch.object(vfs, "_with_reconnect", side_effect=lambda fn, *args: fn(fake_sftp, *args)):
        vfs.delete(PurePosixPath("/remote/file.txt"))

    fake_sftp.remove.assert_called_once_with("/remote/file.txt")
    fake_sftp.rmdir.assert_not_called()


def test_sftp_delete_dir_falls_back_to_rmdir():
    vfs = _make_sftp_vfs()
    fake_sftp = MagicMock()
    fake_sftp.remove.side_effect = OSError("is a dir")

    with patch.object(vfs, "_with_reconnect", side_effect=lambda fn, *args: fn(fake_sftp, *args)):
        vfs.delete(PurePosixPath("/remote/mydir"))

    fake_sftp.rmdir.assert_called_once_with("/remote/mydir")


# ---------------------------------------------------------------------------
# Fix #3 — MkdirCmd uses VFS
# ---------------------------------------------------------------------------

def test_mkdir_cmd_uses_vfs():
    from biome_fm.commands.mkdir_cmd import MkdirCmd
    mock_vfs = MagicMock()
    mock_vfs.exists.return_value = False  # path does not exist — execute() proceeds
    path = Path("/tmp/newdir")
    MkdirCmd(path, mock_vfs).execute()
    mock_vfs.mkdir.assert_called_once_with(path)


def test_mkdir_cmd_accepts_valid_path():
    from biome_fm.commands.mkdir_cmd import MkdirCmd
    # Should not raise — normal valid name
    cmd = MkdirCmd(Path("/tmp/newdir"), MagicMock())
    assert cmd.description == "Create folder 'newdir'"


# ---------------------------------------------------------------------------
# Fix #5 — SQLite preview: SQL injection + XSS
# ---------------------------------------------------------------------------

def test_sqlite_preview_malicious_table_name():
    from biome_fm.preview.provider import ContentKind
    from biome_fm.preview.providers.sqlite_preview import SqlitePreviewProvider

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(str(db_path))
    # Malicious table name with bracket injection
    malicious = 'foo"] DROP TABLE bar; --'
    conn.execute(f'CREATE TABLE "{malicious.replace(chr(34), chr(34)*2)}" (id INTEGER)')
    conn.commit()
    conn.close()

    from biome_fm.preview.provider import PreviewRequest
    req = PreviewRequest(path=db_path)
    result = SqlitePreviewProvider().render(req)

    # Must NOT crash and must return HTML (not ERROR)
    assert result.kind == ContentKind.HTML
    # Table name must be HTML-escaped in output
    assert "DROP TABLE" not in result.data or "&quot;" in result.data or "&#" in result.data
    db_path.unlink(missing_ok=True)


def test_sqlite_preview_normal():
    from biome_fm.preview.provider import ContentKind, PreviewRequest
    from biome_fm.preview.providers.sqlite_preview import SqlitePreviewProvider

    with tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False) as f:
        db_path = Path(f.name)

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE alpha (x INTEGER)")
    conn.execute("CREATE TABLE beta (y TEXT)")
    conn.commit()
    conn.close()

    req = PreviewRequest(path=db_path)
    result = SqlitePreviewProvider().render(req)

    assert result.kind == ContentKind.HTML
    assert "alpha" in result.data
    assert "beta" in result.data
    db_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Fix #15 — atomic_write utility
# ---------------------------------------------------------------------------

def test_atomic_write_replaces_atomically(tmp_path):
    from biome_fm.utils.atomic_write import atomic_write
    p = tmp_path / "file.txt"
    atomic_write(p, "content A")
    atomic_write(p, "content B")
    assert p.read_text() == "content B"


def test_atomic_write_no_corruption_on_exception(tmp_path):
    from biome_fm.utils.atomic_write import atomic_write
    p = tmp_path / "file.txt"
    atomic_write(p, "original")
    with patch("pathlib.Path.replace", side_effect=OSError("locked")), pytest.raises(OSError):
        atomic_write(p, "new")
    # Original file unchanged
    assert p.read_text() == "original"


def test_atomic_write_creates_parent_dir(tmp_path):
    from biome_fm.utils.atomic_write import atomic_write
    p = tmp_path / "nested" / "deep" / "file.txt"
    atomic_write(p, "hello")
    assert p.read_text() == "hello"


# ---------------------------------------------------------------------------
# Fix #28 — SpaceReclaimerPresenter marshal_fn
# ---------------------------------------------------------------------------

def test_space_reclaimer_on_results_via_marshal(tmp_path):
    from biome_fm.presenters.space_reclaimer_presenter import SpaceReclaimerPresenter

    results = []
    marshaled_calls = []

    def fake_marshal(fn):
        marshaled_calls.append(fn)
        fn()  # simulate Qt main-thread dispatch

    with patch("biome_fm.presenters.space_reclaimer_presenter.scan_cleanup_dirs", return_value=[]):
        p = SpaceReclaimerPresenter(
            root=tmp_path,
            patterns=frozenset(),
            on_results=results.append,
            marshal_fn=fake_marshal,
        )
        p._scan()

    assert len(marshaled_calls) == 1  # marshal_fn was called


def test_space_reclaimer_no_marshal_fn(tmp_path):
    from biome_fm.presenters.space_reclaimer_presenter import SpaceReclaimerPresenter

    results = []

    with patch("biome_fm.presenters.space_reclaimer_presenter.scan_cleanup_dirs", return_value=[]):
        p = SpaceReclaimerPresenter(
            root=tmp_path,
            patterns=frozenset(),
            on_results=results.append,
        )
        p._scan()

    assert len(results) == 1  # on_results called directly


def test_space_reclaimer_cancel_suppresses_callback(tmp_path):
    from biome_fm.presenters.space_reclaimer_presenter import SpaceReclaimerPresenter

    results = []

    def slow_scan(*args, **kwargs):
        return []

    p = SpaceReclaimerPresenter(
        root=tmp_path,
        patterns=frozenset(),
        on_results=results.append,
    )
    p._cancel.set()  # cancel before scan

    with patch("biome_fm.presenters.space_reclaimer_presenter.scan_cleanup_dirs", side_effect=slow_scan):
        p._scan()

    assert results == []  # on_results never called


# ---------------------------------------------------------------------------
# Fix #26 — Plugin hook isolation
# ---------------------------------------------------------------------------

def test_plugin_hook_isolation_on_navigate(caplog):
    import logging

    from biome_fm.plugins.manager import PluginManager

    pm = PluginManager()

    class BadPlugin:
        @staticmethod
        def biome_fm_on_navigate(path):
            raise RuntimeError("plugin crash")

    # Patch the hook to raise
    with patch.object(pm._pm.hook, "on_navigate", side_effect=RuntimeError("plugin crash")), caplog.at_level(logging.ERROR):
        pm.on_navigate(Path("/some/path"))  # must NOT propagate

    assert "Plugin hook on_navigate raised" in caplog.text


def test_plugin_hook_isolation_preview_providers(caplog):
    import logging

    from biome_fm.plugins.manager import PluginManager

    pm = PluginManager()

    with patch.object(pm._pm.hook, "provide_preview_providers", side_effect=RuntimeError("crash")), caplog.at_level(logging.ERROR):
        result = pm.get_preview_providers()

    assert result == []
    assert "Plugin hook provide_preview_providers raised" in caplog.text


# ---------------------------------------------------------------------------
# Fix #16 — git_worker.stop() in _on_close (smoke test, no Qt)
# ---------------------------------------------------------------------------

def test_git_worker_stop_called_on_close():
    """Verify stop() exists and _on_close() references git_worker.stop()."""
    from biome_fm.git.worker import GitStatusWorker

    assert hasattr(GitStatusWorker, "stop")
    app_src = (Path(__file__).resolve().parents[2] / "src/biome_fm/app.py").read_text()
    assert "git_worker.stop" in app_src, "_on_close must call git_worker.stop"


# ---------------------------------------------------------------------------
# Fix #11 — No duplicate QShortcut bindings
# ---------------------------------------------------------------------------

def test_no_duplicate_shortcuts():
    import re
    app_src = (Path(__file__).resolve().parents[2] / "src/biome_fm/app.py").read_text()
    shortcuts = re.findall(r'QShortcut\s*\(\s*QKeySequence\s*\(\s*"([^"]+)"', app_src)
    dupes = [k for k in set(shortcuts) if shortcuts.count(k) > 1]
    assert not dupes, f"Duplicate shortcuts in app.py: {dupes}"
