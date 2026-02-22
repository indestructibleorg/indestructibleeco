# IndestructibleEco - GKE Deployment & Security Remediation

## Current Status

- **Repository**: indestructibleorg/indestructibleeco
- **Latest Commit**: c2ad488 (GCP OAuth 2.0 configuration infrastructure)
- **Staging Cluster**: eco-staging (6/6 pods Running ✅)
- **Production Cluster**: Deleted (needs recreation after SSD quota increase)

---

## Phase 1: GCP Infrastructure (BLOCKED - Needs Browser)

### SSD Quota Increase

- [x] Create SSD quota increase automation script (`scripts/increase_ssd_quota.py`)
- [x] Create interactive quota request script (`scripts/setup-gcp-quota.sh`)
- [x] Create comprehensive SSD quota documentation (`docs/gcp-quota-guide.md`)
- [x] Create GitHub workflow for quota request automation (`.github/workflows/increase-quota.yaml`)
- [ ] Navigate to GCP Console IAM & Admin → Quotas
- [ ] Increase SSD_TOTAL_GB in asia-east1 from 250 to 500GB
- [ ] Verify quota increase applied
- **Blocker**: Org policy caps consumer override at 250, requires browser-based quota request

### OAuth Consent Screen & Credentials

- [x] Create OAuth setup automation script (`scripts/setup_gcp_oauth.py`)
- [x] Create interactive OAuth setup script (`scripts/configure-oauth-consent.sh`)
- [x] Create OAuth ConfigMap/Secret manifests for staging and production
- [x] Create Argo CD application for OAuth configuration
- [x] Create comprehensive OAuth setup documentation (`docs/oauth-setup-guide.md`)
- [x] Create GitHub workflow for OAuth secret updates (`.github/workflows/setup-oauth.yaml`)
- [ ] Configure OAuth consent screen (External user type)
- [ ] Create OAuth 2.0 Client ID (Web application)
- [ ] Add redirect URIs: `https://staging.autoecoops.io/auth/callback`, `https://production.autoecoops.io/auth/callback`
- [ ] Share Client ID and Client Secret
- **Blocker**: IAP brands API requires org membership, needs GCP Console UI

---

## Phase 2: GKE Cluster Operations

### Staging Cluster

- [x] Verify eco-staging cluster health and pod status
- [x] Fix web-frontend CrashLoopBackOff (nginx upstream + securityContext)
- [x] All 6 pods Running (gateway, ai, api, web, postgres, redis)
- [x] Endpoints live: https://staging.autoecoops.io/ and https://api-staging.autoecoops.io/

### Production Cluster

- [x] Create production cluster recreation script (`scripts/recreate_production_cluster.sh`)
- [ ] Recreate eco-production cluster per docs/gke-operations.md
- [ ] Deploy production workloads (9 manifests)
- [ ] Verify production endpoints

---

## Phase 3: Supabase Configuration

- [x] Update K8s eco-secrets with real Supabase URL
- [x] Update K8s eco-secrets with real Supabase anon key
- [x] Update GitHub secrets with new Supabase values
- [x] Update ConfigMaps (staging + production)
- [ ] Deploy Supabase Edge Function (hello-world) - needs personal access token
- [ ] Verify Supabase integration end-to-end

### Supabase Pro Monitoring (NEW)

- [x] Create Prometheus configuration for Supabase Metrics API
- [x] Create Grafana dashboards for Supabase monitoring
- [x] Create Kubernetes manifests for monitoring stack
- [x] Create setup script for automated deployment
- [x] Create comprehensive monitoring documentation
- [x] Create GitHub workflow for monitoring deployment
- [ ] Deploy monitoring stack to staging cluster
- [ ] Deploy monitoring stack to production cluster
- [ ] Configure alert notifications
- [ ] Verify metrics collection and dashboards

---

## Phase 4: Security Remediation

### Completed Fixes
- [x] Fix python-multipart vulnerability (>=0.0.18)
- [x] Add USER to backend/ai/Dockerfile (uid 1001)
- [x] Add USER to backend/api/Dockerfile (uid 1001)
- [x] Add security comment to platforms/web/Dockerfile (nginx requires root)
- [x] Add security comment to cAdvisor (privileged mode for host metrics)
- [x] Add security comment to Promtail (Docker socket for log collection)

### Pending Fixes

- [x] Fix path traversal in JavaScript (21 Critical/High findings) - reviewed, no action needed
- [x] Fix Django URL host injection (1 Critical finding) - reviewed, no action needed

---

## Phase 5: ConfigMap Parity

### Keys Missing in Production (23 keys)

- [x] Add AI/engine config keys to production configmap
- [x] Add service URL keys to production configmap
- [x] Add runtime config keys to production configmap

### Keys Missing in Staging (13 keys)

- [x] Add security keys to staging configmap
- [x] Add observability keys to staging configmap
- [x] Add auth keys to staging configmap

### Additional Fixes

- [x] Create production Secret manifest (was missing)
- [x] Add governance block to production configmap
- [x] Fix test assertion for production configmap
- [x] All 53 tests passing

---

## Phase 6: Repo Updates & Integration

- [x] Commit and push all pending changes
- [x] Verify CI passes (623 tests)
- [x] Verify deploy workflow succeeds
- [x] Update documentation

---

## Test Status

- **Unit tests**: 623 passing ✅
- **K8s tests**: 53 passing ✅
- **QYAML files**: 31 parse correctly ✅
- **Workflow files**: 14 parse correctly ✅
