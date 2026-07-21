"""ScriptRunner — discovers and executes scripts from a folder (Feature #20)."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

_SCRIPT_GLOBS = ("*.py", "*.sh")


class ScriptRunner:
    def __init__(self, script_dir: Path) -> None:
        self._dir = script_dir

    def list_scripts(self) -> list[Path]:
        results: list[Path] = []
        for glob in _SCRIPT_GLOBS:
            results.extend(sorted(self._dir.glob(glob)))
        return results

    def run(
        self,
        script: Path,
        selected: list[Path],
        cwd: Path,
        timeout: float = 30,
        ipc_port: int = 0,
    ) -> subprocess.CompletedProcess:
        if not script.resolve().is_relative_to(self._dir.resolve()):
            raise ValueError(f"Script {script} is outside {self._dir}")
        env = {
            **os.environ,
            "BIOME_SELECTED": "\n".join(str(p) for p in selected),
            "BIOME_CWD": str(cwd),
        }
        if ipc_port:
            env["BIOME_IPC_PORT"] = str(ipc_port)
        cmd = [sys.executable, str(script)] if script.suffix == ".py" else [str(script)]
        return subprocess.run(
            cmd, env=env, capture_output=True, text=True, timeout=timeout
        )
