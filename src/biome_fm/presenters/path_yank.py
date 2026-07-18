from pathlib import Path


def yank_component(path: Path, key: str) -> str | None:
    match key:
        case "n": return path.name
        case "p": return str(path)
        case "d": return str(path.parent)
        case "e": return path.suffix
        case _: return None
