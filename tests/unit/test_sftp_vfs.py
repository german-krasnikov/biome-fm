from pathlib import Path
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
