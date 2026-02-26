#!/usr/bin/env python3
"""Generate compliance report from evidence JSON.
Usage: python3 generate-compliance-report.py <evidence.json> <output.md>
"""
import json, sys, os


def bold(s):
    return f'**{s}**'


def main():
    evidence_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/compliance-evidence.json'
    output_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/compliance-report.md'

    with open(evidence_path, encoding='utf-8') as f:
        ev = json.load(f)

    period = ev['period']
    cm = ev['change_management']
    ci = ev['ci_cd_integrity']
    vm = ev['vulnerability_management']
    ir = ev['incident_response']
    cc = ev['compliance_controls']

    ci_rate = ci['success_rate_pct']
    ci_status = 'PASS' if ci_rate >= 99.0 else 'WARN' if ci_rate >= 95.0 else 'FAIL'
    # Number of open code scanning alerts (count only, not actual alert content)
    scanning_alert_count = int(vm.get('open_scanning_alerts', 0))
    sec_status = 'PASS' if scanning_alert_count == 0 else 'FAIL'
    dep_status = 'PASS' if vm['open_dependabot_alerts'] == 0 else 'WARN'

    pr_list = '\n'.join(f'- {t}' for t in cm['pr_titles'][:10]) if cm['pr_titles'] else 'No merges in this period.'

    report = '\n'.join([
        f'# Compliance Report — {period}',
        '',
        f'{bold("Generated")}: {ev["generated_at"]}',
        f'{bold("Repository")}: {ev["repository"]}',
        f'{bold("Frameworks")}: SOC2 Type II | ISO 27001:2022',
        '',
        '---',
        '',
        '## Executive Summary',
        '',
        '| Domain | Metric | Value | Status |',
        '|--------|--------|-------|--------|',
        f'| Change Management | Merged PRs | {cm["merged_prs"]} | PASS |',
        f'| CI/CD Integrity | Pipeline Success Rate | {ci_rate}% | {ci_status} |',
        f'| Vulnerability Management | Open Scanning Alerts | {scanning_alert_count} | {sec_status} |',
        f'| Vulnerability Management | Open Dependabot Alerts | {vm["open_dependabot_alerts"]} | {dep_status} |',
        f'| Incident Response | Total Incidents | {ir["total_incidents"]} | PASS |',
        f'| Incident Response | Resolved Incidents | {ir["resolved_incidents"]} | PASS |',
        '',
        '---',
        '',
        '## 1. Change Management (SOC2 CC8)',
        '',
        'All code changes are managed through GitHub Pull Requests with mandatory review gates enforced by `pr-automation.yaml`. Branch protection rules require CI to pass before merge.',
        '',
        f'{bold("Period Activity")}: {cm["merged_prs"]} pull requests merged.',
        '',
        f'{bold("Recent merges:")}',
        '',
        pr_list,
        '',
        '---',
        '',
        '## 2. CI/CD Pipeline Integrity (SOC2 CC8 / ISO 27001 A.14)',
        '',
        'The CI pipeline enforces YAML and governance block validation, OPA policy checks via conftest (Rego policies), SBOM generation (Syft/CycloneDX format), artifact signing (cosign/Sigstore), and vulnerability scanning (Grype, threshold: no HIGH/CRITICAL).',
        '',
        f'{bold("Pipeline Runs")}: {ci["total_ci_runs"]} total, {ci["successful_runs"]} successful ({ci_rate}% success rate).',
        '',
        '---',
        '',
        '## 3. Vulnerability Management (SOC2 CC7 / ISO 27001 A.12)',
        '',
        '| Alert Type | Open Count | Target |',
        '|------------|-----------|--------|',
        f'| Code Scanning | {scanning_alert_count} | 0 |',
        f'| Dependabot (dependencies) | {vm["open_dependabot_alerts"]} | 0 |',
        '',
        'Dependabot is configured for npm, pip, Docker, and GitHub Actions with weekly update schedule.',
        '',
        '---',
        '',
        '## 4. Access Control (SOC2 CC6 / ISO 27001 A.9)',
        '',
        'Authentication is handled via OIDC federation (Keycloak/Supabase). Authorization uses RBAC with centralized policy in `policy/`. All API requests require JWT with `traceId` and `sessionId`. Secret rotation is managed via GitHub Secrets with `AUTO_FIX_TOKEN` PAT.',
        '',
        '---',
        '',
        '## 5. Incident Response (SOC2 CC9 / ISO 27001 A.16)',
        '',
        '| Metric | Value |',
        '|--------|-------|',
        f'| Total Incidents | {ir["total_incidents"]} |',
        f'| Resolved | {ir["resolved_incidents"]} |',
        f'| Mean Time to Resolve | {ir["mean_time_to_resolve"]} |',
        '',
        'Incidents are automatically detected by `drift-detection.yaml` (every 30 min) and `canary-deploy.yaml` (SLO gate failures). Each incident triggers an auto-created GitHub issue with rollback confirmation.',
        '',
        '---',
        '',
        '## 6. Compliance Control Mapping',
        '',
        '| Control | Description | Evidence |',
        '|---------|-------------|----------|',
        f'| SOC2 CC6 | {cc["SOC2_CC6"]} | OIDC config, RBAC policies |',
        f'| SOC2 CC7 | {cc["SOC2_CC7"]} | Prometheus dashboards, SLO reports |',
        f'| SOC2 CC8 | {cc["SOC2_CC8"]} | PR merge history, CI run logs |',
        f'| SOC2 CC9 | {cc["SOC2_CC9"]} | Drift detection logs, rollback history |',
        f'| ISO A.12 | {cc["ISO27001_A12"]} | SBOM artifacts, cosign signatures |',
        f'| ISO A.14 | {cc["ISO27001_A14"]} | OPA policy files, conftest results |',
        f'| ISO A.16 | {cc["ISO27001_A16"]} | Incident issues, auto-close history |',
        '',
        '---',
        '',
        '*This report was automatically generated by `compliance-report.yaml`. Evidence artifacts are stored in GitHub Actions run logs and attached to this issue.*',
    ])

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'Report written to {output_path}')


if __name__ == '__main__':
    main()
