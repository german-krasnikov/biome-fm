"""Sprint 2 cleanup tests — format_size, run_git, ls_parser, uri_parser relocation."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch


# ── format_size ────────────────────────────────────────────────────────────────

from biome_fm.utils.format import format_size


def test_format_size_bytes():
    assert format_size(0) == "0 B"
    assert format_size(320) == "320 B"
    assert format_size(1023) == "1023 B"


def test_format_size_kb():
    assert format_size(1024) == "1.0 KB"
    assert format_size(1536) == "1.5 KB"


def test_format_size_mb():
    assert format_size(1_048_576) == "1.0 MB"
    assert format_size(1_572_864) == "1.5 MB"


def test_format_size_gb():
    assert format_size(1_073_741_824) == "1.0 GB"


def test_format_size_tb():
    assert format_size(1_099_511_627_776) == "1.0 TB"


def test_format_size_pb():
    assert format_size(1_125_899_906_842_624) == "1.0 PB"


# ── run_git ────────────────────────────────────────────────────────────────────

from biome_fm.git.run import run_git


def test_run_git_returns_stdout(tmp_path):
    mock_result = MagicMock()
    mock_result.stdout = "main\n"
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = run_git(["branch", "--show-current"], cwd=tmp_path)
    assert result == "main\n"
    mock_run.assert_called_once_with(
        ["git", "branch", "--show-current"],
        cwd=tmp_path,
        capture_output=True, text=True, timeout=5, check=True,
    )


def test_run_git_check_false(tmp_path):
    mock_result = MagicMock()
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        run_git(["check-ignore", "-q", "file.txt"], cwd=tmp_path, check=False)
    _, kwargs = mock_run.call_args
    assert kwargs["check"] is False


def test_run_git_custom_timeout(tmp_path):
    mock_result = MagicMock()
    mock_result.stdout = ""
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        run_git(["add", "."], cwd=tmp_path, timeout=10)
    _, kwargs = mock_run.call_args
    assert kwargs["timeout"] == 10


# ── ls_parser ─────────────────────────────────────────────────────────────────

from biome_fm.models.ls_parser import parse_ls_line


def test_parse_ls_line_file():
    line = "-rw-r--r-- 1 user group 1234 2024-01-15 12:30 README.md"
    r = parse_ls_line(line)
    assert r is not None
    assert r["name"] == "README.md"
    assert r["is_dir"] is False
    assert r["size"] == 1234


def test_parse_ls_line_dir():
    line = "drwxr-xr-x 2 user group 4096 2024-01-15 12:30 src"
    r = parse_ls_line(line)
    assert r is not None
    assert r["is_dir"] is True
    assert r["name"] == "src"


def test_parse_ls_line_no_match():
    assert parse_ls_line("total 42") is None
    assert parse_ls_line("") is None


def test_parse_ls_line_mtime():
    from datetime import datetime
    line = "-rw-r--r-- 1 u g 100 2024-06-01 09:00 file.txt"
    r = parse_ls_line(line)
    assert r is not None
    expected = datetime(2024, 6, 1, 9, 0).timestamp()
    assert r["mtime"] == expected


# ── uri_parser import from new location ───────────────────────────────────────

def test_uri_parser_importable_from_utils():
    from biome_fm.utils.uri_parser import detect_scheme, parse_uri, ParsedURI
    assert detect_scheme("sftp://host/path") == "sftp"
    r = parse_uri("sftp://alice@host:22/home")
    assert r.scheme == "sftp"
    assert r.username == "alice"


def test_uri_parser_shim_still_works():
    # backward-compat shim must still export the same names
    from biome_fm.presenters.uri_parser import detect_scheme, parse_uri, ParsedURI
    assert detect_scheme("s3://bucket") == "s3"
