# IndestructibleEco — Auto-Repair Architecture

**URI:** `indestructibleeco://docs/auto-repair-architecture`
**Version:** 1.0.0
**Last Updated:** 2025-02-20

---

## Table of Contents

1. [Overview](#overview)
2. [Why AI Cannot Fully Auto-Repair](#why-ai-cannot-fully-auto-repair)
3. [Auto-Repair Engine Architecture](#auto-repair-engine-architecture)
4. [Fix Strategy Registry](#fix-strategy-registry)
5. [CI/CD Integration](#cicd-integration)
6. [Argo CD Self-Healing](#argo-cd-self-healing)
7. [Enterprise Security Tools](#enterprise-security-tools)
8. [Closed-Loop Automation Roadmap](#closed-loop-automation-roadmap)

---

## Overview

The IndestructibleEco Auto-Repair system is a multi-layered defense mechanism that detects, diagnoses, and — where safe — automatically fixes issues in the CI/CD pipeline, Kubernetes manifests, and application configuration. It operates on the principle that automated repair should be applied only when the fix is deterministic, reversible, and cannot introduce new failures.

The system consists of three tiers. The first tier is the CI Validator Engine (`tools/ci-validator/validate.py`), which detects issues across 7 validation categories. The second tier is the Auto-Fix Engine (`tools/ci-validator/auto-fix.py`), which applies deterministic fixes for known patterns. The third tier is Argo CD's self-heal mechanism, which ensures the Kubernetes cluster state always matches the Git-defined state.

---

## Why AI Cannot Fully Auto-Repair

Understanding the boundaries of automated repair is critical for building reliable systems. There are four fundamental categories of limitations that prevent fully autonomous repair, and each requires a different mitigation strategy.

### 1. Context Ambiguity

AI systems operate on pattern matching and statistical inference, but many repair decisions require understanding the developer's intent, the project's architectural constraints, and the deployment environment's specific requirements. Consider a Dockerfile `COPY` instruction that references a path not found in the build context. The correct fix depends on whether the file was moved, renamed, deleted intentionally, or simply not yet created. An AI system cannot distinguish between these cases without additional context.

For example, when `docker/Dockerfile` contains `COPY src/ ./src/` but no `src/` directory exists at the repository root, the AI faces multiple valid interpretations. The directory might need to be created (structural gap), the path might need to be changed to `backend/ai/src/` (wrong reference), or the entire COPY instruction might be obsolete (dead code). Each interpretation leads to a fundamentally different fix, and choosing incorrectly could break the build or introduce subtle runtime errors.

The IndestructibleEco approach to this limitation is the CI Validator Engine, which flags ambiguous issues as warnings rather than errors and provides the Auto-Fix Engine with enough context (file path, line number, build context) to make deterministic fixes only when the correct action is unambiguous.

### 2. Security and Compliance Boundaries

Automated fixes that modify dependencies, update package versions, or change security configurations carry inherent risk. Upgrading a package to fix a vulnerability might introduce breaking API changes, incompatible behavior, or even new vulnerabilities in transitive dependencies. Enterprise environments operating under SOC2, HIPAA, or PCI-DSS compliance frameworks require human review for changes that affect the security posture.

The IndestructibleEco platform enforces this boundary through governance blocks in every `.qyaml` file. Each manifest carries `compliance_tags` (e.g., `zero-trust`, `soc2`) and an `approval_chain` that defines who must review changes. The Auto-Fix Engine respects these boundaries by operating in dry-run mode in CI and requiring explicit human invocation for live fixes.

### 3. Cascading Impact Assessment

A single fix can trigger cascading effects across the system. Renaming a Kubernetes service changes its DNS name, which breaks all services that reference it. Modifying a ConfigMap value might require pod restarts across multiple deployments. Changing a port number in one manifest requires corresponding changes in ingress rules, service definitions, health checks, and monitoring configurations.

The CI Validator's cross-reference integrity checker (Validator 7) partially addresses this by verifying that all file references in configurations point to existing files. However, it cannot predict all runtime interactions. The Auto-Fix Engine therefore limits its scope to single-file fixes and flags multi-file changes for manual review.

### 4. Non-Deterministic Environments

Build environments, container registries, and Kubernetes clusters have state that cannot be fully captured in Git. A Docker build might fail due to a transient network error, a registry rate limit, or a base image update. These failures are not fixable by modifying source code — they require retry logic, infrastructure changes, or waiting for external services to recover.

The CI/CD pipeline handles this through retry policies (5 retries with exponential backoff in Argo CD) and the Auto-Repair workflow, which distinguishes between code-level issues (fixable) and infrastructure issues (retry or escalate).

---

## Auto-Repair Engine Architecture

The Auto-Fix Engine (`tools/ci-validator/auto-fix.py`) implements a three-phase repair cycle that mirrors the project's engineering methodology.

```
┌─────────────────────────────────────────────────────────────┐
│                  Auto-Repair Pipeline                        │
│                                                             │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Validate │───▶│ Classify │───▶│  Apply   │              │
│  │ (detect) │    │ (triage) │    │  (fix)   │              │
│  └──────────┘    └──────────┘    └──────────┘              │
│       │               │               │                     │
│  7 validators    auto_fixable?    fix_strategy              │
│  0+ findings     yes → queue      registered?               │
│                  no → report      yes → execute             │
│                                   no → skip                 │
└─────────────────────────────────────────────────────────────┘
```

**Phase 1 — Validate:** The CI Validator Engine runs all 7 validators against the repository, producing a list of findings. Each finding includes severity (error/warning), file path, line number, message, and metadata flags (`auto_fixable`, `fix_strategy`).

**Phase 2 — Classify:** Findings are partitioned into auto-fixable (have a registered fix strategy) and manual-review (no strategy or strategy explicitly marked as manual). Auto-fixable findings are queued for repair.

**Phase 3 — Apply:** Each auto-fixable finding is dispatched to its registered fix strategy function. The function receives the finding context and the repository path, applies the fix (or simulates it in dry-run mode), and returns a result indicating success or failure with details.

---

## Fix Strategy Registry

The Auto-Fix Engine supports five fix strategies, each handling a specific category of issues.

### 1. path-correction

**Scope:** Dockerfile COPY instructions with incorrect or ambiguous paths.

**Logic:** Adds `./` prefix to COPY source paths that lack explicit relative path notation. This is a safe, deterministic fix because Docker's COPY instruction treats `file.txt` and `./file.txt` identically, but the explicit prefix improves clarity and satisfies the CI Validator's path verification.

**Risk Level:** Low — cosmetic change with no behavioral impact.

### 2. identity-replace

**Scope:** Stale identity references (`superai`, `SUPERAI_`, `superai-platform`) that should be `eco`, `ECO_`, `indestructibleeco`.

**Logic:** Applies a prioritized replacement map (longer patterns first to avoid partial matches). Scans the entire file content and replaces all occurrences.

**Risk Level:** Medium — could affect string literals, comments, or documentation. The CI Validator excludes known safe files (validator itself, rule definitions, auto-fix engine) from identity scanning.

### 3. yaml-syntax

**Scope:** Common YAML syntax issues including tabs (which YAML forbids) and trailing whitespace.

**Logic:** Replaces all tab characters with 2 spaces and strips trailing whitespace from all lines.

**Risk Level:** Low — tabs are always invalid in YAML, and trailing whitespace is universally undesirable.

### 4. governance-block

**Scope:** `.qyaml` files missing one or more of the 4 mandatory governance blocks (`document_metadata`, `governance_info`, `registry_binding`, `vector_alignment_map`).

**Logic:** Generates a complete governance block with auto-generated unique IDs, URIs, and URNs based on the file path. Appends the block to the end of the file as a separate YAML document (after `---` separator).

**Risk Level:** Medium — the auto-generated values are placeholders and should be reviewed. The `generated_by: ci-auto-fix-engine` tag makes these blocks identifiable for later manual refinement.

### 5. schema-field

**Scope:** `skill.json` manifests missing required fields in the governance identity block.

**Logic:** Adds missing `governance.identity.id`, `governance.identity.uri`, and `governance.identity.urn` fields with auto-generated values based on the skill directory name.

**Risk Level:** Low — adds missing required fields without modifying existing data.

---

## CI/CD Integration

The auto-repair system is integrated into the CI/CD pipeline at two levels.

### Gate 5: Auto-Fix (ci.yaml)

The main CI workflow includes a fifth gate that runs only when any of the first four gates fail. It executes the Auto-Fix Engine in dry-run mode, generating a diagnostic report that identifies which issues are auto-fixable and provides the command to apply fixes locally.

This gate does not modify the repository — it only diagnoses. The developer reviews the report, runs `python3 tools/ci-validator/auto-fix.py` locally, verifies the changes, and pushes a fix commit. This preserves the human-in-the-loop for all code changes while minimizing the time to identify and resolve issues.

### Auto-Repair Workflow (auto-repair.yaml)

A separate workflow triggers on CI failure via the `workflow_run` event. It performs deeper diagnostics by running both the CI Validator and Auto-Fix Engine, fetching failed job logs from the GitHub API, and generating a consolidated repair report. This report includes the failure context (commit, branch, run ID), validator findings, auto-fix analysis, and actionable recommendations.

### Local Development

Developers can run both tools locally for immediate feedback:

```bash
# Detect issues
python3 tools/ci-validator/validate.py

# Preview fixes (dry-run)
python3 tools/ci-validator/auto-fix.py --dry-run

# Apply fixes
python3 tools/ci-validator/auto-fix.py

# Generate report
python3 tools/ci-validator/auto-fix.py --report=fix-report.json
```

---

## Argo CD Self-Healing

Argo CD provides a complementary layer of auto-repair at the Kubernetes level. While the CI Auto-Fix Engine operates on source code and configuration files, Argo CD operates on the deployed cluster state.

### How Self-Heal Works

When `selfHeal: true` is enabled in the Argo CD Application sync policy, Argo CD continuously compares the live cluster state against the Git-defined state. If any difference is detected (a manual `kubectl edit`, a pod crash that changes replica count, a ConfigMap modification), Argo CD automatically re-applies the Git state to the cluster.

This mechanism handles several categories of issues that source-level auto-repair cannot address. Configuration drift from manual cluster modifications is automatically corrected. Failed rollouts that leave resources in an inconsistent state are re-synchronized. Accidental deletions of resources defined in Git are automatically recreated.

### Prune Policy

With `prune: true`, Argo CD also handles the reverse case: resources that exist in the cluster but are no longer defined in Git are automatically deleted. This ensures that removing a `.qyaml` file from the repository results in the corresponding Kubernetes resource being cleaned up, preventing orphaned resources.

### Integration with YAML Toolkit

The YAML Toolkit v1 generates `.qyaml` files with governance blocks that Argo CD treats as standard Kubernetes manifests (the governance blocks are YAML documents that Kubernetes ignores). When the toolkit generates new or updated manifests, Argo CD automatically detects the changes and syncs them to the cluster. This creates a fully automated pipeline from YAML generation to cluster deployment.

---

## Enterprise Security Tools

For organizations requiring additional security automation beyond the built-in auto-repair system, several enterprise tools can be integrated.

### GitHub Advanced Security

GitHub's built-in security features include Dependabot for dependency vulnerability scanning and automated PR creation, CodeQL for static analysis, and secret scanning. These tools can be configured to automatically create pull requests that fix known vulnerabilities, which then flow through the standard CI/CD pipeline.

### Snyk Code

Snyk provides deeper vulnerability scanning with auto-fix capabilities. It can be integrated as a GitHub Action or as a standalone scanner in the CI pipeline. Snyk's auto-fix PRs include detailed explanations of the vulnerability, the fix applied, and any potential breaking changes.

### cert-manager

For TLS certificate management in Kubernetes, cert-manager provides fully automated certificate issuance and renewal. When integrated with Argo CD, certificate resources defined in Git are automatically provisioned, and cert-manager handles renewal before expiration without any manual intervention.

### OPA Gatekeeper

Open Policy Agent (OPA) Gatekeeper enforces policy constraints on Kubernetes resources. It can prevent deployments that violate security policies (e.g., running as root, missing resource limits) before they reach the cluster. Combined with Argo CD, this creates a defense-in-depth approach where Git defines the desired state, Argo CD enforces it, and Gatekeeper validates it.

---

## Closed-Loop Automation Roadmap

The current auto-repair system represents the foundation of a progressively more autonomous platform. The roadmap below outlines planned enhancements organized by automation level.

### Level 1: Detect & Report (Current)

The CI Validator Engine detects issues across 7 categories and generates structured reports. The Auto-Fix Engine identifies auto-fixable issues and provides dry-run previews. Argo CD monitors cluster drift and reports sync status. All findings require human review before action.

### Level 2: Detect & Fix (Deterministic)

The Auto-Fix Engine applies deterministic fixes for known patterns (path correction, identity replacement, YAML syntax). Argo CD self-heals cluster drift automatically. GitHub Dependabot creates auto-fix PRs for dependency vulnerabilities. Human review is required only for non-deterministic fixes.

### Level 3: Detect, Fix & Verify (Closed-Loop)

The Auto-Fix Engine applies fixes, re-runs validation, and commits only if all validators pass. The CI pipeline includes a verification gate that confirms fixes don't introduce regressions. Argo CD sync status is monitored and failures trigger automatic rollback. Human review is required only for novel issue types.

### Level 4: Predictive & Preventive (Future)

Static analysis identifies potential issues before they manifest in CI. Dependency update impact analysis predicts breaking changes before upgrading. Resource utilization trends predict scaling needs before capacity is exhausted. Human involvement shifts from reactive repair to proactive architecture decisions.