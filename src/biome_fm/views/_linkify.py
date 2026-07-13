"""Pure-Python path linkify helpers for ChatLog (no Qt)."""
from __future__ import annotations

import re

# Matches absolute (/path), home (~/path), relative paths with 2+ slashes.
# Relative requires 2+ segments to avoid false positives like and/or, I/O.
_PATH_RE = re.compile(
    r'(?<![\w="\'/.:])(/[\w./\-]+|~/[\w./\-]+|[a-zA-Z][\w.\-]*/[\w.\-]+/[\w./\-]+)'
)

_TAG_RE = re.compile(r"<[^>]+>")
_SKIP_TAGS = frozenset({"code", "pre", "a"})


def _linkify_html(fragment: str) -> str:
    """Wrap filesystem paths in biome: links; skip paths inside code/pre/a tags."""
    result: list[str] = []
    pos = 0
    depth: dict[str, int] = {t: 0 for t in _SKIP_TAGS}

    for m in _TAG_RE.finditer(fragment):
        if pos < m.start():
            text = fragment[pos : m.start()]
            if any(depth[k] > 0 for k in depth):
                result.append(text)
            else:
                result.append(
                    _PATH_RE.sub(
                        lambda p: f'<a href="biome:{p.group(0)}">{p.group(0)}</a>', text
                    )
                )

        tag = m.group(0)
        name_m = re.match(r"</?(\w+)", tag)
        if name_m:
            name = name_m.group(1).lower()
            if name in depth:
                if tag.startswith("</"):
                    depth[name] = max(0, depth[name] - 1)
                else:
                    depth[name] += 1
        result.append(tag)
        pos = m.end()

    text = fragment[pos:]
    if any(depth[k] > 0 for k in depth):
        result.append(text)
    else:
        result.append(
            _PATH_RE.sub(
                lambda p: f'<a href="biome:{p.group(0)}">{p.group(0)}</a>', text
            )
        )
    return "".join(result)
