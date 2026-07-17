"""Unit tests for ScriptRunner (Feature #20)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from biome_fm.models.script_runner import ScriptRunner


def test_list_scripts(tmp_path: Path) -> None:
    (tmp_path / "run.py").touch()
    (tmp_path / "deploy.sh").touch()
    (tmp_path / "readme.md").touch()  # not a script
    runner = ScriptRunner(tmp_path)
    names = {p.name for p in runner.list_scripts()}
    assert names == {"run.py", "deploy.sh"}


def test_run_passes_env(tmp_path: Path) -> None:
    script = tmp_path / "show_env.py"
    script.write_text(
        "import os, sys\n"
        "print(os.environ['BIOME_SELECTED'])\n"
        "print(os.environ['BIOME_CWD'])\n"
    )
    script.chmod(0o755)
    cwd = tmp_path / "cwd"
    cwd.mkdir()
    selected = [tmp_path / "a.txt", tmp_path / "b.txt"]
    runner = ScriptRunner(tmp_path)
    result = runner.run(script, selected, cwd)
    assert result.returncode == 0
    out = result.stdout
    assert str(selected[0]) in out
    assert str(cwd) in out


def test_timeout_handled(tmp_path: Path) -> None:
    script = tmp_path / "slow.py"
    script.write_text("import time; time.sleep(100)\n")
    script.chmod(0o755)
    runner = ScriptRunner(tmp_path)
    with pytest.raises(subprocess.TimeoutExpired):
        runner.run(script, [], tmp_path, timeout=0.1)
