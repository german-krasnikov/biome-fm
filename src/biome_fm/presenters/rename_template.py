"""TC-style multi-rename template token expander."""
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path


def expand_template(template: str, path: Path, index: int, counter_start: int = 1) -> str:
    """Expand TC-style tokens: [N] name, [E] ext, [C] counter, [C:n] offset counter, [YMD] mtime."""
    mtime = datetime.fromtimestamp(path.stat().st_mtime)

    def _counter(m: re.Match) -> str:
        start = int(m.group(1)) if m.group(1) else counter_start
        return str(start + index).zfill(3)

    result = template
    result = result.replace("[N]", path.stem)
    result = result.replace("[E]", path.suffix.lstrip("."))
    result = re.sub(r"\[C(?::(\d+))?\]", _counter, result)
    result = result.replace("[YMD]", mtime.strftime("%Y-%m-%d"))
    return result
