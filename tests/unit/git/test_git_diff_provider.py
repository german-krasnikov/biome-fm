"""Unit tests for GitDiffPreviewProvider — TDD red phase."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest


# ---------------------------------------------------------------------------
# can_handle
# ---------------------------------------------------------------------------

def test_can_handle_no_status_fn():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    p = GitDiffPreviewProvider(status_fn=None)
    assert p.can_handle(Path("/any/file.py")) is False


def test_can_handle_clean_file():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    p = GitDiffPreviewProvider(status_fn=lambda _: None)
    assert p.can_handle(Path("/repo/clean.py")) is False


def test_can_handle_untracked():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    p = GitDiffPreviewProvider(status_fn=lambda _: "??")
    assert p.can_handle(Path("/repo/new.py")) is False


def test_can_handle_modified():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    p = GitDiffPreviewProvider(status_fn=lambda _: " M")
    assert p.can_handle(Path("/repo/modified.py")) is True


def test_can_handle_binary_ext():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    p = GitDiffPreviewProvider(status_fn=lambda _: " M")
    assert p.can_handle(Path("/repo/image.png")) is False


# ---------------------------------------------------------------------------
# render
# ---------------------------------------------------------------------------

_SAMPLE_DIFF = """\
diff --git a/foo.py b/foo.py
index 1234..5678 100644
--- a/foo.py
+++ b/foo.py
@@ -1,3 +1,4 @@
 line1
+line2
 line3
"""


def _provider_with_mock_subprocess(diff_output: str, *, raise_exc=None):
    """Return a provider whose _find_repo returns a fake repo and subprocess is mocked."""
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider

    p = GitDiffPreviewProvider(status_fn=lambda _: " M")

    if raise_exc:
        mock_run = MagicMock(side_effect=raise_exc)
    else:
        mock_run = MagicMock(return_value=MagicMock(stdout=diff_output, returncode=0))

    return p, mock_run


def test_render_returns_html_with_diff(tmp_path):
    """Mock subprocess → HTML result containing diff markup."""
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider

    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("line1\nline3\n")

    p = GitDiffPreviewProvider(status_fn=lambda _: " M")

    fake_result = MagicMock(stdout=_SAMPLE_DIFF, returncode=0)
    with patch("biome_fm.preview.providers.git_diff.subprocess.run", return_value=fake_result):
        result = p.render(PreviewRequest(path=f))

    assert result.kind == ContentKind.HTML
    assert isinstance(result.data, str)
    assert "+" in result.data or "diff" in result.data.lower()


def test_render_no_diff_output(tmp_path):
    """subprocess returns empty stdout → '(no diff)'."""
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider

    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("x")

    p = GitDiffPreviewProvider(status_fn=lambda _: " M")

    fake_result = MagicMock(stdout="", returncode=0)
    with patch("biome_fm.preview.providers.git_diff.subprocess.run", return_value=fake_result):
        result = p.render(PreviewRequest(path=f))

    assert result.data == "(no diff)"


def test_render_git_not_found(tmp_path):
    """subprocess raises FileNotFoundError → '(git not available)'."""
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider

    (tmp_path / ".git").mkdir()
    f = tmp_path / "foo.py"
    f.write_text("x")

    p = GitDiffPreviewProvider(status_fn=lambda _: " M")

    with patch("biome_fm.preview.providers.git_diff.subprocess.run", side_effect=FileNotFoundError):
        result = p.render(PreviewRequest(path=f))

    assert result.data == "(git not available)"


def test_priority_is_lower_than_code_provider():
    """GitDiffPreviewProvider.priority must be lower (higher prio) than CodePreviewProvider."""
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    from biome_fm.preview.providers.code import CodePreviewProvider

    assert GitDiffPreviewProvider.priority < CodePreviewProvider.priority
