"""TDD tests for ScriptVFS (extfs-style archive browsing via shell scripts)."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from biome_fm.models.script_vfs import ScriptVFS, ScriptVFSSpec, load_script_vfs_specs


ARCHIVE = Path("/fake/archive.rpm")


@pytest.fixture
def spec():
    return ScriptVFSSpec(
        extensions=[".rpm"],
        list_cmd="rpm_list {archive} {dir}",
        read_cmd="rpm_read {archive} {path}",
        timeout=5,
    )


def test_listdir_parses_tab_output(spec, monkeypatch):
    output = "f\t1234\t1234567890\tfile.txt\nd\t0\t0\tsubdir\n"
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: output)

    items = ScriptVFS(ARCHIVE, spec).listdir(ARCHIVE)

    assert len(items) == 2
    assert items[0].name == "file.txt"
    assert items[0].is_dir is False
    assert items[0].size == 1234
    assert items[0].modified == 1234567890.0
    assert items[1].name == "subdir"
    assert items[1].is_dir is True


def test_read_bytes_calls_read_cmd(spec, monkeypatch):
    captured = {}

    def fake_check_output(cmd, **kw):
        captured["cmd"] = cmd
        return b"hello"

    monkeypatch.setattr(subprocess, "check_output", fake_check_output)

    result = ScriptVFS(ARCHIVE, spec).read_bytes(ARCHIVE / "file.txt")

    assert result == b"hello"
    assert "archive.rpm" in captured["cmd"]
    assert "file.txt" in captured["cmd"]


def test_listdir_handles_error(spec, monkeypatch):
    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *a, **kw: (_ for _ in ()).throw(subprocess.CalledProcessError(1, "cmd")),
    )

    assert ScriptVFS(ARCHIVE, spec).listdir(ARCHIVE) == []


def test_load_script_vfs_specs(tmp_path):
    (tmp_path / "rpm.toml").write_text(
        'extensions = [".rpm"]\nlist_cmd = "rpm_ls {archive} {dir}"\nread_cmd = "rpm_cat {archive} {path}"\ntimeout = 15\n'
    )
    specs = load_script_vfs_specs(tmp_path)

    assert len(specs) == 1
    assert specs[0].extensions == [".rpm"]
    assert specs[0].list_cmd == "rpm_ls {archive} {dir}"
    assert specs[0].timeout == 15


def test_open_file_returns_bytesio(spec, monkeypatch):
    monkeypatch.setattr(subprocess, "check_output", lambda *a, **kw: b"content")

    vfs = ScriptVFS(ARCHIVE, spec)
    with vfs.open_file(ARCHIVE / "readme.txt") as f:
        assert f.read() == b"content"
