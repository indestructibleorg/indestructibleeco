# GKE Operations Guide — IndestructibleEco

## Cluster Information

| Cluster | Region | Status | Purpose |
|---------|--------|--------|---------|
| eco-staging | asia-east1 | ✅ RUNNING | Staging environment |
| eco-production | asia-east1 | ❌ DELETED (SSD quota) | Production environment |

## Current Staging Deployment

### Pods (6/6 Running)

- `eco-ai-service` — AI inference service (nginx placeholder)
- `eco-api-gateway` — API gateway (nginx placeholder)
- `eco-api-service` — Express API (nginx placeholder)
- `eco-web-frontend` — Web frontend (nginx placeholder)
- `postgres-0` — PostgreSQL 16 Alpine
- `redis-0` — Redis 7 Alpine

### Resource Configuration (GKE Autopilot Optimized)
All application pods use standardized resources:

- **Requests**: 250m CPU, 512Mi memory, 256Mi ephemeral-storage
- **Limits**: 500m CPU, 1Gi memory, 256Mi ephemeral-storage

### Endpoints

- `http://staging.autoecoops.io` → Web frontend
- `http://api-staging.autoecoops.io` → API gateway
- SSL certificate: Provisioning via GKE ManagedCertificate

### Static IPs

- Staging: `34.102.242.107` (global, `eco-staging-ip`)
- Production: `34.107.200.53` (global, `eco-production-ip`)

---

## Recreate Production Cluster

The production cluster was deleted to free SSD quota (200/250 GB in asia-east1). To recreate:

### Step 1: Request SSD Quota Increase (Recommended)

Before recreating, request a quota increase to avoid the same issue:

```bash
# Via GCP Console:
# 1. Go to IAM & Admin > Quotas
# 2. Filter: Service = Compute Engine, Metric = SSD Total Storage
# 3. Select asia-east1 region
# 4. Click "Edit Quotas" and request 500 GB
```

### Step 2: Recreate the Cluster

```bash
gcloud container clusters create-auto eco-production \
  --region=asia-east1 \
  --project=my-project-ops-1991 \
  --release-channel=regular \
  --network=default \
  --subnetwork=default \
  --enable-master-authorized-networks \
  --master-authorized-networks=0.0.0.0/0 \
  --quiet
```

### Step 3: Deploy Production Manifests

```bash
# Get credentials
gcloud container clusters get-credentials eco-production --region asia-east1

# Apply manifests (strip governance blocks first)
for f in k8s/production/*.qyaml; do
  sed '/^---$/,/^[a-z]/{ /^---$/d; /^[a-z]/!d }' "$f" | \
  sed '/^document_metadata:/,/^[a-z]/d; /^governance_info:/,/^[a-z]/d; /^registry_binding:/,/^[a-z]/d; /^vector_alignment_map:/,/^[a-z]/d' | \
  kubectl apply -f -
done
```

### Step 4: Verify Deployment

```bash
kubectl get pods -n eco-production
kubectl get ingress -n eco-production
kubectl get managedcertificate -n eco-production
```

### Step 5: Re-enable Cloudflare Proxy (After Cert Provisioning)

Once the ManagedCertificate status is `Active`, re-enable Cloudflare proxy for production DNS records.

---

## SSD Quota Management

### Current Usage

- eco-staging: ~100 GB (1 Autopilot node boot disk)
- PVCs: 15 GB (10Gi postgres + 5Gi redis, pd-standard — does NOT count against SSD quota)

### Quota Limits

- SSD_TOTAL_GB: 250 GB in asia-east1
- Each Autopilot node requires ~100 GB SSD boot disk
- Maximum 2 clusters with 1 node each = 200 GB

### Recommendations

1. Request SSD quota increase to 500 GB via GCP Console
2. Consider using a different region with higher default quotas
3. Monitor quota usage: `gcloud compute regions describe asia-east1 --format="json(quotas)"`

---

## Cloudflare DNS Configuration

### Zone: autoecoops.io (ID: 3f10062913fe82ee54594594413c3d68)

| Record | Type | Value | Proxied | Purpose |
|--------|------|-------|---------|---------|
| staging | A | 34.102.242.107 | No (DNS-only) | GKE staging ingress |
| api-staging | A | 34.102.242.107 | No (DNS-only) | GKE staging API |
| production | A | 34.107.200.53 | Yes | GKE production ingress |
| api-production | A | 34.107.200.53 | Yes | GKE production API |
| autoecoops.io | A×4 | 185.199.108-111.153 | No | GitHub Pages |
| www | CNAME | indestructibleorg.github.io | No | GitHub Pages |

**Note**: Staging DNS records are set to DNS-only (not proxied) to allow GKE ManagedCertificate domain verification. Once certificates are active, re-enable Cloudflare proxy.

---

## Service Account

- **Name**: `eco-deploy-sa@my-project-ops-1991.iam.gserviceaccount.com`
- **Roles**: container.admin, compute.admin, iam.serviceAccountUser, storage.admin, artifactregistry.admin, serviceusage.serviceUsageAdmin, owner
- **Key**: Stored in GitHub secret `GCP_SA_KEY`

---

## Troubleshooting

### Pods Stuck in Pending

1. Check node resources: `kubectl describe node <node-name> | grep -A 10 "Allocated"`
2. Check SSD quota: `gcloud compute regions describe asia-east1 --format="json(quotas)" | grep SSD`
3. Check pod events: `kubectl describe pod <pod-name> -n eco-staging`

### Health Check Failures (502)

1. Verify health check path: `gcloud compute health-checks list`
2. Update if needed: `gcloud compute health-checks update http <name> --request-path="/"`
3. Wait 30-60 seconds for backends to become healthy

### ManagedCertificate FailedNotVisible

1. Ensure Cloudflare proxy is disabled (DNS-only) for the domain
2. Verify DNS resolves to GKE static IP: `dig +short <domain>`
3. Delete and recreate the ManagedCertificate
4. Wait 15-60 minutes for provisioning
