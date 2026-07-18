"""TC-style multi-rename template token expander."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

_CASE_MODS = frozenset({"upper", "lower", "title"})


def expand_template(template: str, path: Path, index: int, counter_start: int = 1) -> str:
    """Expand TC-style tokens: [N] name, [E] ext, [C] counter, [C:n] offset counter, [YMD] mtime.

    Supports [TOKEN:modifier] where modifier is upper/lower/title.
    """
    mtime = datetime.fromtimestamp(path.stat().st_mtime)
    _tokens: dict[str, str] = {
        "N": path.stem,
        "E": path.suffix.lstrip("."),
        "YMD": mtime.strftime("%Y-%m-%d"),
    }

    def _counter(m: re.Match) -> str:
        start = int(m.group(1)) if m.group(1) else counter_start
        return str(start + index).zfill(3)

    def _mod_expand(m: re.Match) -> str:
        tok, mod = m.group(1), m.group(2)
        val = _tokens.get(tok)
        if val is None or mod not in _CASE_MODS:
            return m.group(0)
        return getattr(val, mod)()

    result = re.sub(r"\[([A-Z]+):([a-z]+)\]", _mod_expand, template)
    result = result.replace("[N]", path.stem)
    result = result.replace("[E]", path.suffix.lstrip("."))
    result = re.sub(r"\[C(?::(\d+))?\]", _counter, result)
    result = result.replace("[YMD]", mtime.strftime("%Y-%m-%d"))
    return result
