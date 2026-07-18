from pathlib import Path


def suggest_destination(
    file_path: Path,
    frecency: list[tuple[Path, int]],
    current_dir: Path | None = None,
) -> Path | None:
    ext = file_path.suffix.lower()
    for dir_path, _ in sorted(frecency, key=lambda x: -x[1]):
        if current_dir and dir_path == current_dir:
            continue
        try:
            if any(f.suffix.lower() == ext for f in dir_path.iterdir() if f.is_file()):
                return dir_path
        except (OSError, PermissionError):
            continue
    return None
