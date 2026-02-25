"""Tests for PR blocked-response governance behavior."""
import importlib.util
import json
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


def test_retrigger_ci_rerequests_startup_failure_checks(monkeypatch):
    calls = []
    monkeypatch.setattr(
        diagnose,
        "get_check_runs",
        lambda _: [{"id": 55, "name": "Security Gates — Trivy + Checkov + Gitleaks", "status": "completed", "conclusion": "startup_failure"}],
    )
    monkeypatch.setattr(
        diagnose,
        "gh_api",
        lambda path, method="GET", data=None: calls.append((path, method)) or {},
    )

    count = diagnose.retrigger_ci(123, "deadbeef", {"Security Gates — Trivy + Checkov + Gitleaks"})

    assert count == 1
    assert (f"/repos/{diagnose.REPO}/check-runs/55/rerequest", "POST") in calls


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
        {"name": "canary-gate", "status": "completed", "conclusion": "failure"},
        {"name": "optional-ci-health", "status": "completed", "conclusion": "skipped"},
        {"name": "optional-ci-health-queued", "status": "queued", "conclusion": "skipped"},
        {"name": "request-codacy-review", "status": "completed", "conclusion": "skipped"},
        {"name": "lint", "status": "completed", "conclusion": "failure"},
    ])
    assert ("Security Gates — Trivy + Checkov + Gitleaks", "startup_failure") in anomalies
    assert ("canary-gate", "failure") in anomalies
    assert ("optional-ci-health", "skipped") in anomalies
    assert ("optional-ci-health-queued", "skipped") not in anomalies
    assert ("request-codacy-review", "skipped") not in anomalies
    assert ("lint", "failure") not in anomalies


def test_build_dedup_key_uses_pr_sha_and_source(monkeypatch):
    monkeypatch.setattr(diagnose, "TRIGGER_EVENT", "workflow_run")
    monkeypatch.setattr(diagnose, "SOURCE_WORKFLOW", "Security Gates — Trivy + Checkov + Gitleaks")
    assert (
        diagnose.build_dedup_key(280, "abc123")
        == "280:abc123:Security Gates — Trivy + Checkov + Gitleaks"
    )


def test_upsert_anomaly_issue_includes_source_observed_at_and_markers(monkeypatch):
    captured = {}
    monkeypatch.setattr(diagnose, "TRIGGER_EVENT", "workflow_run")
    monkeypatch.setattr(diagnose, "SOURCE_WORKFLOW", "Security Gates — Trivy + Checkov + Gitleaks")
    monkeypatch.setattr(diagnose, "find_open_auto_anomaly_issue", lambda _: None)

    def fake_gh_api(path, method="GET", data=None):
        if path.endswith("/issues") and method == "POST":
            captured["body"] = data["body"]
            return {"number": 321}
        return {}

    monkeypatch.setattr(diagnose, "gh_api", fake_gh_api)

    result = diagnose.upsert_auto_anomaly_issue(280, [("canary-gate", "failure")], "abc123")

    assert result["issue_number"] == 321
    assert result["anomaly_count"] == 1
    assert result["dedup_skipped"] is False
    assert "Trigger Source" in captured["body"]
    assert "workflow_run: Security Gates — Trivy + Checkov + Gitleaks" in captured["body"]
    assert "Observed At" in captured["body"]
    assert "<!-- autoecoops:dkey=280:abc123:Security Gates — Trivy + Checkov + Gitleaks -->" in captured["body"]


def test_upsert_anomaly_issue_dedups_same_key(monkeypatch):
    monkeypatch.setattr(diagnose, "TRIGGER_EVENT", "schedule")
    monkeypatch.setattr(diagnose, "SOURCE_WORKFLOW", "")
    dedup_key = diagnose.build_dedup_key(280, "headsha")
    signature = diagnose.build_anomaly_signature([("canary-gate", "failure")])
    issue_body = (
        "x\n"
        f"<!-- autoecoops:dkey={dedup_key} -->\n"
        f"<!-- autoecoops:asig={signature} -->\n"
        "<!-- autoecoops:acount=2 -->\n"
    )
    monkeypatch.setattr(
        diagnose,
        "find_open_auto_anomaly_issue",
        lambda _: {"number": 42, "body": issue_body},
    )
    calls = []
    monkeypatch.setattr(diagnose, "gh_api", lambda *args, **kwargs: calls.append((args, kwargs)) or {})

    result = diagnose.upsert_auto_anomaly_issue(280, [("canary-gate", "failure")], "headsha")

    assert result["issue_number"] == 42
    assert result["anomaly_count"] == 2
    assert result["dedup_skipped"] is True
    assert not calls


