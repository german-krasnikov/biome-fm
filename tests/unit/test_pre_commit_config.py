"""Tests for .pre-commit-config.yaml correctness."""
import pathlib

import yaml


def _load_cfg() -> dict:
    cfg_path = pathlib.Path(__file__).parents[2] / ".pre-commit-config.yaml"
    with cfg_path.open() as f:
        return yaml.safe_load(f)


def _load_hooks() -> dict:
    cfg = _load_cfg()
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


def test_only_version_check_runs_on_pre_push() -> None:
    cfg = _load_cfg()
    assert cfg["default_stages"] == ["pre-commit"], (
        f"default_stages must be ['pre-commit'], got: {cfg.get('default_stages')!r}"
    )
    for repo in cfg["repos"]:
        for hook in repo.get("hooks", []):
            stages = hook.get("stages", cfg["default_stages"])
            is_version_check = hook["id"] == "version-check"
            assert ("pre-push" in stages) == is_version_check, (
                f"hook {hook['id']!r}: pre-push in stages={stages} "
                f"but is_version_check={is_version_check}"
            )
