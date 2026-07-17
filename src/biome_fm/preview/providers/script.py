"""Pluggable script-based preview providers loaded from TOML files."""
from __future__ import annotations

import subprocess
import tomllib
from dataclasses import dataclass
from pathlib import Path

from biome_fm.preview.provider import ContentKind, PreviewRequest, PreviewResult


@dataclass
class ScriptSpec:
    extensions: frozenset[str]
    command: list[str]
    priority: int = 50


class ScriptPreviewProvider:
    def __init__(self, spec: ScriptSpec) -> None:
        self._spec = spec
        self.priority = spec.priority

    def can_handle(self, path: Path) -> bool:
        return path.suffix.lower() in self._spec.extensions

    def render(self, req: PreviewRequest) -> PreviewResult:
        cmd = [c.replace("%f", str(req.path)) for c in self._spec.command]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            output = proc.stdout or proc.stderr
            return PreviewResult(kind=ContentKind.TEXT, data=output)
        except subprocess.TimeoutExpired:
            return PreviewResult(kind=ContentKind.ERROR, data="Script timed out")
        except Exception as e:
            return PreviewResult(kind=ContentKind.ERROR, data=str(e))


def load_script_providers(scripts_dir: Path) -> list[ScriptPreviewProvider]:
    """Read *.toml from scripts_dir, return one provider per file."""
    if not scripts_dir.is_dir():
        return []
    providers = []
    for toml_file in scripts_dir.glob("*.toml"):
        try:
            data = tomllib.loads(toml_file.read_text(encoding="utf-8"))
            spec = ScriptSpec(
                extensions=frozenset(data.get("extensions", [])),
                command=data.get("command", []),
                priority=data.get("priority", 50),
            )
            providers.append(ScriptPreviewProvider(spec))
        except Exception:
            pass  # skip malformed files
    return providers
