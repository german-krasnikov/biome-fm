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
    "base_bg":  "#1c1c1e",
    "surface":  "#2c2c2e",
    "surface_opaque":  "#2c2c2e",
    "surface2": "#3a3a3c",
    "surface2_opaque": "#3a3a3c",
    "border":   "#48484a",
    "text":     "#f5f5f7",
    "text_dim": "#98989f",
    "accent":   "#0a84ff",
    "accent2":  "#5e5ce6",
    "red":      "#ff453a",
    "green":    "#32d74b",
    "selection_bg": "#0a84ff",
}

# Backward-compat alias (existing tests import _TOKENS)
_TOKENS = _DARK_FALLBACK

_GLASS_KEYS: frozenset[str] = frozenset({"base", "surface", "surface2"})
_GLASS_ALPHA = 120  # ~47% opacity — enough to see blur through
_GLASS_SELECTION_ALPHA = 140  # selection slightly more opaque for readability


def _hex_to_rgba(hex_color: str, alpha: int) -> str:
    if not hex_color.startswith("#"):
        return hex_color
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _apply_glass_alpha(tokens: dict) -> dict:
    result = dict(tokens)
    result["base_bg"] = "transparent"
    for key in _GLASS_KEYS - {"base"}:
        if key in result:
            result[key] = _hex_to_rgba(result[key], _GLASS_ALPHA)
    accent = tokens.get("accent", _DARK_FALLBACK["accent"])
    result["selection_bg"] = _hex_to_rgba(accent, _GLASS_SELECTION_ALPHA)
    return result


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
            tokens.setdefault("base_bg", tokens["base"])
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
    tokens.setdefault("base_bg", tokens.get("base", _DARK_FALLBACK["base"]))
    tokens.setdefault("selection_bg", tokens.get("accent", _DARK_FALLBACK["accent"]))
    return tokens  # type: ignore[return-value]


def _apply_palette(app: QApplication, tokens: ThemeTokens, glass: bool = False) -> None:
    p = QPalette()
    window_color = QColor(0, 0, 0, 0) if glass else QColor(tokens["base"])
    p.setColor(QPalette.ColorRole.Window,         window_color)
    p.setColor(QPalette.ColorRole.WindowText,      QColor(tokens["text"]))
    base_color = QColor(tokens["surface"])
    alt_color = QColor(tokens["surface2"])
    if glass:
        base_color.setAlpha(_GLASS_ALPHA)
        alt_color.setAlpha(_GLASS_ALPHA)
    p.setColor(QPalette.ColorRole.Base,            base_color)
    p.setColor(QPalette.ColorRole.AlternateBase,   alt_color)
    p.setColor(QPalette.ColorRole.Text,            QColor(tokens["text"]))
    p.setColor(QPalette.ColorRole.PlaceholderText, QColor(tokens["text_dim"]))
    btn_color = QColor(tokens["surface2"])
    highlight_color = QColor(tokens["accent"])
    if glass:
        btn_color.setAlpha(_GLASS_ALPHA)
        highlight_color.setAlpha(_GLASS_SELECTION_ALPHA)
    p.setColor(QPalette.ColorRole.Button,          btn_color)
    p.setColor(QPalette.ColorRole.ButtonText,      QColor(tokens["text"]))
    p.setColor(QPalette.ColorRole.Highlight,       highlight_color)
    p.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens["base"]))
    p.setColor(QPalette.ColorRole.ToolTipBase,     QColor(tokens["surface"]))
    p.setColor(QPalette.ColorRole.ToolTipText,     QColor(tokens["text"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text,
               QColor(tokens["text_dim"]))
    p.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText,
               QColor(tokens["text_dim"]))
    app.setPalette(p)


def apply_theme(
    app: QApplication,
    name: str = "dark",
    plugin_manager: object = None,
    glass: bool = False,
) -> None:
    tokens = load_theme(name, plugin_manager=plugin_manager)
    _apply_palette(app, tokens, glass=glass)
    qss_tokens = _apply_glass_alpha(tokens) if glass else tokens
    app.setStyleSheet(Template(_QSS_TMPL).substitute(qss_tokens))
    from biome_fm.event_bus import ThemeChanged, bus  # lazy — avoids circular import
    bus.publish(ThemeChanged(name=name, tokens=tokens))
