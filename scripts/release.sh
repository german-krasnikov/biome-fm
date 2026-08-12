#!/usr/bin/env bash
# Release preflight — read-only validation, never mutates anything.
#
# Checks:
#   1. Version sync: pyproject.toml == installed package metadata
#   2. CHANGELOG.md has an entry for the current version
#   3. ruff check src/ passes
#   4. git working tree is clean (no staged, unstaged, or untracked files)
#
# Usage:
#   ./scripts/release.sh --preflight
#   ./scripts/release.sh --preflight 0.35.0   # also asserts exact version
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
cd "$ROOT"

if [[ $# -lt 1 || "$1" != "--preflight" || $# -gt 2 ]]; then
    echo "scripts/release.sh is a read-only preflight validator." >&2
    echo "Usage: ./scripts/release.sh --preflight [EXPECTED_VERSION]" >&2
    echo "To publish, use the create-release workflow." >&2
    exit 2
fi
EXPECTED_VERSION="${2:-}"

# Resolve Python — prefer the project venv
if [[ -x "$ROOT/.venv/bin/python" ]]; then
    PYTHON="$ROOT/.venv/bin/python"
else
    PYTHON="${PYTHON:-python3}"
fi

# ---------------------------------------------------------------------------
echo "==> Checking version sync (pyproject.toml vs installed package)"
# ---------------------------------------------------------------------------
"$PYTHON" - "$EXPECTED_VERSION" <<'PY'
import pathlib, re, sys
from importlib.metadata import version as pkg_version, PackageNotFoundError

root = pathlib.Path(".")
content = (root / "pyproject.toml").read_text(encoding="utf-8")
m = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
if not m:
    raise SystemExit("ERROR: Cannot parse version from pyproject.toml")
toml_ver = m.group(1)

try:
    installed_ver = pkg_version("biome-fm")
except PackageNotFoundError:
    raise SystemExit(
        "ERROR: Package biome-fm is not installed.\n"
        "Run 'uv sync --all-extras' first."
    )

if toml_ver != installed_ver:
    raise SystemExit(
        f"ERROR: Version mismatch — pyproject.toml={toml_ver}, installed={installed_ver}\n"
        "Run 'uv sync --all-extras' to synchronise."
    )

expected = sys.argv[1].removeprefix("v") if sys.argv[1] else None
if expected and toml_ver != expected:
    raise SystemExit(
        f"ERROR: Expected version {expected}, but pyproject.toml has {toml_ver}"
    )

print(f"  version {toml_ver}: OK")
PY

# ---------------------------------------------------------------------------
echo "==> Checking CHANGELOG.md has entry for current version"
# ---------------------------------------------------------------------------
"$PYTHON" - <<'PY'
import pathlib, re, sys

pyproject = pathlib.Path("pyproject.toml").read_text(encoding="utf-8")
m = re.search(r'^version = "([^"]+)"', pyproject, re.MULTILINE)
ver = m.group(1)

changelog = pathlib.Path("CHANGELOG.md").read_text(encoding="utf-8")
# Accept both [v0.34.0] and [0.34.0]
if not re.search(rf"^## \[v?{re.escape(ver)}\]", changelog, re.MULTILINE):
    raise SystemExit(
        f"ERROR: CHANGELOG.md has no entry for version {ver}.\n"
        f"Add a '## [v{ver}] — YYYY-MM-DD' section before releasing."
    )

print(f"  CHANGELOG entry for v{ver}: OK")
PY

# ---------------------------------------------------------------------------
echo "==> Running ruff check"
# ---------------------------------------------------------------------------
"$PYTHON" -m ruff check src/

# ---------------------------------------------------------------------------
echo "==> Checking git working tree is clean"
# ---------------------------------------------------------------------------
DIRTY=0

if ! git diff --quiet; then
    echo "ERROR: Unstaged changes present:" >&2
    git diff --name-only >&2
    DIRTY=1
fi

if ! git diff --cached --quiet; then
    echo "ERROR: Staged changes present:" >&2
    git diff --cached --name-only >&2
    DIRTY=1
fi

UNTRACKED="$(git ls-files --others --exclude-standard)"
if [[ -n "$UNTRACKED" ]]; then
    echo "ERROR: Untracked files present:" >&2
    echo "$UNTRACKED" >&2
    DIRTY=1
fi

if [[ $DIRTY -ne 0 ]]; then
    echo "" >&2
    echo "Working tree must be clean before releasing. Commit or stash changes." >&2
    exit 1
fi

echo "  working tree: clean"

# ---------------------------------------------------------------------------
echo ""
echo "==> Preflight passed"
echo "No files were changed, staged, committed, tagged, pushed, or released."
echo "Continue with the create-release workflow."
