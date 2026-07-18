"""Collapsible tree preview for JSON, XML, YAML, TOML."""
from __future__ import annotations

import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult

_MAX_BYTES = 512 * 1024
_MAX_DEPTH = 30
_EXTS = {".json", ".xml", ".yaml", ".yml", ".toml"}


def _v(val: object, depth: int = 0) -> str:
    if depth >= _MAX_DEPTH:
        return "<span>…</span>"
    e = html.escape
    if isinstance(val, dict):
        if not val:
            return "<span>{}</span>"
        rows = "".join(
            f"<details><summary>{e(str(k))}</summary>{_v(v, depth + 1)}</details>"
            for k, v in val.items()
        )
        return f"<div>{rows}</div>"
    if isinstance(val, list):
        if not val:
            return "<span>[]</span>"
        rows = "".join(
            f"<details><summary>[{i}]</summary>{_v(v, depth + 1)}</details>"
            for i, v in enumerate(val)
        )
        return f"<div>{rows}</div>"
    return f"<span>{e(str(val))}</span>"


def _xml(el: ET.Element, depth: int = 0) -> str:
    if depth >= _MAX_DEPTH:
        return "<span>…</span>"
    e = html.escape
    tag = e(el.tag)
    children = list(el)
    text = (el.text or "").strip()
    inner = "".join(
        f"<details><summary>@{e(k)}</summary><span>{e(v)}</span></details>"
        for k, v in el.attrib.items()
    )
    if text:
        inner += f"<span>{e(text)}</span>"
    inner += "".join(_xml(c, depth + 1) for c in children)
    if not inner:
        return f"<span>&lt;{tag}/&gt;</span>"
    return f"<details><summary>&lt;{tag}&gt;</summary><div>{inner}</div></details>"


def _wrap(body: str, title: str) -> PreviewResult:
    css = "body{font-family:monospace;font-size:13px}details{margin-left:1em}"
    data = f"<html><head><style>{css}</style></head><body>{body}</body></html>"
    return PreviewResult(kind=ContentKind.HTML, data=data, title=title)


class JsonTreeProvider:
    priority = 5

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in _EXTS

    def render(self, req: PreviewRequest) -> PreviewResult:
        try:
            raw = req.path.read_bytes()
        except OSError as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        if len(raw) > _MAX_BYTES:
            return PreviewResult(kind=ContentKind.ERROR, data="File too large (>512KB)")

        ext = req.path.suffix.lower()
        name = req.path.name

        try:
            if ext == ".json":
                data = json.loads(raw)
                return _wrap(_v(data), name)

            if ext == ".xml":
                root = ET.fromstring(raw.decode())
                return _wrap(_xml(root), name)

            if ext in (".yaml", ".yml"):
                try:
                    import yaml  # type: ignore[import-untyped]
                    data = yaml.safe_load(raw)
                    return _wrap(_v(data), name)
                except ImportError:
                    text = raw.decode(errors="replace")
                    return PreviewResult(kind=ContentKind.TEXT, data=text, title=name)

            if ext == ".toml":
                try:
                    import tomllib
                except ImportError:
                    try:
                        import tomli as tomllib  # type: ignore[import-untyped,no-redef]
                    except ImportError:
                        text = raw.decode(errors="replace")
                        return PreviewResult(kind=ContentKind.TEXT, data=text, title=name)
                data = tomllib.loads(raw.decode())
                return _wrap(_v(data), name)

        except Exception as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))

        return PreviewResult(kind=ContentKind.ERROR, data="Unsupported format")
