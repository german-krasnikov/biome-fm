"""Attribute predicate parsing for advanced filtering (F415)."""
from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

_SIZE_RE = re.compile(r'^([<>]?)(\d+(?:\.\d+)?)([kmg]?)$', re.I)
_UNITS = {'k': 1024, 'm': 1024 ** 2, 'g': 1024 ** 3}
_MOD_PERIODS = {'today': 86400, 'week': 604800, 'month': 2592000}


@dataclass
class FilterSpec:
    name: str = ""
    ext: str = ""
    size_op: str = ""
    size_bytes: int = 0
    mod_period: str = ""


def parse_filter(text: str) -> FilterSpec:
    """Parse 'size:>10m mod:today ext:py foo' into FilterSpec."""
    spec = FilterSpec()
    name_parts: list[str] = []
    for token in text.split():
        if ':' in token:
            key, _, val = token.partition(':')
            key = key.lower()
            if key == 'size':
                m = _SIZE_RE.match(val)
                if m:
                    op, num, unit = m.groups()
                    spec.size_op = op or '>'
                    spec.size_bytes = int(float(num) * _UNITS.get(unit.lower(), 1))
            elif key == 'mod' and val.lower() in _MOD_PERIODS:
                spec.mod_period = val.lower()
            elif key == 'ext':
                spec.ext = val.lower().lstrip('.')
        else:
            name_parts.append(token)
    spec.name = ' '.join(name_parts)
    return spec


def filter_accepts(spec: FilterSpec, name: str, size: int, modified: float, is_dir: bool) -> bool:
    """Pure predicate — no Qt, no FileItem import needed."""
    if spec.ext and Path(name).suffix.lower().lstrip('.') != spec.ext:
        return False
    if spec.size_op and not is_dir:
        if spec.size_op == '>' and size <= spec.size_bytes:
            return False
        if spec.size_op == '<' and size >= spec.size_bytes:
            return False
    if spec.mod_period:
        max_age = _MOD_PERIODS.get(spec.mod_period, 0)
        if max_age and (time.time() - modified) > max_age:
            return False
    if spec.name and spec.name.lower() not in name.lower():
        return False
    return True
