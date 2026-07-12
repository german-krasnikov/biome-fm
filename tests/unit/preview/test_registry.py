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
