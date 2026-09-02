"""Application configuration — TOML persistence."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field, fields
from pathlib import Path

from biome_fm.models._store_base import toml_escape as _toml_esc
from biome_fm.utils.atomic_write import atomic_write


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
    serial_ops: bool = False
    ui_font_size: int = 0  # 0 = system default
    reduce_motion: bool = False
    high_contrast: bool = False
    global_hotkey: str = ""  # F321 — e.g. "<ctrl>+<alt>+b"
    toolbar_actions: list[str] = field(default_factory=list)
    toolbar_visible: bool = False

    def __post_init__(self) -> None:
        try:
            self.glass_opacity = max(0, min(100, int(self.glass_opacity)))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            self.glass_opacity = 47

        try:
            self.ui_font_size = max(0, min(72, int(self.ui_font_size)))  # type: ignore[arg-type]
        except (TypeError, ValueError):
            self.ui_font_size = 0

        if not isinstance(self.theme, str):
            self.theme = "dark"

        if not isinstance(self.splitter_sizes, list) or len(self.splitter_sizes) != 2:
            self.splitter_sizes = [600, 600]
        else:
            try:
                self.splitter_sizes = [max(1, int(v)) for v in self.splitter_sizes]
            except (TypeError, ValueError):
                self.splitter_sizes = [600, 600]

        for attr in ("recent_dirs", "highlight_rules", "hidden_columns", "toolbar_actions", "search_history"):
            if not isinstance(getattr(self, attr), list):
                setattr(self, attr, [])

        if not isinstance(self.layout_profiles, dict):
            self.layout_profiles = {}

        for attr in ("editor_cmd", "global_hotkey", "window_geometry", "ai_default_provider",
                     "ai_claude_key", "ai_claude_model", "ai_openai_key", "ai_openai_model",
                     "ai_ollama_url", "ai_ollama_model"):
            if not isinstance(getattr(self, attr), str):
                setattr(self, attr, "")

    def save_layout(self, name: str, data: dict) -> None:
        self.layout_profiles[name] = data

    def load_layout(self, name: str) -> dict | None:
        return self.layout_profiles.get(name)


_AI_KEY_ACCOUNTS = {"ai_claude_key": "claude", "ai_openai_key": "openai"}


def migrate_keys_to_keyring(cfg: Config, path: Path) -> Config:
    """One-time migration: move plaintext keys from config into keyring, then clear."""
    from biome_fm.models.credential_store import CRED_SERVICE, get_credential, set_credential
    changed = False
    for field_name, account in _AI_KEY_ACCOUNTS.items():
        plaintext = getattr(cfg, field_name)
        if plaintext:
            if not get_credential(CRED_SERVICE, account):
                set_credential(CRED_SERVICE, account, plaintext)
            setattr(cfg, field_name, "")
            changed = True
    if changed:
        save_config(cfg, path)
    return cfg


def load_config(path: Path) -> Config:
    """Load config from TOML file. Missing file → defaults."""
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, UnicodeDecodeError, tomllib.TOMLDecodeError):
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
        return '"' + _toml_esc(v) + '"'
    if isinstance(v, dict):
        inner = ", ".join(f'"{_toml_esc(k)}" = {_toml_val(val)}' for k, val in v.items())
        return "{" + inner + "}"
    if isinstance(v, list):
        return "[" + ", ".join(_toml_val(i) for i in v) + "]"
    return str(v)


def save_config(cfg: Config, path: Path) -> None:
    """Save config as TOML. Creates parent dirs if needed."""
    lines = [f"{f.name} = {_toml_val(getattr(cfg, f.name))}" for f in fields(Config)]
    atomic_write(path, "\n".join(lines) + "\n")
