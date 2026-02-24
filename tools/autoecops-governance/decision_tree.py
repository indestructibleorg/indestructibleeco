#!/usr/bin/env python3
"""
AutoEcoOps AI-Assisted Diagnosis Decision Tree
================================================
Structured decision tree for root cause analysis and action recommendation.
Implements the L2 diagnosis layer of the governance engine.

Decision Tree Structure:
  Root → Check state
    ├── DIRTY → Rebase strategy
    ├── CI_PENDING → Monitor / enable auto-merge
    ├── CI_FAILED → Root cause analysis
    │   ├── supply-chain → Syft/Trivy diagnosis
    │   ├── build → Build error analysis
    │   ├── test → Test regression analysis
    │   ├── lint → Lint error analysis
    │   ├── validate → Workflow syntax analysis
    │   └── opa-policy → Policy violation analysis
    ├── BOT_ESCALATION → Governance tier evaluation
    └── SAFE → Merge

Each leaf node returns:
  - action: what to do
  - confidence: high/medium/low
  - evidence_required: what external validation is needed
  - next_level: L1/L2/L3/L4/L5
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class DiagnosisNode:
    """A node in the diagnosis decision tree."""
    id: str
    condition: str
    action: str
    confidence: str  # high / medium / low
    next_level: str  # L1 / L2 / L3 / L4 / L5 / NONE
    evidence_required: list[str] = field(default_factory=list)
    sub_nodes: list["DiagnosisNode"] = field(default_factory=list)
    explanation: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "condition": self.condition,
            "action": self.action,
            "confidence": self.confidence,
            "next_level": self.next_level,
            "evidence_required": self.evidence_required,
            "explanation": self.explanation,
            "sub_nodes": [n.to_dict() for n in self.sub_nodes],
        }


# ─── Decision Tree Definition ─────────────────────────────────────────────────

DECISION_TREE = DiagnosisNode(
    id="root",
    condition="PR state evaluation",
    action="EVALUATE",
    confidence="high",
    next_level="NONE",
    sub_nodes=[
        DiagnosisNode(
            id="dirty",
            condition="mergeable_state == 'dirty'",
            action="NEEDS_REBASE",
            confidence="high",
            next_level="L1",
            explanation="PR has merge conflicts. Dependabot PRs: @dependabot rebase. "
                        "Human PRs: request rebase.",
        ),
        DiagnosisNode(
            id="ci_pending",
            condition="any required check status != 'completed'",
            action="MONITOR",
            confidence="high",
            next_level="NONE",
            explanation="CI is still running. Enable auto-merge and wait.",
        ),
        DiagnosisNode(
            id="ci_failed",
            condition="any required check conclusion == 'failure'",
            action="FAILURE_RESPONSE",
            confidence="high",
            next_level="L1",
            sub_nodes=[
                DiagnosisNode(
                    id="supply_chain_failed",
                    condition="'supply-chain' check failed",
                    action="RETRY_SUPPLY_CHAIN",
                    confidence="high",
                    next_level="L1",
                    evidence_required=["syft_install_log", "trivy_scan_log"],
                    explanation="Supply-chain gate failure. Most common causes:\n"
                                "1. Syft install timeout (network) → retry\n"
                                "2. Trivy DB update failure → retry\n"
                                "3. SBOM generation error → check Syft version\n"
                                "L1: Re-run CI. If 3+ consecutive failures → L3 external validation.",
                ),
                DiagnosisNode(
                    id="build_failed",
                    condition="'build' check failed",
                    action="ANALYZE_BUILD_LOGS",
                    confidence="medium",
                    next_level="L2",
                    evidence_required=["build_log", "dockerfile"],
                    explanation="Build failure. Common causes:\n"
                                "1. Docker base image tag not found → L3 verify tag\n"
                                "2. Missing dependency → check package.json/pyproject.toml\n"
                                "3. Compilation error → code fix required\n"
                                "L1: Re-run. If Docker tag issue → L3 verify via Docker Hub API.",
                ),
                DiagnosisNode(
                    id="test_failed",
                    condition="'test' check failed",
                    action="ANALYZE_TEST_LOGS",
                    confidence="medium",
                    next_level="L2",
                    evidence_required=["test_log", "test_diff"],
                    explanation="Test regression. Common causes:\n"
                                "1. New code breaks existing test → code fix required\n"
                                "2. Flaky test → retry once\n"
                                "3. Environment issue → L4 sandbox simulation\n"
                                "L1: Retry once. If still fails → L2 analyze test diff.",
                ),
                DiagnosisNode(
                    id="lint_failed",
                    condition="'lint' check failed",
                    action="AUTO_FIX_LINT",
                    confidence="high",
                    next_level="L1",
                    evidence_required=["lint_log"],
                    explanation="Lint/type error. Usually auto-fixable:\n"
                                "1. ESLint/Ruff auto-fix → commit fix\n"
                                "2. Type error → may need code change\n"
                                "L1: Run auto-fix and push. If type error → L2.",
                ),
                DiagnosisNode(
                    id="validate_failed",
                    condition="'validate' check failed",
                    action="CHECK_WORKFLOW_SYNTAX",
                    confidence="high",
                    next_level="L2",
                    evidence_required=["validate_log", "workflow_yaml"],
                    explanation="Workflow validation failure. Common causes:\n"
                                "1. continue-on-error (prohibited) → use || true pattern\n"
                                "2. Invalid action version → verify via GitHub API\n"
                                "3. Missing required field → check ci-validator rules\n"
                                "L2: Analyze validate log and fix workflow YAML.",
                ),
                DiagnosisNode(
                    id="opa_failed",
                    condition="'opa-policy' check failed",
                    action="CHECK_POLICY_VIOLATION",
                    confidence="high",
                    next_level="L2",
                    evidence_required=["opa_log", "qyaml_files"],
                    explanation="OPA policy gate failure. Common causes:\n"
                                "1. Missing required .qyaml field → add field\n"
                                "2. Policy version mismatch → update policy\n"
                                "3. New policy rule added → check policy/\n"
                                "L2: Check OPA evaluation output and fix .qyaml or policy.",
                ),
            ],
        ),
        DiagnosisNode(
            id="bot_escalation",
            condition="bot_governance.has_escalation == True",
            action="KEEP_HUMAN_REVIEW",
            confidence="high",
            next_level="NONE",
            sub_nodes=[
                DiagnosisNode(
                    id="tier3_docker_tag",
                    condition="escalation contains 'does not exist' or 'invalid tag'",
                    action="VERIFY_DOCKER_TAG",
                    confidence="medium",
                    next_level="L3",
                    evidence_required=["docker_hub_api", "ngc_mirror"],
                    explanation="Bot claims Docker tag doesn't exist. "
                                "L3: Verify via Docker Hub API (multi-source). "
                                "If tag confirmed valid → remove escalation and merge. "
                                "If tag invalid → close PR with safe replacement suggestion.",
                ),
                DiagnosisNode(
                    id="tier3_security",
                    condition="escalation contains 'CVE-' or 'security vulnerability'",
                    action="SECURITY_REVIEW",
                    confidence="high",
                    next_level="L5",
                    evidence_required=["cve_database", "nvd_api"],
                    explanation="Security vulnerability flagged. "
                                "L5: Lock PR, create security issue, require human review. "
                                "Do not auto-merge under any circumstances.",
                ),
                DiagnosisNode(
                    id="tier3_breaking",
                    condition="escalation contains 'breaking change'",
                    action="BREAKING_CHANGE_REVIEW",
                    confidence="high",
                    next_level="L4",
                    evidence_required=["changelog", "semver_diff"],
                    explanation="Breaking change flagged. "
                                "L4: Sandbox simulation to verify impact. "
                                "If simulation passes → remove escalation. "
                                "If fails → L5 safeguard.",
                ),
            ],
        ),
        DiagnosisNode(
            id="safe_to_merge",
            condition="all required checks pass AND no bot escalation",
            action="MERGE",
            confidence="high",
            next_level="NONE",
            explanation="All required checks pass, no governance escalation. "
                        "Remove human-review-required label if present. "
                        "Squash merge with --admin.",
        ),
    ],
)


# ─── Traversal ────────────────────────────────────────────────────────────────

def traverse(
    node: DiagnosisNode,
    context: dict,
    path: list[str] | None = None,
) -> dict:
    """
    Traverse the decision tree given a PR context.
    Returns the matched leaf node with full path.
    """
    if path is None:
        path = []

    path = path + [node.id]

    # Evaluate condition against context
    matched = evaluate_condition(node.id, context)

    if not matched and node.id != "root":
        return {}

    # If leaf node (no sub_nodes), return this node
    if not node.sub_nodes:
        return {
            "node": node.to_dict(),
            "path": path,
            "context_snapshot": {
                k: v for k, v in context.items()
                if k in ("mergeable_state", "failed_checks", "bot_escalation",
                         "risk_score", "pr_title")
            },
        }

    # Try sub-nodes
    for sub in node.sub_nodes:
        result = traverse(sub, context, path)
        if result:
            return result

    # No sub-node matched — return this node as the best match
    return {
        "node": node.to_dict(),
        "path": path,
        "context_snapshot": {
            k: v for k, v in context.items()
            if k in ("mergeable_state", "failed_checks", "bot_escalation",
                     "risk_score", "pr_title")
        },
    }


def evaluate_condition(node_id: str, context: dict) -> bool:
    """Evaluate whether a node's condition matches the given context."""
    failed_checks = set(context.get("failed_checks", []))
    mergeable_state = context.get("mergeable_state", "")
    any_pending = context.get("any_required_pending", False)
    bot_escalation = context.get("bot_escalation", False)
    escalation_body = context.get("escalation_body", "").lower()

    conditions = {
        "root": True,
        "dirty": mergeable_state == "dirty",
        "ci_pending": any_pending,
        "ci_failed": bool(failed_checks),
        "supply_chain_failed": "supply-chain" in failed_checks,
        "build_failed": "build" in failed_checks,
        "test_failed": "test" in failed_checks,
        "lint_failed": "lint" in failed_checks,
        "validate_failed": "validate" in failed_checks,
        "opa_failed": "opa-policy" in failed_checks,
        "bot_escalation": bot_escalation,
        "tier3_docker_tag": bot_escalation and any(
            kw in escalation_body for kw in ["does not exist", "invalid tag", "not found"]
        ),
        "tier3_security": bot_escalation and any(
            kw in escalation_body for kw in ["cve-", "security vulnerability"]
        ),
        "tier3_breaking": bot_escalation and "breaking change" in escalation_body,
        "safe_to_merge": (
            not failed_checks
            and not any_pending
            and not bot_escalation
            and mergeable_state not in ("dirty", "blocked")
        ),
    }

    return conditions.get(node_id, False)


