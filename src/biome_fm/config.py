"""Application configuration — TOML persistence."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path


@dataclass
class Config:
    theme: str = "dark"
    splitter_sizes: list[int] = field(default_factory=lambda: [600, 600])
    window_geometry: str = ""
    recent_dirs: list[str] = field(default_factory=list)
    ai_default_provider: str = "claude"
    ai_claude_key: str = ""
    ai_claude_model: str = "claude-sonnet-4-20250514"
    ai_openai_key: str = ""
    ai_openai_model: str = "gpt-4o"
    ai_ollama_url: str = "http://localhost:11434"
    ai_ollama_model: str = "llama3.2"
    ai_cli_claude_code_model: str = ""
    ai_cli_codex_model: str = ""
    ai_cli_opencode_model: str = ""
    sync_browsing: bool = False
    file_type_colors: bool = True
    show_hidden: bool = False
    glass: bool = False
    glass_opacity: int = 47


def load_config(path: Path) -> Config:
    """Load config from TOML file. Missing file → defaults."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, tomllib.TOMLDecodeError):
        return Config()
    # Migrate legacy ai_api_key → ai_claude_key
    if data.get("ai_api_key") and not data.get("ai_claude_key"):
        data["ai_claude_key"] = data["ai_api_key"]
    valid = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in valid})


def save_config(cfg: Config, path: Path) -> None:
    """Save config as TOML. Creates parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for f in fields(Config):
        val = getattr(cfg, f.name)
        if isinstance(val, bool):
            lines.append(f"{f.name} = {'true' if val else 'false'}")
        elif isinstance(val, str):
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
