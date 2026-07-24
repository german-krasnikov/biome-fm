"""TDD: Preview providers dark-mode (Item #57)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.plugins.types import _DARK_FALLBACK
from biome_fm.preview.provider import ContentKind, PreviewMode, PreviewRequest, PreviewResult


# ── Scenario 5 — PreviewRequest default tokens ───────────────────────────────

def test_preview_request_default_tokens():
    req = PreviewRequest(path=Path("/x"))
    assert req.tokens["base"] == _DARK_FALLBACK["base"]
    assert req.dark is True


# ── Scenario 1 — CsvTableProvider uses theme tokens ──────────────────────────

def test_csv_uses_theme_tokens(tmp_path):
    from biome_fm.preview.providers.csv_preview import CsvTableProvider
    p = tmp_path / "a.csv"
    p.write_text("name,age\nAlice,30\n", encoding="utf-8")
    light = {**_DARK_FALLBACK, "surface": "#ffffff", "base": "#f2f2f7",
             "border": "#c6c6c8", "surface2": "#e5e5ea", "text": "#1c1c1e"}
    req = PreviewRequest(path=p, dark=False, tokens=light)
    result = CsvTableProvider().render(req)
    assert result.kind == ContentKind.HTML
    assert "#ffffff" in result.data        # light surface present
    assert "#2a2a2a" not in result.data    # old hardcoded dark color gone


# ── Scenario 2 — NotebookProvider accent from tokens ─────────────────────────

def test_notebook_accent_from_tokens(tmp_path):
    from biome_fm.preview.providers.notebook import NotebookProvider
    nb = {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": [
        {"cell_type": "markdown", "source": ["# hello"]}
    ]}
    p = tmp_path / "nb.ipynb"
    p.write_text(json.dumps(nb), encoding="utf-8")
    tokens = {**_DARK_FALLBACK, "accent": "#ff0000"}
    req = PreviewRequest(path=p, dark=True, tokens=tokens)
    result = NotebookProvider().render(req)
    assert result.kind == ContentKind.HTML
    assert "#ff0000" in result.data        # custom accent in .markdown border
    assert "#89b4fa" not in result.data    # Catppuccin accent gone


# ── Scenario 3 — GitDiffPreviewProvider picks correct Pygments style ─────────

def test_git_diff_light_style():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    html = GitDiffPreviewProvider._to_html("- old\n+ new\n", dark=False)
    assert "272822" not in html            # monokai bg absent


def test_git_diff_dark_style():
    from biome_fm.preview.providers.git_diff import GitDiffPreviewProvider
    html = GitDiffPreviewProvider._to_html("- old\n+ new\n", dark=True)
    assert "272822" in html                # monokai bg present


# ── GitLogPreviewProvider same pattern ───────────────────────────────────────

def test_git_log_light_style():
    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    html = GitLogPreviewProvider._to_html("abc123 some commit", dark=False)
    assert "272822" not in html


def test_git_log_dark_style():
    from biome_fm.preview.providers.git_log import GitLogPreviewProvider
    html = GitLogPreviewProvider._to_html("abc123 some commit", dark=True)
    assert "272822" in html


# ── GitBlamePreviewProvider uses tokens ──────────────────────────────────────

def test_git_blame_uses_tokens():
    from biome_fm.preview.providers.git_blame import GitBlamePreviewProvider
    blame = (
        "abc1234567890123456789012345678901234567890 1 1 1\n"
        "author Alice\n"
        "\tsome code\n"
    )
    tokens = {**_DARK_FALLBACK, "text_dim": "#ff0000", "text": "#00ff00"}
    html = GitBlamePreviewProvider._parse_to_html(blame, tokens)
    assert "#ff0000" in html   # text_dim for commit hash
    assert "#888" not in html  # old hardcoded color gone


# ── Scenario 4 — set_tokens clears cache ─────────────────────────────────────

def test_set_tokens_clears_cache(tmp_path):
    from biome_fm.preview.presenter import PreviewPresenter
    from biome_fm.preview.registry import PreviewRegistry

    class FakeView:
        def show_result(self, r): pass
        def set_busy(self, b): pass
        def set_visible(self, v): pass
        def is_panel_visible(self): return False
        def scroll_to_bottom(self): pass

    presenter = PreviewPresenter(FakeView(), PreviewRegistry())
    key = (tmp_path / "x.csv", 0.0, True, PreviewMode.AUTO)
    presenter._cache[key] = (PreviewResult(ContentKind.TEXT, "old"), 0.0)
    presenter.set_tokens({**_DARK_FALLBACK, "surface": "#ff0000"})
    assert len(presenter._cache) == 0