def test_apply_anomaly_escalation_adds_labels(monkeypatch):
    added_labels = []
    patched_labels = []

    monkeypatch.setattr(diagnose, "add_label", lambda pr, label: added_labels.append((pr, label)))

    def fake_gh_api(path, method="GET", data=None):
        if path.endswith("/issues/88") and method == "GET":
            return {"labels": [{"name": "blocked"}]}
        if path.endswith("/issues/88") and method == "PATCH":
            patched_labels.append(data["labels"])
            return {}
        return {}

    monkeypatch.setattr(diagnose, "gh_api", fake_gh_api)

    diagnose.apply_anomaly_escalation(280, 88, diagnose.ANOMALY_ESCALATION_THRESHOLD)

    assert (280, diagnose.HUMAN_REVIEW_LABEL) in added_labels
    assert patched_labels
    assert diagnose.ANOMALY_SEVERITY_LABEL in patched_labels[0]


def test_get_open_prs_keeps_draft_prs(monkeypatch):
    payload = json.dumps([
        {"number": 1, "isDraft": True},
        {"number": 2, "isDraft": False},
    ])

    class Result:
        returncode = 0
        stdout = payload

    monkeypatch.setattr(diagnose, "gh_run", lambda *args, **kwargs: Result())
    prs = diagnose.get_open_prs()
    assert [p["number"] for p in prs] == [1, 2]


def test_process_pr_draft_retriggers_failures_without_merge(monkeypatch):
    monkeypatch.setattr(
        diagnose,
        "get_check_runs",
        lambda _: [{"name": "lint", "status": "completed", "conclusion": "failure"}],
    )
    monkeypatch.setattr(diagnose, "ensure_conventional_pr_title", lambda _n, title: title)
    monkeypatch.setattr(diagnose, "apply_mechanical_codacy_fixes", lambda *_: False)
    monkeypatch.setattr(diagnose, "collect_non_required_gate_anomalies", lambda _: [])
    monkeypatch.setattr(diagnose, "close_auto_anomaly_issue_if_clean", lambda *_: None)

    retriggered = []
    merged = []
    auto_merged = []
    monkeypatch.setattr(diagnose, "retrigger_ci", lambda pr, sha, names: retriggered.append((pr, sha, set(names))))
    monkeypatch.setattr(diagnose, "direct_merge", lambda *args, **kwargs: merged.append(args))
    monkeypatch.setattr(diagnose, "enable_auto_merge", lambda *args, **kwargs: auto_merged.append(args))

    diagnose.process_pr(
        pr_num=280,
        pr_title="t",
        pr_branch="b",
        head_sha="abc",
        merge_status="BLOCKED",
        labels=[],
        is_draft=True,
    )

    assert retriggered
    assert not merged
    assert not auto_merged


def test_process_pr_draft_updates_behind_branch(monkeypatch):
    monkeypatch.setattr(diagnose, "get_check_runs", lambda _: [])
    monkeypatch.setattr(diagnose, "ensure_conventional_pr_title", lambda _n, title: title)
    monkeypatch.setattr(diagnose, "apply_mechanical_codacy_fixes", lambda *_: False)
    monkeypatch.setattr(diagnose, "collect_non_required_gate_anomalies", lambda _: [])
    monkeypatch.setattr(diagnose, "close_auto_anomaly_issue_if_clean", lambda *_: None)

    updates = []
    monkeypatch.setattr(diagnose, "update_branch", lambda pr: updates.append(pr))
    monkeypatch.setattr(diagnose, "direct_merge", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not merge draft")))
    monkeypatch.setattr(diagnose, "enable_auto_merge", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("should not auto-merge draft")))

    diagnose.process_pr(
        pr_num=280,
        pr_title="t",
        pr_branch="b",
        head_sha="abc",
        merge_status="BEHIND",
        labels=[],
        is_draft=True,
    )

    assert updates == [280]


def test_ensure_conventional_pr_title_updates_when_invalid(monkeypatch):
    calls = []
    monkeypatch.setattr(diagnose, "gh_api", lambda path, method="GET", data=None: calls.append((path, method, data)) or {})

    new_title = diagnose.ensure_conventional_pr_title(280, "[WIP] Fix errors")

    assert new_title.startswith("chore(pr): ")
    assert calls and calls[0][1] == "PATCH"


def test_ensure_conventional_pr_title_keeps_valid(monkeypatch):
    calls = []
    monkeypatch.setattr(diagnose, "gh_api", lambda path, method="GET", data=None: calls.append((path, method, data)) or {})

    title = "fix(ci): resolve startup failure for security gates"
    out = diagnose.ensure_conventional_pr_title(280, title)

    assert out == title
    assert not calls


