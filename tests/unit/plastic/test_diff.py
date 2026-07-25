"""Unit tests for _diff.py — workspace_diff(), get_server_path(), cs_diff()."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from biome_fm.plastic._cm import CMError
from biome_fm.plastic._diff import (
    branch_diff,
    count_diff_lines,
    cs_diff,
    cs_log_files,
    cs_range_diff,
    get_server_path,
    is_binary,
    is_image,
    label_range_diff,
    parse_cs_diff_files,
    shelve_diff,
    workspace_diff,
)


# ── workspace_diff ────────────────────────────────────────────────────────────

def test_workspace_diff_returns_run_cm_output(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="--- a\n+++ b\n") as m:
        result = workspace_diff(tmp_path / "file.py", tmp_path)
    assert result == "--- a\n+++ b\n"


def test_workspace_diff_passes_unified_format(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        workspace_diff(tmp_path / "file.py", tmp_path)
    args = m.call_args.args[0]
    assert "--format=unified" in args


def test_workspace_diff_safe_true(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        workspace_diff(tmp_path / "file.py", tmp_path)
    assert m.call_args.kwargs.get("safe") is True


def test_workspace_diff_returns_empty_on_no_changes(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value=""):
        assert workspace_diff(tmp_path / "file.py", tmp_path) == ""


# ── get_server_path ───────────────────────────────────────────────────────────

def test_get_server_path_returns_first_line_if_absolute(tmp_path):
    out = "/src/main/file.py\n cs:42 (07/24/2026 12:00:00) by alice\n"
    with patch("biome_fm.plastic._diff.run_cm", return_value=out):
        result = get_server_path(tmp_path / "file.py", tmp_path)
    assert result == "/src/main/file.py"


def test_get_server_path_returns_none_if_not_absolute(tmp_path):
    # First line doesn't start with /
    out = "src/file.py\n cs:42\n"
    with patch("biome_fm.plastic._diff.run_cm", return_value=out):
        result = get_server_path(tmp_path / "file.py", tmp_path)
    assert result is None


def test_get_server_path_returns_none_on_empty_output(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value=""):
        result = get_server_path(tmp_path / "file.py", tmp_path)
    assert result is None


def test_get_server_path_calls_fileinfo(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        get_server_path(tmp_path / "file.py", tmp_path)
    assert m.call_args.args[0][0] == "fileinfo"


# ── cs_diff ───────────────────────────────────────────────────────────────────

def _getfile_writes(content: str):
    """Return a run_cm side_effect that writes *content* to the --file= path."""
    def _side_effect(args, cwd=None, safe=False):
        for arg in args:
            if arg.startswith("--file="):
                Path(arg[7:]).write_text(content)
                return ""
        return ""
    return _side_effect


def test_cs_diff_returns_unified_diff(tmp_path):
    local = tmp_path / "file.py"
    local.write_text("line2\n")

    with patch("biome_fm.plastic._diff.run_cm", side_effect=_getfile_writes("line1\n")):
        result = cs_diff(local, cs_id=5, server_path="/src/file.py", cwd=tmp_path)

    assert "line1" in result
    assert "line2" in result
    assert "---" in result
    assert "+++" in result


def test_cs_diff_uses_provided_server_path(tmp_path):
    local = tmp_path / "file.py"
    local.write_text("")
    captured = []

    def _capture(args, cwd=None, safe=False):
        captured.extend(args)
        for arg in args:
            if arg.startswith("--file="):
                Path(arg[7:]).write_text("")
        return ""

    with patch("biome_fm.plastic._diff.run_cm", side_effect=_capture):
        cs_diff(local, cs_id=7, server_path="/custom/path.py", cwd=tmp_path)

    assert any("/custom/path.py#cs:7" in a for a in captured)


def test_cs_diff_falls_back_to_filename_when_server_path_none(tmp_path):
    local = tmp_path / "myfile.py"
    local.write_text("")
    captured = []

    def _capture(args, cwd=None, safe=False):
        captured.extend(args)
        for arg in args:
            if arg.startswith("--file="):
                Path(arg[7:]).write_text("")
        return ""

    # get_server_path will return None (empty output for fileinfo)
    with patch("biome_fm.plastic._diff.run_cm", side_effect=_capture):
        cs_diff(local, cs_id=3, server_path=None, cwd=tmp_path)

    # Falls back to bare filename
    assert any("myfile.py#cs:3" in a for a in captured)


def test_cs_diff_returns_empty_on_cmerror(tmp_path):
    local = tmp_path / "file.py"
    local.write_text("content\n")

    def _fail(args, cwd=None, safe=False):
        if "getfile" in args:
            raise CMError("not in repo")
        # fileinfo call returns ""
        return ""

    with patch("biome_fm.plastic._diff.run_cm", side_effect=_fail):
        result = cs_diff(local, cs_id=1, server_path="/src/file.py", cwd=tmp_path)
    assert result == ""


def test_cs_diff_empty_when_local_file_missing(tmp_path):
    local = tmp_path / "gone.py"
    # Don't create the file — cs_diff should handle OSError gracefully

    def _write(args, cwd=None, safe=False):
        for arg in args:
            if arg.startswith("--file="):
                Path(arg[7:]).write_text("base\n")
        return ""

    with patch("biome_fm.plastic._diff.run_cm", side_effect=_write):
        result = cs_diff(local, cs_id=1, server_path="/gone.py", cwd=tmp_path)

    # No exception; diff shows base content removed (or empty)
    assert isinstance(result, str)


def test_cs_diff_returns_empty_for_identical_files(tmp_path):
    content = "same line\n"
    local = tmp_path / "file.py"
    local.write_text(content)

    with patch("biome_fm.plastic._diff.run_cm", side_effect=_getfile_writes(content)):
        result = cs_diff(local, cs_id=1, server_path="/file.py", cwd=tmp_path)
    assert result == ""


# ── is_binary ─────────────────────────────────────────────────────────────────

def test_is_binary_detects_null_bytes(tmp_path):
    f = tmp_path / "img.bin"
    f.write_bytes(b"PNG\x00\x00header")
    assert is_binary(f) is True


def test_is_binary_false_for_text(tmp_path):
    f = tmp_path / "file.py"
    f.write_text("def foo(): pass\n")
    assert is_binary(f) is False


def test_is_binary_false_on_missing_file(tmp_path):
    assert is_binary(tmp_path / "ghost.py") is False


def test_workspace_diff_returns_placeholder_for_binary(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"\x00\x01\x02")
    with patch("biome_fm.plastic._diff.run_cm") as m:
        result = workspace_diff(f, tmp_path)
    m.assert_not_called()
    assert result == "(binary file — diff not available)"


def test_cs_diff_returns_placeholder_for_binary(tmp_path):
    local = tmp_path / "data.bin"
    local.write_bytes(b"\x00\x01\x02")
    with patch("biome_fm.plastic._diff.run_cm") as m:
        result = cs_diff(local, cs_id=1, server_path="/data.bin", cwd=tmp_path)
    m.assert_not_called()
    assert result == "(binary file — diff not available)"


# ── count_diff_lines ──────────────────────────────────────────────────────────

def test_count_diff_lines_basic():
    diff = "--- a\n+++ b\n@@ -1,1 +1,2 @@\n-old\n+new\n+extra\n"
    assert count_diff_lines(diff) == (2, 1)


def test_count_diff_lines_empty():
    assert count_diff_lines("") == (0, 0)


# ── Advanced diff variants (4.8) ─────────────────────────────────────────────

def test_cs_range_diff_builds_correct_range_arg(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="diff") as m:
        cs_range_diff(5, 7, tmp_path)
    assert m.call_args.args[0] == ["diff", "cs:5..cs:7"]


def test_branch_diff_normalizes_br_prefix(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        branch_diff("main", tmp_path)
    assert m.call_args.args[0] == ["diff", "br:main"]


def test_branch_diff_keeps_existing_prefix(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        branch_diff("br:main", tmp_path)
    assert m.call_args.args[0] == ["diff", "br:main"]


def test_label_range_diff_correct_args(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        label_range_diff("v1", "v2", tmp_path)
    assert m.call_args.args[0] == ["diff", "lb:v1..lb:v2"]


def test_shelve_diff_correct_args(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        shelve_diff(3, tmp_path)
    assert m.call_args.args[0] == ["diff", "sh:3"]


# ── is_image ──────────────────────────────────────────────────────────────────

def test_is_image_png():
    assert is_image(Path("sprite.png")) is True


def test_is_image_case_insensitive():
    assert is_image(Path("tex.TGA")) is True


def test_is_image_false_for_python():
    assert is_image(Path("main.py")) is False


# ── parse_cs_diff_files ───────────────────────────────────────────────────────

_MODIFIED_DIFF = """\
diff --git a/src/file.py b/src/file.py
--- a/src/file.py
+++ b/src/file.py
@@ -1,2 +1,3 @@
 unchanged
