"""TOML-based theme system — importlib.resources, QPalette sync."""
from __future__ import annotations

import importlib.resources
import tomllib
from pathlib import Path
from string import Template

from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from biome_fm.plugins.types import ThemeTokens

# Inline dark fallback — safety net if TOML files missing from install
_DARK_FALLBACK: ThemeTokens = {
    "base":     "#1c1c1e",
    "surface":  "#2c2c2e",
    "surface2": "#3a3a3c",
    "border":   "#48484a",
    "text":     "#f5f5f7",
    "text_dim": "#98989f",
    "accent":   "#0a84ff",
    "accent2":  "#5e5ce6",
    "red":      "#ff453a",
    "green":    "#32d74b",
}

# Backward-compat alias (existing tests import _TOKENS)
_TOKENS = _DARK_FALLBACK


def _load_qss_template() -> str:
    pkg = importlib.resources.files("biome_fm.themes")
    return (pkg / "_base.qss.tmpl").read_text(encoding="utf-8")


_QSS_TMPL: str = _load_qss_template()
_QSS = Template(_QSS_TMPL)  # backward-compat alias


def _user_themes_dir() -> Path | None:
    """Return user themes directory, or None if Qt/config unavailable."""
    try:
        from biome_fm.qt import QStandardPaths
        loc = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation)
        if loc:
            return Path(loc) / "biome-fm" / "themes"
    except Exception:
        pass
    return None


def _find_theme(name: str) -> str | None:
    """Return TOML content for named theme, or None. User dir takes priority."""
    user_dir = _user_themes_dir()
    if user_dir:
        user_resolved = user_dir.resolve()
        for cand in (user_dir / f"{name}.toml", user_dir / name / "theme.toml"):
            cand = cand.resolve()
            if cand.is_relative_to(user_resolved) and cand.exists():
                return cand.read_text(encoding="utf-8")
    ref = importlib.resources.files("biome_fm.themes").joinpath(f"{name}.toml")
    try:
        return ref.read_text(encoding="utf-8")
    except (FileNotFoundError, TypeError, OSError):
        return None


def load_theme(
    name: str, _seen: frozenset[str] = frozenset(), plugin_manager: object = None
) -> ThemeTokens:
    """Load theme by name. Plugin themes take priority over TOML → _DARK_FALLBACK."""
    # Plugin hook takes priority (if available)
    if plugin_manager is not None:
        plugin_tokens = plugin_manager.hook.provide_theme(name=name)  # type: ignore[union-attr]
        if plugin_tokens:
            tokens: dict[str, str] = dict(_DARK_FALLBACK)
            tokens.update(plugin_tokens)
            return tokens  # type: ignore[return-value]
    # TOML-based loading with inheritance
    content = _find_theme(name)
    if content is None:
        return dict(_DARK_FALLBACK)  # type: ignore[return-value]
    data = tomllib.loads(content)
    tokens = dict(_DARK_FALLBACK)
    parent = data.get("meta", {}).get("inherits")
    if parent and parent not in _seen:
        tokens = dict(load_theme(parent, _seen | {name}))
    tokens.update(data.get("tokens", {}))
    return tokens  # type: ignore[return-value]


def _apply_palette(app: QApplication, tokens: ThemeTokens) -> None:
    p = QPalette()
    p.setColor(QPalette.ColorRole.Window,         QColor(tokens["base"]))
    p.setColor(QPalette.ColorRole.WindowText,      QColor(tokens["text"]))
    p.setColor(QPalette.ColorRole.Base,            QColor(tokens["surface"]))
    p.setColor(QPalette.ColorRole.AlternateBase,   QColor(tokens["surface2"]))
    p.setColor(QPalette.ColorRole.Text,            QColor(tokens["text"]))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(tokens["text_dim"]))
    p.setColor(QPalette.ColorRole.Button,          QColor(tokens["surface2"]))
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(tokens["text"]))
    p.setColor(QPalette.ColorRole.Highlight,       QColor(tokens["accent"]))
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens["base"]))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor(tokens["surface"]))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor(tokens["text"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
               QColor(tokens["text_dim"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
               QColor(tokens["text_dim"]))
    app.setPalette(p)


def apply_theme(app: QApplication, name: str = "dark", plugin_manager: object = None) -> None:
    tokens = load_theme(name, plugin_manager=plugin_manager)
    _apply_palette(app, tokens)
    app.setStyleSheet(Template(_QSS_TMPL).substitute(tokens))
    from biome_fm.event_bus import ThemeChanged, bus  # lazy — avoids circular import
    bus.publish(ThemeChanged(name=name, tokens=tokens))
