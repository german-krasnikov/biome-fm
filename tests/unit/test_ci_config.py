"""Tests for CI configuration correctness (ci.yml / release.yml)."""
import pathlib

import yaml

_CI = pathlib.Path(__file__).parents[2] / ".github" / "workflows" / "ci.yml"


def _load_ci() -> dict:
    return yaml.safe_load(_CI.read_text())


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
