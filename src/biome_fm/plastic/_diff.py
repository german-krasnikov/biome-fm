"""Diff helpers for Plastic SCM workspace files.

Two entry points:
  workspace_diff(path, cwd)          — fast path, delegates to `cm diff`
  cs_diff(path, cs_id, server_path)  — explicit CS via `cm getfile` + difflib
"""
from __future__ import annotations

import difflib
import tempfile
from pathlib import Path

from ._cm import CMError, run_cm
from ._models import CSDiffFile

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_IMAGE_SUFFIXES = frozenset({'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.ico', '.tga'})


def is_image(path: Path) -> bool:
    return path.suffix.lower() in _IMAGE_SUFFIXES


def is_binary(path: Path, chunk: int = 8192) -> bool:
    """Return True if path looks like a binary file (contains null bytes)."""
    try:
        with open(path, "rb") as f:
            return b"\x00" in f.read(chunk)
    except OSError:
        return False


def count_diff_lines(diff: str) -> tuple[int, int]:
    """Count added/removed lines in a unified diff. Returns (added, removed)."""
    added = removed = 0
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            added += 1
        elif line.startswith("-") and not line.startswith("---"):
            removed += 1
    return added, removed


def _strip_git_prefix(p: str) -> str:
    return p[2:] if p.startswith(("a/", "b/")) else p


def parse_cs_diff_files(diff_text: str) -> list[CSDiffFile]:
    """Split a full unified diff into per-file CSDiffFile entries."""
    chunks: list[str] = []
    current: list[str] = []
    for line in diff_text.splitlines(keepends=True):
        if (line.startswith("diff --") or line.startswith("=== ")) and current:
            chunks.append("".join(current))
            current = []
        current.append(line)
    if current:
        chunks.append("".join(current))

    results: list[CSDiffFile] = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        from_file = to_file = ""
        for line in chunk.splitlines():
            if line.startswith("--- "):
                from_file = line[4:].strip()
            elif line.startswith("+++ "):
                to_file = line[4:].strip()
        if not from_file and not to_file:
            continue
        if from_file == "/dev/null":
            status, path = "A", _strip_git_prefix(to_file)
        elif to_file == "/dev/null":
            status, path = "D", _strip_git_prefix(from_file)
        else:
            status, path = "M", _strip_git_prefix(to_file or from_file)
        added, removed = count_diff_lines(chunk)
        results.append(CSDiffFile(path=path, status=status, added=added, removed=removed, diff_text=chunk))
    return results


# ---------------------------------------------------------------------------
# Fast path: let cm produce the diff itself
# ---------------------------------------------------------------------------

_CM_STATUS_MAP = {"C": "M", "A": "A", "D": "D", "M": "R"}


def cs_log_files(cs_id: int, cwd: Path) -> list[CSDiffFile]:
    """Return files changed in *cs_id* via `cm log --itemformat`.

    Works on cloud/Unity Plastic workspaces where cs_range_diff fails.
    Status mapping: C→M (changed), A→A, D→D, M→R (moved/renamed).
    """
    out = run_cm(
        ["log", f"cs:{cs_id}", '--itemformat={shortstatus}|{path}{newline}'],
        cwd=cwd, safe=True,
    )
    if not out:
        return []
    results: list[CSDiffFile] = []
    in_changes = False
    for line in out.splitlines():
        if not in_changes:
            if line.strip() == "Changes:":
                in_changes = True
            continue
        if line.startswith("---"):
            break
        if "|" not in line:
            continue
        raw_status, _, path = line.partition("|")
        path = path.strip()
        if not path:
            continue
        status = _CM_STATUS_MAP.get(raw_status.strip(), raw_status.strip())
        results.append(CSDiffFile(path=path, status=status, added=0, removed=0, diff_text=""))
    return results


def cs_range_diff(cs_a: int, cs_b: int, cwd: Path) -> str:
    """cm diff cs:A..cs:B"""
    return run_cm(["diff", f"cs:{cs_a}..cs:{cs_b}"], cwd=cwd, safe=True)


def branch_diff(branch: str, cwd: Path) -> str:
    """cm diff br:/name — shows workspace vs branch tip"""
    name = branch if branch.startswith("br:") else f"br:{branch}"
    return run_cm(["diff", name], cwd=cwd, safe=True)


