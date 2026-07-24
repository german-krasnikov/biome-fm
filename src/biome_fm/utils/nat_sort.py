"""Natural-sort key — Qt-free, shared by directory_model and pane_presenter."""
import re
from biome_fm.utils.encoding import normalize_filename


def nat_key(name: str) -> list:
    """Split on digit runs; NFC-normalised, case-insensitive. IMG_2 < IMG_10."""
    parts = re.split(r"(\d+)", normalize_filename(name).lower())
    return [int(p) if p.isdigit() else p for p in parts]
