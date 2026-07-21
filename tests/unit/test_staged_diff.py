"""Unit tests for staged_diff() — no Qt needed."""
import subprocess

from biome_fm.git.commit_ops import staged_diff


def test_staged_diff_no_repo(tmp_path):
    assert staged_diff(tmp_path) == ""


def test_staged_diff_with_changes(tmp_path):
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t.com"], cwd=tmp_path, check=True, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "T"], cwd=tmp_path, check=True, capture_output=True
    )
    f = tmp_path / "a.txt"
    f.write_text("content\n")
    subprocess.run(["git", "add", "a.txt"], cwd=tmp_path, check=True, capture_output=True)

    diff = staged_diff(tmp_path)
    assert "+content" in diff
