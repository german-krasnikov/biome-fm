"""TDD: SFTP VFS full implementation."""
from __future__ import annotations

from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch


def _make_sftp_vfs():
    from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs

    session = SFTPSession(host="example.com", port=22, user="alice")
    return SFTPVfs(session)


def test_no_paramiko_graceful() -> None:
    """Without paramiko, SFTPVfs.available() is False and connect raises."""
    import biome_fm.models.sftp_vfs as mod

    orig = mod._HAS_PARAMIKO
    try:
        mod._HAS_PARAMIKO = False
        vfs = _make_sftp_vfs()
        assert not vfs.available()
        try:
            vfs.connect()
            assert False, "Should have raised"
        except RuntimeError as e:
            assert "paramiko" in str(e).lower()
    finally:
        mod._HAS_PARAMIKO = orig


def test_listdir_mocked() -> None:
    """listdir converts SFTPAttributes to FileItem list."""
    import biome_fm.models.sftp_vfs as mod

    if not mod._HAS_PARAMIKO:
        import pytest
        pytest.skip("paramiko not installed")

    vfs = _make_sftp_vfs()

    # Mock the SFTP client
    attr1 = MagicMock()
    attr1.filename = "foo.txt"
    attr1.st_size = 42
    attr1.st_mtime = 0
    import stat as _stat
    attr1.st_mode = _stat.S_IFREG | 0o644

    attr2 = MagicMock()
    attr2.filename = "bar"
    attr2.st_size = 0
    attr2.st_mtime = 0
    attr2.st_mode = _stat.S_IFDIR | 0o755

    mock_sftp = MagicMock()
    mock_sftp.listdir_attr.return_value = [attr1, attr2]
    vfs._sftp = mock_sftp

    items = vfs.listdir(PurePosixPath("/remote"))
    assert len(items) == 2
    names = {i.name for i in items}
    assert "foo.txt" in names
    assert "bar" in names
    dirs = [i for i in items if i.is_dir]
    assert len(dirs) == 1
    assert dirs[0].name == "bar"


def test_read_bytes_mocked() -> None:
    """read_bytes delegates to sftp.open."""
    import biome_fm.models.sftp_vfs as mod

    if not mod._HAS_PARAMIKO:
        import pytest
        pytest.skip("paramiko not installed")

    vfs = _make_sftp_vfs()
    mock_sftp = MagicMock()
    mock_file = MagicMock()
    mock_file.read.return_value = b"hello"
    mock_sftp.open.return_value.__enter__ = lambda s: mock_file
    mock_sftp.open.return_value.__exit__ = MagicMock(return_value=False)
    vfs._sftp = mock_sftp

    data = vfs.read_bytes(PurePosixPath("/remote/foo.txt"))
    assert data == b"hello"


def test_sftp_connect_dialog_has_fields(qtbot) -> None:
    """SFTPConnectDialog exposes host, port, user, password fields."""
    from biome_fm.views.sftp_connect_dialog import SFTPConnectDialog

    w = SFTPConnectDialog()
    qtbot.addWidget(w)
    assert hasattr(w, "_host")
    assert hasattr(w, "_port")
    assert hasattr(w, "_user")
    assert hasattr(w, "_password")
