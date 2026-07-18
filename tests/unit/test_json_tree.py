"""Tests for JsonTreeProvider — TDD RED phase."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest


@pytest.fixture
def provider():
    from biome_fm.preview.providers.json_tree import JsonTreeProvider
    return JsonTreeProvider()


def _req(path: Path) -> PreviewRequest:
    return PreviewRequest(path=path, dark=True)


# --- can_handle ---

def test_can_handle_json(provider, tmp_path):
    assert provider.can_handle(tmp_path / "data.json") is True


def test_can_handle_xml(provider, tmp_path):
    assert provider.can_handle(tmp_path / "data.xml") is True


def test_can_handle_yaml(provider, tmp_path):
    assert provider.can_handle(tmp_path / "data.yaml") is True
    assert provider.can_handle(tmp_path / "data.yml") is True


def test_can_handle_toml(provider, tmp_path):
    assert provider.can_handle(tmp_path / "data.toml") is True


def test_cannot_handle_txt(provider, tmp_path):
    assert provider.can_handle(tmp_path / "file.txt") is False


# --- render JSON ---

def test_render_valid_json(provider, tmp_path):
    f = tmp_path / "data.json"
    f.write_text(json.dumps({"a": 1, "b": [2, 3]}))
    result = provider.render(_req(f))
    assert result.kind == ContentKind.HTML
    assert "<details>" in result.data
    assert "<summary>" in result.data


def test_invalid_json_shows_error(provider, tmp_path):
    f = tmp_path / "bad.json"
    f.write_text("{not valid json")
    result = provider.render(_req(f))
    assert result.kind == ContentKind.ERROR


def test_size_capped(provider, tmp_path):
    f = tmp_path / "big.json"
    f.write_bytes(b"x" * (512 * 1024 + 1))
    result = provider.render(_req(f))
    assert result.kind == ContentKind.ERROR


def test_nested_depth_rendered(provider, tmp_path):
    nested = {"outer": {"inner": {"deep": 42}}}
    f = tmp_path / "nested.json"
    f.write_text(json.dumps(nested))
    result = provider.render(_req(f))
    assert result.kind == ContentKind.HTML
    assert "outer" in result.data
    assert "inner" in result.data
    assert "deep" in result.data


# --- render XML ---

def test_render_valid_xml(provider, tmp_path):
    f = tmp_path / "data.xml"
    f.write_text("<root><child attr='x'>hello</child></root>")
    result = provider.render(_req(f))
    assert result.kind == ContentKind.HTML
    assert "root" in result.data
    assert "child" in result.data


def test_invalid_xml_shows_error(provider, tmp_path):
    f = tmp_path / "bad.xml"
    f.write_text("<unclosed>")
    result = provider.render(_req(f))
    assert result.kind == ContentKind.ERROR


# --- render TOML ---

def test_render_valid_toml(provider, tmp_path):
    f = tmp_path / "data.toml"
    f.write_text("[section]\nkey = 'value'\n")
    result = provider.render(_req(f))
    # Either HTML or fallback TEXT — not ERROR
    assert result.kind in (ContentKind.HTML, ContentKind.TEXT)


# --- priority ---

def test_priority(provider):
    assert provider.priority == 5