def test_apply_mechanical_codacy_fixes_signed_commit_with_optional_details(monkeypatch):
    monkeypatch.setattr(
        diagnose,
        "get_pr_review_comments",
        lambda _pr: [{
            "user": {"login": "codacy-production[bot]"},
            "body": "Codacy found an issue: I001",
            "path": "tools/pr-blocked-response/diagnose.py",
        }],
    )
    monkeypatch.setattr(diagnose, "AUTOFIX_SIGNOFF", True)
    monkeypatch.setattr(diagnose, "AUTOFIX_DETAILS", "Apply safe mechanical formatting fixes")

    commit_cmds = []
    comments = []

    class Result:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(cmd, capture_output=True, text=True):
        if cmd[:2] == [diagnose.sys.executable, "-m"]:
            return Result(returncode=0)
        if cmd[:3] == ["git", "status", "--porcelain"]:
            return Result(stdout=" M tools/pr-blocked-response/diagnose.py\n")
        if cmd[:2] == ["git", "commit"]:
            commit_cmds.append(cmd)
            return Result(returncode=0)
        if cmd[:3] == ["git", "rev-parse", "--short"]:
            return Result(stdout="abc123\n")
        if cmd[:2] == ["git", "push"]:
            return Result(returncode=0)
        return Result(returncode=0)

    monkeypatch.setattr(diagnose.subprocess, "run", fake_run)
    monkeypatch.setattr(
        diagnose,
        "gh_api",
        lambda path, method="GET", data=None: comments.append((path, method, data)) or {},
    )

    ok = diagnose.apply_mechanical_codacy_fixes(280, "copilot/fix-automation-workflow-errors")

    assert ok is True
    assert commit_cmds and "-s" in commit_cmds[0]
    assert any("Apply safe mechanical formatting fixes" in (entry[2] or {}).get("body", "") for entry in comments)


class _DummyAuditTrail:
    def __init__(self, *_args, **_kwargs):
        self.final_action = None
        self.final_outcome = None

    def record_step(self, *_args, **_kwargs):
        return None

    def record_decision(self, *_args, **_kwargs):
        return None

    def compute_risk_score(self, *_args, **_kwargs):
        return 0

    def save(self):
        return None


def test_engine_draft_pending_enters_maintenance_without_automerge(monkeypatch):
    monkeypatch.setattr(engine, "circuit_breaker_check", lambda: False)
    monkeypatch.setattr(engine, "AuditTrail", _DummyAuditTrail)
    monkeypatch.setattr(engine, "capture_pr_snapshot", lambda _pr: {"state_hash": "x", "tarball_path": "/tmp/x"})
    monkeypatch.setattr(engine, "evaluate_bot_governance", lambda _pr: {"decision": "ok", "max_tier": "TIER-2", "has_escalation": False, "comments": [], "state_hash": "h"})

    def fake_gh_api(path, method="GET", data=None):
        if path.endswith("/pulls/280"):
            return {
                "head": {"sha": "abc", "ref": "branch"},
                "mergeable": True,
                "mergeable_state": "clean",
                "labels": [],
                "title": "t",
                "draft": True,
                "auto_merge": None,
                "user": {"login": "dev"},
            }
        if "check-runs" in path:
            return {"check_runs": [{"name": "validate", "status": "queued", "conclusion": None}]}
        return {}

    monkeypatch.setattr(engine, "gh_api", fake_gh_api)
    merge_calls = []
    monkeypatch.setattr(engine, "gh_cli", lambda args: merge_calls.append(args) or (0, "", ""))

    result = engine.process_pr_with_governance(280)

    assert result["action"] == "MONITOR_DRAFT"
    assert result["outcome"] == "ci_in_progress_draft"
    assert not merge_calls


def test_engine_draft_all_pass_does_not_merge(monkeypatch):
    monkeypatch.setattr(engine, "circuit_breaker_check", lambda: False)
    monkeypatch.setattr(engine, "AuditTrail", _DummyAuditTrail)
    monkeypatch.setattr(engine, "capture_pr_snapshot", lambda _pr: {"state_hash": "x", "tarball_path": "/tmp/x"})
    monkeypatch.setattr(engine, "evaluate_bot_governance", lambda _pr: {"decision": "ok", "max_tier": "TIER-2", "has_escalation": False, "comments": [], "state_hash": "h"})

    def fake_gh_api(path, method="GET", data=None):
        if path.endswith("/pulls/280"):
            return {
                "head": {"sha": "abc", "ref": "branch"},
                "mergeable": True,
                "mergeable_state": "clean",
                "labels": [],
                "title": "t",
                "draft": True,
                "auto_merge": None,
                "user": {"login": "dev"},
            }
        if "check-runs" in path:
            return {
                "check_runs": [
                    {"name": "validate", "status": "completed", "conclusion": "success"},
                    {"name": "lint", "status": "completed", "conclusion": "success"},
                    {"name": "test", "status": "completed", "conclusion": "success"},
                    {"name": "build", "status": "completed", "conclusion": "success"},
                    {"name": "opa-policy", "status": "completed", "conclusion": "success"},
                    {"name": "supply-chain", "status": "completed", "conclusion": "success"},
                ]
            }
        return {}

    monkeypatch.setattr(engine, "gh_api", fake_gh_api)
    merge_calls = []
    monkeypatch.setattr(engine, "gh_cli", lambda args: merge_calls.append(args) or (0, "", ""))

    result = engine.process_pr_with_governance(280)

    assert result["action"] == "DRAFT_MAINTENANCE"
    assert result["outcome"] == "ready_but_draft"
    assert not merge_calls
