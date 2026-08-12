"""Smoke tests for scripts/release.sh — arg parsing only."""
import subprocess
from pathlib import Path

SCRIPT = Path(__file__).parents[2] / "scripts" / "release.sh"
ROOT = Path(__file__).parents[2]


def test_release_sh_rejects_missing_preflight_flag():
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 2
    assert "--preflight" in result.stderr


def test_release_sh_rejects_wrong_flag():
    result = subprocess.run(
        ["bash", str(SCRIPT), "--publish"],
        capture_output=True,
        text=True,
        cwd=str(ROOT),
    )
    assert result.returncode == 2
    assert "Usage" in result.stderr
