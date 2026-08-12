#!/usr/bin/env python3
"""Sync version from pyproject.toml (canonical) to src/biome_fm/__init__.py.

Usage:
    python scripts/sync_versions.py 0.35.0   # bump canonical + sync copies
    python scripts/sync_versions.py --sync   # sync __init__.py from pyproject.toml
    python scripts/sync_versions.py --check  # verify without writing (CI)
"""
import os
import re
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")

ROOT = Path(__file__).parents[1]
PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src" / "biome_fm" / "__init__.py"


# ---------------------------------------------------------------------------
# Readers
# ---------------------------------------------------------------------------


def _read_pyproject_version(path: Path) -> str:
    m = re.search(r'^version = "([^"]*)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        print(f"version field not found in {path}", file=sys.stderr)
        sys.exit(1)
    return m.group(1)


def _read_init_version(path: Path) -> str:
    m = re.search(r'^__version__ = "([^"]*)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    return m.group(1) if m else "?"


# ---------------------------------------------------------------------------
# Updaters — pure functions: Path, version → new file content (str)
# ---------------------------------------------------------------------------


def _update_pyproject(path: Path, version: str) -> str:
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'^version = "[^"]*"', f'version = "{version}"', text, count=1, flags=re.MULTILINE
    )
    if n == 0:
        raise ValueError(f"version pattern not found in {path}")
    return new_text


def _update_init(path: Path, version: str) -> str:
    text = path.read_text(encoding="utf-8")
    new_text, n = re.subn(
        r'^__version__ = "[^"]*"',
        f'__version__ = "{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    if n:
        return new_text
    # No static __version__ found (e.g. dynamic importlib.metadata pattern).
    # Extract the module docstring if present, then write a canonical header.
    doc_m = re.match(r'("""[^"]*"""|\'\'\'[^\']*\'\'\')', text)
    docstring = doc_m.group(0) if doc_m else '"""Biome FM."""'
    return f'{docstring}\n\n__version__ = "{version}"\n'


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------


def _atomic_write(path: Path, content: str) -> None:
    tmp = path.with_suffix(".tmp")
    try:
        tmp.write_bytes(content.encode("utf-8"))
        os.replace(str(tmp), str(path))
    finally:
        if tmp.exists():
            tmp.unlink()


def _validate(version: str) -> None:
    if not SEMVER_RE.fullmatch(version):
        print(f"Invalid semver: {version!r}", file=sys.stderr)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Modes
# ---------------------------------------------------------------------------


def _check() -> None:
    """Verify copies match canonical — exits non-zero on any drift."""
    canonical = _read_pyproject_version(PYPROJECT)
    _validate(canonical)
    init_ver = _read_init_version(INIT_PY)
    if canonical != init_ver:
        print(
            f"version mismatch:\n"
            f"  pyproject.toml : {canonical}\n"
            f"  __init__.py    : {init_ver}",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"versions in sync: {canonical}")


def _sync(version: str, *, update_canonical: bool) -> None:
    """Write version to all targets, with atomic writes and full rollback."""
    targets: dict[str, tuple[Path, object]] = {}
    if update_canonical:
        targets["pyproject.toml"] = (PYPROJECT, _update_pyproject)
    targets["__init__.py"] = (INIT_PY, _update_init)

    # Collect new content first — fail fast before touching disk.
    updates: list[tuple[str, Path, str, bytes]] = []
    for name, (path, updater) in targets.items():
        if not path.exists():
            print(f"Missing: {path}", file=sys.stderr)
            sys.exit(1)
        try:
            content = updater(path, version)  # type: ignore[operator]
            updates.append((name, path, content, path.read_bytes()))
        except Exception as exc:
            print(f"Failed to prepare {name}: {exc}", file=sys.stderr)
            sys.exit(1)

    # Atomic writes with rollback on failure.
    written: list[tuple[str, Path, bytes]] = []
    try:
        for name, path, content, original in updates:
            _atomic_write(path, content)
            written.append((name, path, original))
    except Exception as exc:
        for wname, wpath, original in reversed(written):
            try:
                wpath.write_bytes(original)
            except Exception as rb_err:
                print(f"Rollback failed {wname}: {rb_err}", file=sys.stderr)
        print(f"Write failed: {exc}", file=sys.stderr)
        sys.exit(1)

    for name, _, _, _ in updates:
        print(f"Updated {name} → {version}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    args = sys.argv[1:]

    if not args:
        print("Usage: sync_versions.py <version> | --sync | --check", file=sys.stderr)
        sys.exit(1)

    if args[0] == "--check":
        _check()
        return

    if args[0] == "--sync":
        version = _read_pyproject_version(PYPROJECT)
        _validate(version)
        _sync(version, update_canonical=False)
        return

    if len(args) != 1:
        print("Usage: sync_versions.py <version>", file=sys.stderr)
        sys.exit(1)

    version = args[0]
    _validate(version)
    _sync(version, update_canonical=True)


if __name__ == "__main__":
    main()
