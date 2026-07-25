from __future__ import annotations
from pathlib import Path
from ._cm import run_cm


def replication_push(server: str, repo: str, cwd: Path) -> str:
    return run_cm(["replication", "push", f"--server={server}", f"--repository={repo}"], cwd=cwd, safe=True, timeout=300)


def replication_pull(server: str, cwd: Path) -> str:
    return run_cm(["replication", "pull", f"--server={server}"], cwd=cwd, safe=True, timeout=300)


def package_create(output_path: str, cwd: Path) -> str:
    return run_cm(["replica", "package", "create", f"--file={output_path}"], cwd=cwd, safe=True, timeout=300)


def package_import(file_path: str, cwd: Path) -> str:
    return run_cm(["replica", "package", "import", f"--file={file_path}"], cwd=cwd, safe=True, timeout=300)
