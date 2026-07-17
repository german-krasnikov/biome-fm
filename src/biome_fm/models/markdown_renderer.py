"""Backward-compat shim — renderer moved to preview/."""
from biome_fm.preview.markdown_renderer import (  # noqa: F401
    FENCE_RE,
    PRE_RE,
    _css,
    _inject_css,
    render,
)
