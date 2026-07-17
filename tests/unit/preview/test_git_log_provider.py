"""Unit tests for GitLogPreviewProvider."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from biome_fm.preview.provider import ContentKind, PreviewRequest


def test_render_log(tmp_path):
    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("x")

    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    p = GitLogPreviewProvider()

    fake = MagicMock(stdout="abc1234 initial commit\n", returncode=0)
    with patch("biome_fm.preview.providers.git_log.subprocess.run", return_value=fake):
        result = p.render(PreviewRequest(path=f))

    assert result.kind == ContentKind.HTML
    assert "abc1234" in result.data or "commit" in result.data.lower()


def test_no_git_graceful(tmp_path):
    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("x")

    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    p = GitLogPreviewProvider()

    with patch("biome_fm.preview.providers.git_log.subprocess.run", side_effect=FileNotFoundError):
        result = p.render(PreviewRequest(path=f))

    assert result.kind == ContentKind.TEXT
    assert "git" in result.data.lower()


def test_can_handle_in_repo(tmp_path):
    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("x")
    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    assert GitLogPreviewProvider().can_handle(f) is True


def test_can_handle_outside_repo(tmp_path):
    f = tmp_path / "foo.py"
    f.write_text("x")
    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    assert GitLogPreviewProvider().can_handle(f) is False