def label_range_diff(lb_a: str, lb_b: str, cwd: Path) -> str:
    """cm diff lb:A..lb:B"""
    return run_cm(["diff", f"lb:{lb_a}..lb:{lb_b}"], cwd=cwd, safe=True)


def shelve_diff(shelve_id: int, cwd: Path) -> str:
    """cm diff sh:N"""
    return run_cm(["diff", f"sh:{shelve_id}"], cwd=cwd, safe=True)


def workspace_diff(path: Path, cwd: Path) -> str:
    """Return unified diff for *path* vs its base changeset.

    Uses `cm diff <path> --format=unified`. Returns "" if cm unavailable or
    the file has no changes.
    """
    if is_binary(path):
        return "(binary file — diff not available)"
    out = run_cm(["diff", str(path), "--format=unified"], cwd=cwd, safe=True)
    return out


# ---------------------------------------------------------------------------
# Explicit CS path: cm getfile → difflib
# ---------------------------------------------------------------------------

def get_server_path(local_path: Path, cwd: Path) -> str | None:
    """Try to resolve the Plastic server path for *local_path*.

    Uses `cm fileinfo <path>`. The first line of output is the server path.
    Returns None if unavailable.

    cm fileinfo output example:
        /src/main/file.py
         cs:42 (07/24/2026 12:00:00) by alice@server
    """
    out = run_cm(["fileinfo", str(local_path)], cwd=cwd, safe=True)
    if not out:
        return None
    first = out.splitlines()[0].strip()
    # Must look like a repo path (starts with /)
    return first if first.startswith("/") else None


def _find_conflict_file(path: Path, tag: str) -> Path | None:
    """Find Plastic conflict sidecar e.g. file.txt.BASE.1.txt or file.BASE.txt."""
    parent = path.parent
    stem = path.stem
    for candidate in parent.iterdir():
        name = candidate.name
        if name.startswith(f"{stem}.{tag}") or name.startswith(f"{path.name}.{tag}"):
            return candidate
    return None


def get_merge_sides(path: Path, cwd: Path) -> tuple[str, str, str]:
    """Return (base, source, destination) for a conflicted file.

    Plastic SCM writes .BASE.* and .SOURCE.* sidecar files during merge
    conflicts. Falls back to cm diff for the base revision if sidecars
    are missing. Returns ("", "", "") on any error.
    """
    try:
        base_file = _find_conflict_file(path, "BASE")
        source_file = _find_conflict_file(path, "SOURCE")
        base = base_file.read_text(errors="replace") if base_file else ""
        source = source_file.read_text(errors="replace") if source_file else ""
        try:
            dest = path.read_text(errors="replace")
        except OSError:
            dest = ""
        return base, source, dest
    except Exception:
        return "", "", ""


def cs_diff(
    local_path: Path,
    cs_id: int,
    server_path: str | None = None,
    cwd: Path | None = None,
    context: int = 3,
) -> str:
    """Unified diff of *local_path* vs its content at changeset *cs_id*.

    server_path — Plastic server path (e.g. "/src/file.py").
                  If None, resolved via `cm fileinfo`. Falls back to bare
                  filename as last resort (works when repo root == workspace root).
    cwd         — workspace directory; defaults to local_path.parent.

    Returns "" on any failure (getfile error, file missing, unchanged).
    """
    _cwd = cwd or local_path.parent

    if is_binary(local_path):
        return "(binary file — diff not available)"

    if server_path is None:
        server_path = get_server_path(local_path, _cwd) or local_path.name

    cs_ref = f"{server_path}#cs:{cs_id}"

    with tempfile.NamedTemporaryFile(suffix=".base.tmp", delete=False) as tf:
        tmp = Path(tf.name)

    try:
        try:
            run_cm(["getfile", cs_ref, f"--file={tmp}"], cwd=_cwd)
        except CMError:
            return ""

        base_lines = tmp.read_text(errors="replace").splitlines(keepends=True)
    finally:
        tmp.unlink(missing_ok=True)

    try:
        cur_lines = local_path.read_text(errors="replace").splitlines(keepends=True)
    except OSError:
        cur_lines = []

    diff = difflib.unified_diff(
        base_lines,
        cur_lines,
        fromfile=f"{local_path.name}@cs:{cs_id}",
        tofile=str(local_path),
        n=context,
    )
    return "".join(diff)
