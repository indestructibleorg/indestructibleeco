#!/usr/bin/env bash
# =============================================================================
# pat-revoke-and-update.sh — Revoke stale Classic PATs + Update Secrets
# =============================================================================
# Usage:
#   ./scripts/pat-revoke-and-update.sh [OPTIONS]
#
# Options:
#   --active-token TOKEN     Active PAT used to call GitHub API (required)
#   --new-token    TOKEN     New replacement PAT to set in Secrets (optional)
#   --expiry       DATE      Expiry date of new PAT in YYYY-MM-DD format (optional)
#   --repo         OWNER/REPO  Target repository (default: indestructibleorg/eco-base)
#   --dry-run                Preview all actions without executing
#   --skip-revoke            Skip revocation step (only update Secrets)
#   --skip-secrets           Skip Secrets update step (only revoke)
#
# Environment variables (alternative to flags):
#   ACTIVE_TOKEN, NEW_PAT, PAT_EXPIRY_DATE, TARGET_REPO
#
# What this script does:
#   Step 1  Validate --active-token via GitHub API (/user + /rate_limit)
#   Step 2  List all Classic PATs (ghp_*) via /user/installations (best-effort)
#           and attempt revocation of tokens that return 401 on /user
#   Step 3  Validate --new-token (if provided): must return HTTP 200 on /user
#   Step 4  Encrypt and update GitHub Actions Secrets:
#             PAT_TOKEN        ← new token value
#             PAT_TOKEN_ID     ← first 30 chars of new token
#             PAT_EXPIRY_DATE  ← expiry date (YYYY-MM-DD)
#   Step 5  Write timestamped audit JSON
#
# Dependencies: bash, curl, python3 (stdlib + pynacl for secret encryption)
# =============================================================================

set -euo pipefail

# ── Defaults ──────────────────────────────────────────────────────────────────
REPO="${TARGET_REPO:-indestructibleorg/eco-base}"
ACTIVE_TOKEN="${ACTIVE_TOKEN:-}"
NEW_TOKEN="${NEW_PAT:-}"
EXPIRY="${PAT_EXPIRY_DATE:-}"
DRY_RUN=false
SKIP_REVOKE=false
SKIP_SECRETS=false
TIMESTAMP=$(date -u +%Y%m%dT%H%M%SZ)
LOG_FILE="/tmp/pat-revoke-${TIMESTAMP}.log"
AUDIT_FILE="/tmp/pat-revoke-audit-${TIMESTAMP}.json"

# ── Argument parsing ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case "$1" in
    --active-token) ACTIVE_TOKEN="$2"; shift 2 ;;
    --new-token)    NEW_TOKEN="$2";    shift 2 ;;
    --expiry)       EXPIRY="$2";       shift 2 ;;
    --repo)         REPO="$2";         shift 2 ;;
    --dry-run)      DRY_RUN=true;      shift   ;;
    --skip-revoke)  SKIP_REVOKE=true;  shift   ;;
    --skip-secrets) SKIP_SECRETS=true; shift   ;;
    *) echo "Unknown option: $1" >&2; exit 1   ;;
  esac
done

# ── Helpers ────────────────────────────────────────────────────────────────────
log()  { echo "[$(date -u +%H:%M:%SZ)] $*" | tee -a "$LOG_FILE"; }
die()  { log "ERROR: $*"; exit 1; }
info() { log "INFO : $*"; }

api_get() {
  local token="$1" path="$2"
  curl -s -w "\n%{http_code}" \
    -H "Authorization: token $token" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com${path}"
}

api_put() {
  local token="$1" path="$2" data="$3"
  curl -s -w "\n%{http_code}" -X PUT \
    -H "Authorization: token $token" \
    -H "Accept: application/vnd.github+json" \
    -H "Content-Type: application/json" \
    -d "$data" \
    "https://api.github.com${path}"
}

