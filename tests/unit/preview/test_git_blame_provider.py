"""Unit tests for GitBlamePreviewProvider."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from biome_fm.preview.provider import ContentKind, PreviewRequest

_BLAME_OUT = """\
abc1234 1 1 1
author Jane
summary initial commit
filename foo.py
\tline content here
"""


def test_render_blame(tmp_path):
    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("line content here\n")

    from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
    p = GitBlamePreviewProvider()

    fake = MagicMock(stdout=_BLAME_OUT, returncode=0)
    with patch("biome_fm.preview.providers.git_blame.subprocess.run", return_value=fake):
        result = p.render(PreviewRequest(path=f))

    assert result.kind == ContentKind.HTML
    assert "abc1234" in result.data or "Jane" in result.data


def test_render_blame_no_git(tmp_path):
    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("x")

    from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
    p = GitBlamePreviewProvider()

    with patch("biome_fm.preview.providers.git_blame.subprocess.run", side_effect=FileNotFoundError):
        result = p.render(PreviewRequest(path=f))

    assert result.kind == ContentKind.TEXT
