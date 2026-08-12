#!/usr/bin/env python3
"""Verify version consistency across biome-fm artifacts.

Checks:
  1. pyproject.toml has a valid semver version (canonical source)
  2. src/biome_fm/__init__.py has hardcoded __version__ matching pyproject.toml version
  3. CHANGELOG.md has an entry for the current version

Usage:
    python scripts/check_version.py [--root <path>]
"""
import re
import sys
from pathlib import Path

SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
ROOT = Path(__file__).parents[1]

PYPROJECT = ROOT / "pyproject.toml"
INIT_PY = ROOT / "src" / "biome_fm" / "__init__.py"
CHANGELOG = ROOT / "CHANGELOG.md"


def _read_pyproject_version(path: Path) -> str:
    m = re.search(r'^version\s*=\s*"([^"]+)"', path.read_text(encoding="utf-8"), re.MULTILINE)
    if not m:
        _fail(f"{path}: version field not found")
    return m.group(1)


def _check_init(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    if "__version__" not in text:
        _fail(f"{path}: __version__ is missing")
    m = re.search(r'__version__\s*=\s*"([^"]*)"', text)
    if not m:
        _fail(f"{path}: __version__ must be a hardcoded string literal")
    if m.group(1) != version:
        _fail(f"{path}: __version__ = {m.group(1)!r} but pyproject.toml has {version!r}")


def _check_changelog(path: Path, version: str) -> None:
    text = path.read_text(encoding="utf-8")
    # Format: ## [v0.34.0] — YYYY-MM-DD
    if not re.search(rf"^## \[v{re.escape(version)}\]", text, re.MULTILINE):
        _fail(
            f"CHANGELOG.md has no entry for v{version}.\n"
            f"  Expected a line matching: ## [v{version}] — YYYY-MM-DD"
        )


def _fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def main() -> None:
    for path in (PYPROJECT, INIT_PY, CHANGELOG):
        if not path.exists():
            _fail(f"Missing file: {path}")

    version = _read_pyproject_version(PYPROJECT)

    if not SEMVER_RE.fullmatch(version):
        _fail(f"pyproject.toml version {version!r} is not valid semver (X.Y.Z)")

    _check_init(INIT_PY, version)
    _check_changelog(CHANGELOG, version)

    print(f"OK: version {version} — pyproject.toml, __init__.py, CHANGELOG.md all consistent")


if __name__ == "__main__":
    main()
