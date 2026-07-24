"""Convert terminal output lines to HTML with clickable file links."""
from __future__ import annotations

import html
import re
from pathlib import Path

# Most specific first — Python traceback, then absolute path, then relative
_PY_RE = re.compile(r'File "([^"]+)", line (\d+)')
_PATH_RE = re.compile(r'((?:[A-Za-z]:[\\/]|/)[^\s:]+):(\d+)(?::\d+)?:')
_REL_RE = re.compile(r'^([^\s/:][^\s:]*\.[a-zA-Z0-9]+):(\d+)(?::\d+)?:')


def _href(path: str, line: str, cwd: str) -> str:
    p = Path(path)
    if not p.is_absolute() and cwd:
        p = Path(cwd) / p
    return f"biome-file:///{html.escape(p.as_posix().lstrip('/'))}?line={line}"


def linkify(text: str, cwd: str = "") -> str:
    for pattern in (_PY_RE, _PATH_RE, _REL_RE):
        m = pattern.search(text)
        if m:
            path, line = m.group(1), m.group(2)
            href = _href(path, line, cwd)
            before = html.escape(text[: m.start()])
            label = html.escape(text[m.start() : m.end()])
            after = html.escape(text[m.end() :])
            return f'{before}<a href="{href}">{label}</a>{after}'
    return html.escape(text)
