from pathlib import Path, PurePosixPath
from unittest.mock import MagicMock

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
