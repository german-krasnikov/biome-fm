import fnmatch
from pathlib import Path


def filter_by_mask(paths: list[Path], mask: str | None) -> list[Path]:
    if not mask:
        return paths
    patterns = [p.strip() for p in mask.split(",") if p.strip()]
    return [p for p in paths if any(fnmatch.fnmatch(p.name.lower(), pat.lower()) for pat in patterns)]