-removed
+added
+extra
"""

_ADDED_DIFF = """\
diff --git a/new.py b/new.py
--- /dev/null
+++ b/new.py
@@ -0,0 +1,2 @@
+line1
+line2
"""

_DELETED_DIFF = """\
diff --git a/old.py b/old.py
--- a/old.py
+++ /dev/null
@@ -1,2 +0,0 @@
-line1
-line2
"""


def test_parse_cs_diff_files_modified():
    files = parse_cs_diff_files(_MODIFIED_DIFF)
    assert len(files) == 1
    f = files[0]
    assert f.status == "M"
    assert f.path == "src/file.py"   # git prefix stripped
    assert f.added == 2
    assert f.removed == 1


def test_parse_cs_diff_files_added():
    files = parse_cs_diff_files(_ADDED_DIFF)
    assert len(files) == 1
    assert files[0].status == "A"
    assert files[0].added == 2
    assert files[0].removed == 0


def test_parse_cs_diff_files_deleted():
    files = parse_cs_diff_files(_DELETED_DIFF)
    assert len(files) == 1
    assert files[0].status == "D"
    assert files[0].added == 0
    assert files[0].removed == 2


def test_parse_cs_diff_files_empty():
    assert parse_cs_diff_files("") == []


def test_parse_cs_diff_files_multiple():
    combined = _MODIFIED_DIFF + _ADDED_DIFF
    files = parse_cs_diff_files(combined)
    assert len(files) == 2


# ── cs_log_files ──────────────────────────────────────────────────────────────

_CM_LOG_OUTPUT = """\
Changeset number: 11
Branch: /main
Owner: yuri.voylenko.ff@playrix.com
Date: 08/05/2026 18:42:39
Comment: Added Workers
Changes:
C|Assets/12275/Animations/Egg_Packer/Egg_Packer.anim
A|Assets/12203/Prefabs/Worker_1.prefab
D|Assets/old/file.mat
M|Assets/moved/file.prefab
------------------------------------------------------------
"""


def test_cs_log_files_parses_all_statuses(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value=_CM_LOG_OUTPUT):
        files = cs_log_files(11, tmp_path)
    assert len(files) == 4
    statuses = {f.path.split("/")[-1]: f.status for f in files}
    assert statuses["Egg_Packer.anim"] == "M"   # C → M (changed)
    assert statuses["Worker_1.prefab"] == "A"
    assert statuses["file.mat"] == "D"
    assert statuses["file.prefab"] == "R"        # M → R (moved/renamed)


def test_cs_log_files_added_removed_zero(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value=_CM_LOG_OUTPUT):
        files = cs_log_files(11, tmp_path)
    assert all(f.added == 0 and f.removed == 0 for f in files)


def test_cs_log_files_diff_text_empty(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value=_CM_LOG_OUTPUT):
        files = cs_log_files(11, tmp_path)
    assert all(f.diff_text == "" for f in files)


def test_cs_log_files_empty_output(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value=""):
        files = cs_log_files(11, tmp_path)
    assert files == []


def test_cs_log_files_uses_correct_cm_args(tmp_path):
    with patch("biome_fm.plastic._diff.run_cm", return_value="") as m:
        cs_log_files(7, tmp_path)
    args = m.call_args.args[0]
    assert args[0] == "log"
    assert "cs:7" in args
    assert any("--itemformat" in a for a in args)


def test_cs_log_files_changes_header_present_but_no_items(tmp_path):
    """CS with no changed files: 'Changes:' section exists but is immediately followed by separator."""
    out = "Changeset number: 3\nBranch: /main\nChanges:\n----\n"
    with patch("biome_fm.plastic._diff.run_cm", return_value=out):
        files = cs_log_files(3, tmp_path)
    assert files == []
