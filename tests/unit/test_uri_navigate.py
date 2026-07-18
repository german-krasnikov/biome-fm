"""URI parser unit tests — F040."""
import pytest
from biome_fm.presenters.uri_parser import ParsedURI, detect_scheme, parse_uri


def test_detect_uri_scheme():
    assert detect_scheme("sftp://host/path") == "sftp"


def test_detect_s3_uri():
    assert detect_scheme("s3://bucket/key") == "s3"


def test_plain_path_no_scheme():
    assert detect_scheme("/home/user") is None


def test_windows_path_no_scheme():
    assert detect_scheme("C:\\Users\\foo") is None


def test_parse_sftp_uri():
    r = parse_uri("sftp://alice@myhost:2222/home/alice")
    assert r.scheme == "sftp"
    assert r.host == "myhost"
    assert r.port == 2222
    assert r.path == "/home/alice"
    assert r.username == "alice"


def test_parse_malformed_port_no_crash():
    """urlparse.port raises ValueError for non-integer ports — must be caught."""
    r = parse_uri("sftp://host:notaport/path")
    assert r.port is None
    assert r.host == "host"


def test_parse_empty_string():
    r = parse_uri("")
    assert r.scheme == ""
    assert r.host == ""
    assert r.port is None


def test_detect_unknown_scheme_with_protocol_separator():
    """http / unknown schemes must not be treated as known VFS schemes."""
    assert detect_scheme("http://example.com") is None


def test_detect_sftp_no_host():
    """sftp:// with no host still has a known scheme."""
    assert detect_scheme("sftp://") == "sftp"
