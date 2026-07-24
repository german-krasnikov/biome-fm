"""Unit tests for PreviewRegistry — no Qt."""
from pathlib import Path

from biome_fm.preview.providers.fallback import FallbackProvider
from biome_fm.preview.providers.image import ImagePreviewProvider
from biome_fm.preview.providers.markdown import MarkdownPreviewProvider
from biome_fm.preview.providers.text import TextPreviewProvider
from biome_fm.preview.registry import PreviewRegistry


def test_markdown_wins_over_text():
    reg = PreviewRegistry()
    reg.register(TextPreviewProvider())    # priority 10
    reg.register(MarkdownPreviewProvider())  # priority 5
    assert isinstance(reg.find(Path("README.md")), MarkdownPreviewProvider)


def test_image_wins_over_all():
    reg = PreviewRegistry()
    reg.register(TextPreviewProvider())
    reg.register(MarkdownPreviewProvider())
    reg.register(ImagePreviewProvider())   # priority 0
    assert isinstance(reg.find(Path("photo.png")), ImagePreviewProvider)


def test_fallback_for_unknown():
    reg = PreviewRegistry()
    reg.register(ImagePreviewProvider())
    result = reg.find(Path("archive.7z"))
    assert isinstance(result, FallbackProvider)


def test_empty_registry_returns_fallback():
    reg = PreviewRegistry()
    result = reg.find(Path("anything.xyz"))
    assert isinstance(result, FallbackProvider)


def test_priority_order_maintained():
    reg = PreviewRegistry()
    reg.register(FallbackProvider())       # priority 999
    reg.register(ImagePreviewProvider())   # priority 0
    reg.register(MarkdownPreviewProvider())  # priority 5
    reg.register(TextPreviewProvider())    # priority 10
    # Providers sorted by priority
    priorities = [p.priority for p in reg._providers]
    assert priorities == sorted(priorities)


# ── Item-7 regression: git blame/log must NOT live in registry ───────────────

def test_git_blame_not_in_auto_mode(tmp_path):
    """Registry without blame returns code provider for .py in git repo."""
    (tmp_path / ".git").mkdir()
    f = tmp_path / "script.py"
    f.write_text("x = 1\n")

    from biome_fm.preview.providers.code import CodePreviewProvider
    reg = PreviewRegistry()
    reg.register(CodePreviewProvider())
    assert isinstance(reg.find(f), CodePreviewProvider)


def test_git_log_not_in_auto_mode(tmp_path):
    """Registry without log returns text provider for .txt in git repo."""
    (tmp_path / ".git").mkdir()
    f = tmp_path / "readme.txt"
    f.write_text("hello\n")

    reg = PreviewRegistry()
    reg.register(TextPreviewProvider())
    assert isinstance(reg.find(f), TextPreviewProvider)


def test_bug_reproduced_when_registered(tmp_path):
    """Documents the bug: blame intercepts all files when registered at priority=2."""
    (tmp_path / ".git").mkdir()
    f = tmp_path / "script.py"
    f.write_text("x = 1\n")

    from biome_fm.preview.providers.code import CodePreviewProvider
    from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
    reg = PreviewRegistry()
    reg.register(CodePreviewProvider())
    reg.register(GitBlamePreviewProvider())  # registering = the bug
    # blame (priority=2) beats code (priority=8) for any file in a git repo
    assert isinstance(reg.find(f), GitBlamePreviewProvider)