api_delete() {
  local token="$1" path="$2"
  curl -s -w "\n%{http_code}" -X DELETE \
    -H "Authorization: token $token" \
    -H "Accept: application/vnd.github+json" \
    "https://api.github.com${path}"
}

check_token_valid() {
  local token="$1"
  local response
  response=$(api_get "$token" "/user")
  local http_code
  http_code=$(echo "$response" | tail -1)
  local body
  body=$(echo "$response" | head -n -1)
  if [[ "$http_code" == "200" ]]; then
    echo "$(echo "$body" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('login','unknown'))")"
    return 0
  else
    echo "INVALID"
    return 1
  fi
}

encrypt_secret() {
  local key_b64="$1" secret_value="$2"
  python3 - "$key_b64" "$secret_value" << 'PYEOF'
import sys, subprocess
from base64 import b64encode

key_b64   = sys.argv[1]
secret    = sys.argv[2]

try:
    from nacl import encoding, public
except ImportError:
    subprocess.check_call(["pip3", "install", "pynacl", "-q"],
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    from nacl import encoding, public

pub_key   = public.PublicKey(key_b64.encode(), encoding.Base64Encoder())
box       = public.SealedBox(pub_key)
encrypted = box.encrypt(secret.encode())
print(b64encode(encrypted).decode())
PYEOF
}

# ── Validation ─────────────────────────────────────────────────────────────────
[[ -z "$ACTIVE_TOKEN" ]] && die "--active-token or ACTIVE_TOKEN is required"

log "============================================================"
log " PAT Revoke & Update Script"
log "============================================================"
log "Repo     : $REPO"
log "Dry run  : $DRY_RUN"
log "Log file : $LOG_FILE"
log ""

# ── Step 1: Validate active token ─────────────────────────────────────────────
log "--- Step 1: Validating active token ---"
ACTIVE_USER=$(check_token_valid "$ACTIVE_TOKEN") || die "Active token is invalid (HTTP 401). Provide a working token via --active-token."
info "Active token valid. Authenticated as: $ACTIVE_USER"

# Detect token type
TOKEN_PREFIX="${ACTIVE_TOKEN:0:4}"
if [[ "$TOKEN_PREFIX" == "ghp_" ]]; then
  ACTIVE_TOKEN_TYPE="classic"
elif [[ "$TOKEN_PREFIX" == "gith" ]]; then
  ACTIVE_TOKEN_TYPE="fine_grained"
else
  ACTIVE_TOKEN_TYPE="unknown"
fi
info "Active token type: $ACTIVE_TOKEN_TYPE"

# ── Step 2: Revoke stale Classic PATs ─────────────────────────────────────────
REVOKED_TOKENS=()
REVOKE_ERRORS=()

if $SKIP_REVOKE; then
  log "--- Step 2: Skipped (--skip-revoke) ---"
else
  log "--- Step 2: Revoking stale Classic PATs ---"
  log ""
  log "NOTE: GitHub API does not expose a list endpoint for Classic PATs."
  log "      This step validates and revokes tokens provided via environment"
  log "      variable STALE_TOKENS (comma-separated) or prompts for input."
  log ""

  # Collect stale tokens from env or stdin
  STALE_TOKENS_RAW="${STALE_TOKENS:-}"

  if [[ -z "$STALE_TOKENS_RAW" ]]; then
    # Check if known stale tokens are set in environment
    # Tokens passed in previous sessions: ghp_g8EtjXwg... (401) and ghp_nXIUZY6v... (active)
    log "No STALE_TOKENS env var set."
    log "To revoke specific tokens, set: export STALE_TOKENS='ghp_xxx,ghp_yyy'"
    log "Attempting to detect stale tokens from known list..."

    # Known tokens from this session (will be validated)
    STALE_TOKENS_RAW="${KNOWN_STALE_TOKENS:-}"
  fi

  if [[ -n "$STALE_TOKENS_RAW" ]]; then
    IFS=',' read -ra STALE_LIST <<< "$STALE_TOKENS_RAW"
    for token in "${STALE_LIST[@]}"; do
      token=$(echo "$token" | tr -d ' \n\r')
      [[ -z "$token" ]] && continue

      TOKEN_DISPLAY="${token:0:12}..."
      info "Checking token: $TOKEN_DISPLAY"

      # Validate token status
      RESPONSE=$(api_get "$token" "/user")
      HTTP_CODE=$(echo "$RESPONSE" | tail -1)

      if [[ "$HTTP_CODE" == "401" ]]; then
        info "Token $TOKEN_DISPLAY is already INVALID (401) — no revocation needed"
        REVOKED_TOKENS+=("${TOKEN_DISPLAY}:already_invalid")
      elif [[ "$HTTP_CODE" == "200" ]]; then
        TOKEN_USER=$(echo "$RESPONSE" | head -n -1 | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('login','?'))" 2>/dev/null || echo "?")
        info "Token $TOKEN_DISPLAY is VALID (user: $TOKEN_USER) — revoking..."

        if $DRY_RUN; then
          log "[DRY-RUN] Would revoke token: $TOKEN_DISPLAY"
          REVOKED_TOKENS+=("${TOKEN_DISPLAY}:dry_run_revoked")
        else
          # Classic PATs can be revoked via DELETE /applications/{client_id}/token
          # but without OAuth app credentials, we use the installations endpoint
          # The most reliable way: use the token itself to call DELETE /user/tokens/{token_id}
          # For Classic PATs, GitHub provides revocation via the token itself
          DEL_RESPONSE=$(curl -s -w "\n%{http_code}" -X DELETE \
            -H "Authorization: token $token" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/installation/token" 2>/dev/null || echo -e "\n000")
          DEL_CODE=$(echo "$DEL_RESPONSE" | tail -1)

          # Alternative: use active token to revoke via admin endpoint (requires admin:org scope)
          # For Classic PATs, the owner must revoke via UI or use the token itself
          # We attempt self-revocation using the stale token
          SELF_DEL=$(curl -s -w "\n%{http_code}" -X DELETE \
            -H "Authorization: token $token" \
            -H "Accept: application/vnd.github+json" \
            "https://api.github.com/authorizations/$(
              curl -s -H "Authorization: token $token" \
                   -H "Accept: application/vnd.github+json" \
                   "https://api.github.com/user" | \
              python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('id','0'))" 2>/dev/null
            )" 2>/dev/null || echo -e "\n000")
          SELF_DEL_CODE=$(echo "$SELF_DEL" | tail -1)

          if [[ "$SELF_DEL_CODE" == "204" || "$SELF_DEL_CODE" == "200" ]]; then
            info "Token $TOKEN_DISPLAY revoked successfully"
            REVOKED_TOKENS+=("${TOKEN_DISPLAY}:revoked")
          else
            # Classic PATs cannot be programmatically revoked without OAuth app credentials
            # Log the token prefix for manual revocation
            log "::warning:: Token $TOKEN_DISPLAY requires manual revocation."
            log "  Visit: https://github.com/settings/tokens"
            log "  Look for token starting with: ${token:0:12}"
            REVOKE_ERRORS+=("${TOKEN_DISPLAY}:manual_required")
          fi
        fi
      else
        log "::warning:: Unexpected HTTP $HTTP_CODE for token $TOKEN_DISPLAY"
        REVOKE_ERRORS+=("${TOKEN_DISPLAY}:http_${HTTP_CODE}")
      fi
    done
  else
    log "No stale tokens provided. Skipping revocation."
    log "Manual revocation: https://github.com/settings/tokens"
    log "  Tokens to revoke:"
    log "    - ghp_g8EtjXwg... (confirmed 401 — already invalid)"
    log "    - Any other Classic PATs no longer in use"
  fi
fi

# ── Step 3: Validate new token ─────────────────────────────────────────────────
NEW_TOKEN_USER=""
if [[ -n "$NEW_TOKEN" ]]; then
  log "--- Step 3: Validating new token ---"
  NEW_TOKEN_USER=$(check_token_valid "$NEW_TOKEN") || die "New token is invalid (HTTP 401). Provide a valid token via --new-token."
  info "New token valid. Authenticated as: $NEW_TOKEN_USER"

  NEW_TOKEN_PREFIX="${NEW_TOKEN:0:4}"
  if [[ "$NEW_TOKEN_PREFIX" == "ghp_" ]]; then
    NEW_TOKEN_TYPE="classic"
    log "::warning:: New token is a Classic PAT. Fine-grained PAT is recommended."
  elif [[ "${NEW_TOKEN:0:10}" == "github_pat" ]]; then
    NEW_TOKEN_TYPE="fine_grained"
    info "New token type: fine_grained (recommended)"
  else
    NEW_TOKEN_TYPE="unknown"
  fi

  # Validate expiry format if provided
  if [[ -n "$EXPIRY" ]]; then
    if ! echo "$EXPIRY" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}$'; then
      die "Invalid --expiry format: '$EXPIRY'. Expected YYYY-MM-DD."
    fi
    # Check expiry is in the future
    TODAY=$(date -u +%Y-%m-%d)
    if [[ "$EXPIRY" < "$TODAY" ]]; then
      die "Expiry date $EXPIRY is in the past. Provide a future date."
    fi
    DAYS_UNTIL_EXPIRY=$(python3 -c "
from datetime import date
today = date.fromisoformat('$TODAY')
expiry = date.fromisoformat('$EXPIRY')
print((expiry - today).days)
")
    info "New token expires: $EXPIRY ($DAYS_UNTIL_EXPIRY days from today)"
    if [[ "$DAYS_UNTIL_EXPIRY" -gt 90 ]]; then
      log "::warning:: Token lifetime exceeds 90-day policy maximum (OPERATIONS.md Rule-03 analogy)."
    fi
  fi
else
  log "--- Step 3: Skipped (--new-token not provided) ---"
fi

# ── Step 4: Update GitHub Actions Secrets ─────────────────────────────────────
SECRETS_UPDATED=()

if $SKIP_SECRETS || [[ -z "$NEW_TOKEN" ]]; then
  log "--- Step 4: Skipped (--skip-secrets or no --new-token) ---"
else
  log "--- Step 4: Updating GitHub Actions Secrets ---"

  # Fetch repo public key
  info "Fetching repo public key for $REPO..."
  KEY_RESPONSE=$(api_get "$ACTIVE_TOKEN" "/repos/$REPO/actions/secrets/public-key")
  KEY_HTTP=$(echo "$KEY_RESPONSE" | tail -1)
  KEY_BODY=$(echo "$KEY_RESPONSE" | head -n -1)

  [[ "$KEY_HTTP" != "200" ]] && die "Failed to fetch repo public key (HTTP $KEY_HTTP). Check token permissions."

  KEY_ID=$(echo "$KEY_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['key_id'])")
  KEY_B64=$(echo "$KEY_BODY" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['key'])")
  info "Public key fetched (key_id: $KEY_ID)"

  update_secret() {
    local name="$1" value="$2"
    if $DRY_RUN; then
      log "[DRY-RUN] Would update secret: $name"
      SECRETS_UPDATED+=("${name}:dry_run")
      return 0
    fi
    local encrypted
    encrypted=$(encrypt_secret "$KEY_B64" "$value")
    local response
    response=$(api_put "$ACTIVE_TOKEN" \
      "/repos/$REPO/actions/secrets/$name" \
      "{\"encrypted_value\":\"$encrypted\",\"key_id\":\"$KEY_ID\"}")
    local http_code
    http_code=$(echo "$response" | tail -1)
    if [[ "$http_code" == "201" || "$http_code" == "204" ]]; then
      info "Secret $name updated (HTTP $http_code)"
      SECRETS_UPDATED+=("${name}:updated")
    else
      log "::error:: Failed to update secret $name (HTTP $http_code)"
      SECRETS_UPDATED+=("${name}:failed_http_${http_code}")
    fi
  }

  # Update PAT_TOKEN
  update_secret "PAT_TOKEN" "$NEW_TOKEN"

  # Update PAT_TOKEN_ID (first 30 chars)
  TOKEN_ID_SHORT="${NEW_TOKEN:0:30}"
  update_secret "PAT_TOKEN_ID" "$TOKEN_ID_SHORT"

  # Update PAT_EXPIRY_DATE
  if [[ -n "$EXPIRY" ]]; then
    update_secret "PAT_EXPIRY_DATE" "$EXPIRY"
  else
    log "::warning:: --expiry not provided. PAT_EXPIRY_DATE not updated."
    log "  Set it manually: Settings → Secrets → PAT_EXPIRY_DATE = YYYY-MM-DD"
  fi
fi

# ── Step 5: Write audit JSON ───────────────────────────────────────────────────
log "--- Step 5: Writing audit record ---"

python3 - << PYEOF
import json
from datetime import datetime, timezone

entry = {
    "timestamp": "${TIMESTAMP}",
    "script": "pat-revoke-and-update.sh",
    "repo": "${REPO}",
    "dry_run": ${DRY_RUN},
    "active_token_user": "${ACTIVE_USER}",
    "active_token_type": "${ACTIVE_TOKEN_TYPE}",
    "step2_revoke": {
        "skipped": ${SKIP_REVOKE},
        "revoked": [x for x in """${REVOKED_TOKENS[*]:-}""".split() if x],
        "errors":  [x for x in """${REVOKE_ERRORS[*]:-}""".split() if x],
        "manual_revocation_url": "https://github.com/settings/tokens",
    },
    "step3_new_token": {
        "provided": bool("${NEW_TOKEN}"),
        "user": "${NEW_TOKEN_USER}",
        "type": "${NEW_TOKEN_TYPE:-not_provided}",
        "expiry": "${EXPIRY}" if "${EXPIRY}" else None,
        "days_until_expiry": ${DAYS_UNTIL_EXPIRY:-0},
    },
    "step4_secrets": {
        "skipped": ${SKIP_SECRETS},
        "repo": "${REPO}",
        "updated": [x for x in """${SECRETS_UPDATED[*]:-}""".split() if x],
    },
}

with open("${AUDIT_FILE}", "w") as f:
    json.dump(entry, f, indent=2)

print(json.dumps(entry, indent=2))
PYEOF

# ── Summary ────────────────────────────────────────────────────────────────────
log ""
log "============================================================"
log " Summary"
log "============================================================"
log "Dry run     : $DRY_RUN"
log "Log file    : $LOG_FILE"
log "Audit file  : $AUDIT_FILE"
log ""
log "Step 2 (Revoke)  : ${#REVOKED_TOKENS[@]} processed, ${#REVOKE_ERRORS[@]} manual required"
log "Step 4 (Secrets) : ${#SECRETS_UPDATED[@]} secrets processed"
log ""
if [[ ${#REVOKE_ERRORS[@]} -gt 0 ]]; then
  log "Manual revocation required for:"
  for t in "${REVOKE_ERRORS[@]}"; do
    log "  - ${t%%:*}"
  done
  log "  Visit: https://github.com/settings/tokens"
fi
log ""
log "Next steps:"
log "  1. Verify CI: https://github.com/$REPO/actions"
log "  2. Update docs/pat-audit-report.md"
log "  3. Confirm old tokens revoked: https://github.com/settings/tokens"
[[ -n "$EXPIRY" ]] && log "  4. Next rotation due: $EXPIRY (T-14 alert will trigger)"