def diagnose(context: dict) -> dict:
    """
    Run the full diagnosis decision tree for a PR context.

    Args:
        context: {
            "mergeable_state": str,
            "failed_checks": list[str],
            "any_required_pending": bool,
            "bot_escalation": bool,
            "escalation_body": str,
            "risk_score": int,
            "pr_title": str,
        }

    Returns:
        {
            "node": DiagnosisNode dict,
            "path": list[str],
            "action": str,
            "confidence": str,
            "next_level": str,
            "evidence_required": list[str],
            "explanation": str,
        }
    """
    result = traverse(DECISION_TREE, context)
    if not result:
        return {
            "action": "UNKNOWN",
            "confidence": "low",
            "next_level": "L2",
            "explanation": "No matching condition found in decision tree.",
            "path": ["root"],
        }

    node = result.get("node", {})
    return {
        "action": node.get("action", "UNKNOWN"),
        "confidence": node.get("confidence", "low"),
        "next_level": node.get("next_level", "L2"),
        "evidence_required": node.get("evidence_required", []),
        "explanation": node.get("explanation", ""),
        "path": result.get("path", []),
        "context_snapshot": result.get("context_snapshot", {}),
    }


# ─── CLI ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import json
    import sys

    # Example usage
    test_context = {
        "mergeable_state": "blocked",
        "failed_checks": ["supply-chain"],
        "any_required_pending": False,
        "bot_escalation": False,
        "escalation_body": "",
        "risk_score": 15,
        "pr_title": "chore(deps): bump syft from 0.98 to 0.99",
    }

    result = diagnose(test_context)
    print(json.dumps(result, indent=2))
