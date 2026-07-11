"""Application configuration — TOML persistence."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class Config:
    theme: str = "dark"
    left_path: str = ""
    right_path: str = ""
    splitter_sizes: list[int] = field(default_factory=lambda: [600, 600])
    window_geometry: str = ""
    recent_dirs: list[str] = field(default_factory=list)
    ai_api_key: str = ""


def load_config(path: Path) -> Config:
    """Load config from TOML file. Missing file → defaults."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return Config()
    valid = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in valid})


def save_config(cfg: Config, path: Path) -> None:
    """Save config as TOML. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for f in fields(Config):
        val = getattr(cfg, f.name)
        if isinstance(val, str):
            escaped = val.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{f.name} = "{escaped}"')
        elif isinstance(val, list):
            if val and isinstance(val[0], int):
                lines.append(f"{f.name} = [{', '.join(str(v) for v in val)}]")
            else:
                items = ", ".join(f'"{v}"' for v in val)
                lines.append(f"{f.name} = [{items}]")
        else:
            lines.append(f"{f.name} = {val}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
