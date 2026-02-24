"""Tests for PR blocked-response governance behavior."""
import importlib.util
import os


REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIAGNOSE_PATH = os.path.join(REPO_ROOT, "tools", "pr-blocked-response", "diagnose.py")
ENGINE_PATH = os.path.join(REPO_ROOT, "tools", "autoecops-governance", "engine.py")


def _load_module(path, module_name):
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


diagnose = _load_module(DIAGNOSE_PATH, "diagnose_module")
engine = _load_module(ENGINE_PATH, "engine_module")


def test_classify_checks_treats_required_skipped_as_pending():
    passing, failing, pending, all_pass, any_pending = diagnose.classify_checks([
        {"id": 10, "name": "validate", "status": "completed", "conclusion": "success"},
        {"id": 11, "name": "lint", "status": "completed", "conclusion": "skipped"},
    ])
    assert "validate" in passing
    assert "lint" in pending
    assert not failing
    assert not all_pass
    assert any_pending


def test_retrigger_ci_rerequests_skipped_required_checks(monkeypatch):
    calls = []

    monkeypatch.setattr(
        diagnose,
        "get_check_runs",
        lambda _: [{"id": 99, "name": "lint", "status": "completed", "conclusion": "skipped"}],
    )
    monkeypatch.setattr(
        diagnose,
        "gh_api",
        lambda path, method="GET", data=None: calls.append((path, method)) or {},
    )

    diagnose.retrigger_ci(123, "deadbeef", {"lint"})

    assert (f"/repos/{diagnose.REPO}/check-runs/99/rerequest", "POST") in calls


def test_engine_classify_marks_skipped_required_as_pending():
    summary = engine.classify_check_runs([
        {"name": "validate", "status": "completed", "conclusion": "success"},
        {"name": "lint", "status": "completed", "conclusion": "skipped"},
    ])
    assert summary["all_required_pass"] is False
    assert summary["any_required_pending"] is True
    assert summary["any_required_failed"] is False
    assert "lint" in summary["unexpected_skips"]
    assert "test" in summary["missing_required"]


def test_collect_non_required_gate_anomalies_detects_failed_and_key_skipped():
    anomalies = diagnose.collect_non_required_gate_anomalies([
        {"name": "Security Gates — Trivy + Checkov + Gitleaks", "status": "completed", "conclusion": "startup_failure"},
        {"name": "optional-ci-health", "status": "completed", "conclusion": "skipped"},
        {"name": "request-codacy-review", "status": "completed", "conclusion": "skipped"},
        {"name": "lint", "status": "completed", "conclusion": "failure"},
    ])
    assert ("Security Gates — Trivy + Checkov + Gitleaks", "startup_failure") in anomalies
    assert ("optional-ci-health", "skipped") in anomalies
    assert ("request-codacy-review", "skipped") not in anomalies
    assert ("lint", "failure") not in anomalies
