"""Tests for CI configuration correctness (ci.yml / release.yml)."""
import pathlib

import yaml

_CI = pathlib.Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"
_RELEASE = pathlib.Path(__file__).parents[2] / ".github" / "workflows" / "release.yml"


def _load_ci() -> dict:
    return yaml.safe_load(_CI.read_text())


def _load_release() -> dict:
    return yaml.safe_load(_RELEASE.read_text())


# ── CI_GATE-02 ────────────────────────────────────────────────────────────────

def test_integration_in_ci_pass_needs() -> None:
    ci = _load_ci()
    needs = ci["jobs"]["ci-pass"]["needs"]
    assert "integration" in needs, (
        "ci-pass gate must include 'integration' in needs"
    )


def test_integration_job_no_continue_on_error() -> None:
    ci = _load_ci()
    assert not ci["jobs"]["integration"].get("continue-on-error"), (
        "integration job must not use continue-on-error"
    )


def test_ci_pass_evaluate_checks_integration() -> None:
    ci = _load_ci()
    evaluate_step = next(
        s for s in ci["jobs"]["ci-pass"]["steps"]
        if "Evaluate" in s.get("name", "")
    )
    assert "integration" in evaluate_step["run"], (
        "ci-pass evaluate step must check integration result"
    )


# ── CI_GATE-03 ────────────────────────────────────────────────────────────────

def test_release_preflight_has_ci_check() -> None:
    release = _load_release()
    preflight_steps = release["jobs"]["preflight"]["steps"]
    ci_check = any(
        "gh run list" in s.get("run", "") and "CI" in s.get("run", "")
        for s in preflight_steps
    )
    assert ci_check, (
        "release preflight must verify a passing CI run before proceeding"
    )


def test_release_preflight_has_actions_read_permission() -> None:
    release = _load_release()
    perms = release["jobs"]["preflight"].get("permissions", {})
    assert perms.get("actions") == "read", (
        "release preflight job needs actions: read to call gh run list"
    )
