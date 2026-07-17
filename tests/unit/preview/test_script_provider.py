"""Tests for ScriptPreviewProvider — no Qt."""
from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from biome_fm.preview.provider import ContentKind, PreviewRequest
from biome_fm.preview.providers.script import ScriptPreviewProvider, ScriptSpec, load_script_providers


def test_load_from_toml(tmp_path):
    cfg = tmp_path / "foo.toml"
    cfg.write_text('extensions = [".foo", ".bar"]\ncommand = ["echo", "%f"]\npriority = 42\n')
    providers = load_script_providers(tmp_path)
    assert len(providers) == 1
    p = providers[0]
    assert p.priority == 42
    assert p.can_handle(Path("x.foo"))
    assert p.can_handle(Path("y.bar"))
    assert not p.can_handle(Path("z.txt"))


def test_can_handle_ext():
    spec = ScriptSpec(extensions=frozenset({".xyz"}), command=["cat", "%f"])
    p = ScriptPreviewProvider(spec)
    assert p.can_handle(Path("a.xyz"))
    assert not p.can_handle(Path("a.txt"))


def test_render_runs_command(tmp_path):
    f = tmp_path / "test.foo"
    f.write_text("hello")
    spec = ScriptSpec(extensions=frozenset({".foo"}), command=["cat", "%f"])
    p = ScriptPreviewProvider(spec)
    result = p.render(PreviewRequest(path=f))
    assert result.kind == ContentKind.TEXT
    assert "hello" in result.data  # type: ignore[operator]


def test_timeout_returns_error(tmp_path, monkeypatch):
    f = tmp_path / "test.foo"
    f.write_text("")

    def _timeout(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="sleep", timeout=5)

    monkeypatch.setattr(subprocess, "run", _timeout)
    spec = ScriptSpec(extensions=frozenset({".foo"}), command=["sleep", "99"])
    p = ScriptPreviewProvider(spec)
    result = p.render(PreviewRequest(path=f))
    assert result.kind == ContentKind.ERROR
    assert "timed out" in result.data.lower()  # type: ignore[union-attr]


def test_load_empty_dir(tmp_path):
    assert load_script_providers(tmp_path) == []


def test_load_nonexistent_dir(tmp_path):
    assert load_script_providers(tmp_path / "nonexistent") == []
