"""Tests for .pre-commit-config.yaml correctness."""
import pathlib

import yaml


def _load_hooks() -> dict:
    cfg_path = pathlib.Path(__file__).parents[2] / ".pre-commit-config.yaml"
    with cfg_path.open() as f:
        cfg = yaml.safe_load(f)

    for repo in cfg["repos"]:
        if repo.get("repo") == "local":
            return {h["id"]: h for h in repo["hooks"]}
    return {}


def test_version_check_hook_uses_uv_python() -> None:
    hooks = _load_hooks()
    hook = hooks["version-check"]
    assert hook["entry"].startswith("uv run python"), (
        f"entry must start with 'uv run python', got: {hook['entry']!r}"
    )
    assert hook["language"] == "system"
    assert "pre-push" in hook["stages"]
