"""Application configuration — TOML persistence."""
from __future__ import annotations

import shutil
import time
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
    show_git_status: bool = True
    auto_preview: bool = True
    highlight_rules: list[dict] = field(default_factory=list)
    hidden_columns: list[str] = field(default_factory=list)
    follow_system_theme: bool = True
    editor_cmd: str = ""
    search_history: list[str] = field(default_factory=list)
    layout_profiles: dict[str, dict] = field(default_factory=dict)

    def save_layout(self, name: str, data: dict) -> None:
        self.layout_profiles[name] = data

    def load_layout(self, name: str) -> dict | None:
        return self.layout_profiles.get(name)


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


def _toml_val(v: object) -> str:
    """Serialize a Python value to a TOML inline value."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, str):
        return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'
    if isinstance(v, dict):
        inner = ", ".join(f"{k} = {_toml_val(val)}" for k, val in v.items())
        return "{" + inner + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_toml_val(i) for i in v) + "]"
    return str(v)


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
            elif val and isinstance(val[0], dict):
                items = ", ".join(
                    "{" + ", ".join(f'{k} = "{v}"' for k, v in d.items()) + "}"
                    for d in val
                )
                lines.append(f"{f.name} = [{items}]")
            else:
                items = ", ".join(f'"{v}"' for v in val)
                lines.append(f"{f.name} = [{items}]")
        elif isinstance(val, dict):
            lines.append(f"{f.name} = {_toml_val(val)}")
        else:
            lines.append(f"{f.name} = {val}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _rotate_config_backup(cfg_path: Path, keep: int = 7) -> None:
    """Copy cfg_path to a timestamped .bak file, keeping at most `keep` backups."""
    if not cfg_path.exists():
        return
    backups = sorted(cfg_path.parent.glob(f"{cfg_path.stem}.bak.*"))
    # delete oldest first to stay under the cap after the new backup is added
    for old in backups[: max(0, len(backups) - keep + 1)]:
        old.unlink()
    shutil.copy2(cfg_path, cfg_path.parent / f"{cfg_path.stem}.bak.{int(time.time())}")
