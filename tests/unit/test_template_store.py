"""Tests for TemplateStore."""
from __future__ import annotations

from biome_fm.models.template_store import FileTemplate, TemplateStore


def test_builtin_templates() -> None:
    store = TemplateStore()
    templates = store.all_templates()
    assert len(templates) >= 3
    names = [t.name for t in templates]
    assert "Python Script" in names
    assert "Markdown" in names
    assert "Text File" in names


def test_template_has_ext() -> None:
    store = TemplateStore()
    py = next(t for t in store.all_templates() if t.name == "Python Script")
    assert py.ext == ".py"


def test_template_is_dataclass() -> None:
    t = FileTemplate(name="X", ext=".x", content=b"abc")
    assert t.content == b"abc"
