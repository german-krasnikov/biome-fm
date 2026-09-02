import shutil
from io import BytesIO
from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.models.sftp_vfs import SFTPSession, SFTPVfs, parse_sftp_uri


def test_parse_user_host_path():
    s = parse_sftp_uri("sftp://user@host/path")
    assert s == SFTPSession(host="host", port=22, user="user", remote_path="/path")


def test_parse_no_user():
    s = parse_sftp_uri("sftp://host/path")
    assert s is not None
    assert s.user == ""
    assert s.host == "host"


def test_parse_custom_port():
    s = parse_sftp_uri("sftp://host:2222/data")
    assert s is not None
    assert s.port == 2222


def test_parse_invalid():
    assert parse_sftp_uri("not-sftp://x") is None
    assert parse_sftp_uri("http://host/path") is None


def test_available_without_paramiko():
    # paramiko likely not installed in test env
    # This test is valid either way
    result = SFTPVfs.available()
    assert isinstance(result, bool)


def test_listdir_without_paramiko():
    if SFTPVfs.available():
        pytest.skip("paramiko is installed")
    session = SFTPSession(host="localhost")
    vfs = SFTPVfs(session)
    with pytest.raises(RuntimeError, match="paramiko"):
        vfs.listdir(Path("/"))


# ── Security: proxy command injection prevention ─────────────────────────────

from biome_fm.models.sftp_vfs import make_jump_proxy_command


def test_make_jump_proxy_command_quotes_hostname():
    result = make_jump_proxy_command(
        jump_host="evil; rm -rf ~",
        jump_port=22,
        jump_user="",
        target_host="target.example.com",
        target_port=22,
    )
    # semicolon inside single-quoted arg, not at shell top-level
    assert "'evil; rm -rf ~'" in result
    # strip the quoted part and verify no bare semicolon remains
    assert ";" not in result.replace("'evil; rm -rf ~'", "")


def test_make_jump_proxy_command_quotes_jump_user():
    result = make_jump_proxy_command(
        jump_host="jump.host",
        jump_port=22,
        jump_user="user; evil",
        target_host="target",
        target_port=2222,
    )
    assert "'user; evil'@" in result


def test_make_jump_proxy_command_normal_case():
    result = make_jump_proxy_command("jump.host", 22, "alice", "target.host", 2222)
    assert "alice@" in result
    assert "target.host" in result
    assert "-p 22" in result
    assert "-W" in result


# ── C13: open_read must hold channel for full lifetime of file handle ─────────

def test_open_read_holds_channel_during_yield():
    from tests.unit.test_sftp_connection_pool import _make_sftp_vfs

    vfs, _orig, _mod = _make_sftp_vfs(max_channels=1)
    try:
        fake_ch = MagicMock(name="sftp_ch")
        fake_ch.open.return_value = MagicMock(name="fh")
        vfs._client.open_sftp.return_value = fake_ch
        vfs._channels = [fake_ch]  # pre-seed pool — semaphore._value already 1

        with vfs.open_read(PurePosixPath("/remote/file.txt")):
            # Channel must be held (not back in pool) while file handle is live
            assert vfs._channels == []
            assert vfs._semaphore._value == 0

        # After context exit: channel returned to pool
        assert len(vfs._channels) == 1
        assert vfs._semaphore._value == 1
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig


# ── C54: exists / copy / move satisfy WritableVFS ────────────────────────────

def _setup_vfs_with_channel():
    """Return (vfs, fake_ch, _orig, _mod)."""
    from tests.unit.test_sftp_connection_pool import _make_sftp_vfs

    vfs, _orig, _mod = _make_sftp_vfs(max_channels=1)
    fake_ch = MagicMock(name="sftp_ch")
    vfs._channels = [fake_ch]
    return vfs, fake_ch, _orig, _mod


def test_sftp_exists_true():
    vfs, fake_ch, _orig, _mod = _setup_vfs_with_channel()
    try:
        fake_ch.stat.return_value = MagicMock()
        assert vfs.exists(PurePosixPath("/remote/file.txt")) is True
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig


def test_sftp_exists_false():
    vfs, fake_ch, _orig, _mod = _setup_vfs_with_channel()
    try:
        fake_ch.stat.side_effect = FileNotFoundError("/no/such")
        assert vfs.exists(PurePosixPath("/no/such")) is False
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig


class _NocloseFile:
    """BytesIO wrapper whose __exit__ does NOT close the buffer."""

    def __init__(self, buf: BytesIO) -> None:
        self._buf = buf

    def read(self, n: int = -1) -> bytes:
        return self._buf.read(n)

    def write(self, data: bytes) -> int:
        return self._buf.write(data)

    def __enter__(self):
        return self

    def __exit__(self, *_):
        pass  # keep the buffer open so getvalue() works after


def test_sftp_copy_streams_via_read_write():
    vfs, fake_ch, _orig, _mod = _setup_vfs_with_channel()
    try:
        dst_raw = BytesIO()
        src_f = _NocloseFile(BytesIO(b"hello"))
        dst_f = _NocloseFile(dst_raw)

        def fake_open(path, mode):
            return src_f if "r" in mode else dst_f

        fake_ch.open.side_effect = fake_open

        sem_vals: list[int] = []
        _real_copyfileobj = shutil.copyfileobj

        def _capture_copy(fi, fo, *args, **kwargs):
            sem_vals.append(vfs._semaphore._value)
            _real_copyfileobj(fi, fo, *args, **kwargs)

        with patch("biome_fm.models.sftp_vfs.shutil.copyfileobj", _capture_copy):
            vfs.copy(PurePosixPath("/src/f.txt"), PurePosixPath("/dst/f.txt"))

        assert dst_raw.getvalue() == b"hello"
        assert sem_vals == [0]  # exactly one channel held during the copy
        assert vfs._semaphore._value == 1  # returned after call
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig


def test_sftp_copy_safe_at_max_channels_1():
    """copy() with max_channels=1 must complete without deadlock."""
    vfs, fake_ch, _orig, _mod = _setup_vfs_with_channel()
    try:
        src_f = _NocloseFile(BytesIO(b"data"))
        dst_f = _NocloseFile(BytesIO())

        def fake_open(path, mode):
            return src_f if "r" in mode else dst_f

        fake_ch.open.side_effect = fake_open
        vfs.copy(PurePosixPath("/a"), PurePosixPath("/b"))
        assert vfs._semaphore._value == 1
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig


def test_sftp_move_calls_rename():
    vfs, fake_ch, _orig, _mod = _setup_vfs_with_channel()
    try:
        fake_ch.stat.side_effect = FileNotFoundError("/dst")
        src = PurePosixPath("/src/f.txt")
        dst = PurePosixPath("/dst/f.txt")
        vfs.move(src, dst)
        fake_ch.rename.assert_called_once_with(str(src), str(dst))
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig


def test_sftp_move_raises_file_exists_if_dst_present():
    vfs, fake_ch, _orig, _mod = _setup_vfs_with_channel()
    try:
        fake_ch.stat.return_value = MagicMock()  # dst exists
        src = PurePosixPath("/src/f.txt")
        dst = PurePosixPath("/dst/f.txt")
        with pytest.raises(FileExistsError):
            vfs.move(src, dst)
        fake_ch.rename.assert_not_called()
    finally:
        _mod._HAS_PARAMIKO, _mod._paramiko = _orig
