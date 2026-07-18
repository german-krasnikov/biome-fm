"""Unit tests for NotebookProvider."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.notebook import NotebookProvider


@pytest.fixture
def provider():
    return NotebookProvider()


def _nb(cells: list[dict]) -> dict:
    return {"nbformat": 4, "nbformat_minor": 5, "metadata": {}, "cells": cells}


def _code(source: str | list[str], outputs=None) -> dict:
    return {
        "cell_type": "code",
        "source": source if isinstance(source, list) else [source],
        "outputs": outputs or [],
    }


def _markdown(source: str | list[str]) -> dict:
    return {
        "cell_type": "markdown",
        "source": source if isinstance(source, list) else [source],
    }


def _stream_output(text: str) -> dict:
    return {"output_type": "stream", "text": [text]}


def test_can_handle_ipynb(provider, tmp_path):
    assert provider.can_handle(tmp_path / "notebook.ipynb") is True


def test_cannot_handle_py(provider, tmp_path):
    assert provider.can_handle(tmp_path / "script.py") is False


def test_code_cells_rendered(provider, tmp_path):
    nb_file = tmp_path / "nb.ipynb"
    nb_file.write_text(json.dumps(_nb([_code("x = 1\nprint(x)")])))
    result = provider.render(PreviewRequest(path=nb_file))
    assert result.kind == ContentKind.HTML
    assert "<pre" in result.data
    assert "x = 1" in result.data


def test_markdown_cells_rendered(provider, tmp_path):
    nb_file = tmp_path / "nb.ipynb"
    nb_file.write_text(json.dumps(_nb([_markdown("# Hello\nworld")])))
    result = provider.render(PreviewRequest(path=nb_file))
    assert result.kind == ContentKind.HTML
    assert "Hello" in result.data
    assert "world" in result.data


def test_output_cells_shown(provider, tmp_path):
    nb_file = tmp_path / "nb.ipynb"
    nb_file.write_text(
        json.dumps(_nb([_code("print('hi')", [_stream_output("hi\n")])]))
    )
    result = provider.render(PreviewRequest(path=nb_file))
    assert result.kind == ContentKind.HTML
    assert "hi" in result.data


def test_invalid_notebook_shows_error(provider, tmp_path):
    nb_file = tmp_path / "nb.ipynb"
    nb_file.write_text("not json {{{")
    result = provider.render(PreviewRequest(path=nb_file))
    assert result.kind == ContentKind.ERROR


def test_empty_cells_skipped(provider, tmp_path):
    nb_file = tmp_path / "nb.ipynb"
    nb_file.write_text(json.dumps(_nb([_code(""), _code("x = 1")])))
    result = provider.render(PreviewRequest(path=nb_file))
    assert result.kind == ContentKind.HTML
    assert "x = 1" in result.data


def test_size_limit(provider, tmp_path):
    nb_file = tmp_path / "huge.ipynb"
    nb_file.write_bytes(b"x" * (4 * 1024 * 1024 + 1))
    result = provider.render(PreviewRequest(path=nb_file))
    assert result.kind == ContentKind.ERROR
