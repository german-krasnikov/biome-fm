"""Background directory size calculation."""
from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# ponytail: 4 workers covers I/O-bound dir walking; raise to 8 if slow on NVMe RAID
# per-future timeout is future work if network mounts cause stalls
_POOL = ThreadPoolExecutor(max_workers=4, thread_name_prefix="dir-size")


def calc_tree_size(paths: list[Path], cancel: list[bool]) -> int:
    """Sum size of all files under paths. cancel[0]=True aborts early. Returns -1 if cancelled."""
    total = 0
    for p in paths:
        if cancel[0]:
            return -1
        if p.is_file():
            try:
                total += p.stat().st_size
            except OSError:
                pass
        elif p.is_dir():
            for root, _dirs, files in os.walk(p):
                if cancel[0]:
                    return -1
                for f in files:
                    try:
                        total += os.stat(os.path.join(root, f)).st_size
                    except OSError:
                        pass
    return total
