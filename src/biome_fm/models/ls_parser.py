"""Parse `ls -la --time-style=long-iso` output — shared by docker_vfs and fish_vfs."""
from __future__ import annotations

import re
from datetime import datetime

_LS_RE = re.compile(
    r'^([dl\-][rwx\-]{9})\s+\d+\s+\S+\s+\S+\s+(\d+)\s+'
    r'(\d{4}-\d{2}-\d{2})\s+(\d{2}:\d{2})\s+(.+)$'
)


def parse_ls_line(line: str) -> dict | None:
    """Parse one ls -la --time-style=long-iso line. Returns None if no match."""
    m = _LS_RE.match(line)
    if not m:
        return None
    mode_str, size, date, time_, name = m.groups()
    mtime = datetime.strptime(f"{date} {time_}", "%Y-%m-%d %H:%M").timestamp()
    return {"name": name.strip(), "is_dir": mode_str[0] == "d",
            "size": int(size), "mtime": mtime}
