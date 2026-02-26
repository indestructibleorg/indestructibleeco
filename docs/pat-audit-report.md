# GitHub PAT Audit Report

**Generated:** 2026-02-26T02:30:00Z
**Auditor:** eco-ops-bot
**Repository:** indestructibleorg/eco-base
**Account:** indestructiblemachinen (GitHub Pro)

---

## 1. Token Inventory

| # | Token ID (Prefix) | Type | Status | Expiry |
|---|-------------------|------|--------|--------|
| 1 | `ghp_g8EtjXwg...` | Classic PAT | **REVOKED** (HTTP 401) | Unknown |
| 2 | `ghp_nXIUZY6v...` | Classic PAT | **REVOKED** (HTTP 401) | Unknown |
| 3 | `github_pat_11B52RIHI...` | Fine-grained PAT | **ACTIVE** | See §4 |

> Classic PATs #1 and #2 returned HTTP 401 during audit. Formally revoke at [github.com/settings/tokens](https://github.com/settings/tokens) if not already done.

---

## 2. Active Token — Permission Detail

**Token:** `github_pat_11B52RIHI0HntIa9MW543j_...` (Fine-grained PAT)
**Owner:** `indestructiblemachinen` | **Plan:** GitHub Pro

### Permissions (inferred from API operations)

| Permission | Level | Evidence |
|------------|-------|----------|
| `contents` | Read + Write | `git push` to `indestructibleorg/eco-base` succeeded |
| `workflows` | Write | `.github/workflows/` files pushed successfully |
| `issues` | Write | GitHub Issue creation in workflow scripts |
| `pull_requests` | Read | PR comment posting in workflow scripts |
| `metadata` | Read | `/user`, `/repos` API calls succeeded |

### Accessible Repositories (confirmed via API)

| Repository | Visibility |
|------------|------------|
| `indestructibleorg/eco-base` | Public |
| `indestructiblemachinen/indestructibleautoops` | Public |
| `indestructiblemachinen/sonarqube-mcp-server` | Public |
| `indestructiblemachinen/pr-agent` | Public |
| `indestructiblemachinen/oauth-test` | **Private** |
| `indestructiblemachinen/indestructibleeco` | Public |
| `indestructiblemachinen/get-gke-credentials` | Public |
| `indestructiblemachinen/circleci-docs` | Public |
| `indestructibleorg/circleci-docs` | Public |
| `indestructiblemachinen/superai-platform` | Public |

---

## 3. Risk Assessment

| Risk | Severity | Finding | Remediation |
|------|----------|---------|-------------|
| Classic PATs not formally revoked | **HIGH** | `ghp_g8EtjXwg...` and `ghp_nXIUZY6v...` may still exist in GitHub settings | Revoke at [github.com/settings/tokens](https://github.com/settings/tokens) |
| PAT shared in plaintext chat | **HIGH** | All 3 tokens transmitted in plaintext | Rotate immediately after task completion |
| No expiry date confirmed | **MEDIUM** | Fine-grained PAT expiry not verified via API | Check [settings/personal-access-tokens](https://github.com/settings/personal-access-tokens) |
| Broad repo access | **LOW** | Token can read 10+ repos | Scope to `indestructibleorg/eco-base` only |
| No rotation schedule | **MEDIUM** | No automated rotation in place | Implement 90-day rotation via `pat-expiry-check.yml` |

---

## 4. Expiry Status

Fine-grained PAT expiry dates are not exposed via GitHub REST API. Verify manually at:
[https://github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)

The `pat-expiry-check.yml` workflow alerts 14 days before expiry using the `PAT_EXPIRY_DATE` secret.

---

## 5. Required Secrets (set in repo Settings → Secrets)

| Secret | Format | Description |
|--------|--------|-------------|
| `PAT_EXPIRY_DATE` | `YYYY-MM-DD` | Expiry date of active fine-grained PAT |
| `PAT_TOKEN_ID` | First 30 chars of token | Token identifier for audit trail |

---

## 6. Immediate Actions Required

1. **Revoke** `ghp_g8EtjXwg...` at [github.com/settings/tokens](https://github.com/settings/tokens)
2. **Revoke** `ghp_nXIUZY6v...` at [github.com/settings/tokens](https://github.com/settings/tokens)
3. **Verify** expiry date of `github_pat_11B52RIHI...` at [github.com/settings/personal-access-tokens](https://github.com/settings/personal-access-tokens)
4. **Set** `PAT_EXPIRY_DATE` secret in `indestructibleorg/eco-base` repo settings
5. **Rotate** `github_pat_11B52RIHI...` within 24 hours (transmitted in plaintext)

---

*This report is generated automatically. Full token values are never stored in this document.*

## §7 GitHub OAuth App 設定記錄

| 欄位 | 值 |
|------|-----|
| Application Name | eco-base-ci |
| App ID | 3420770 |
| Client ID | Ov23liQEBw4D3jc0466G |
| Client Secret | [已加密儲存於 ECO_OAUTH_CLIENT_SECRET] |
| Homepage URL | https://app.autoecoops.io |
| Callback URL | https://api.autoecoops.io/api/oauth/callback |
| Owner | indestructibleorg |
| Created | 2026-02-26 |
| Secret Created By | indestructiblemachinen |
| Secrets Updated | ECO_OAUTH_CLIENT_ID, ECO_OAUTH_CLIENT_SECRET (2026-02-26T09:40:30Z) |
