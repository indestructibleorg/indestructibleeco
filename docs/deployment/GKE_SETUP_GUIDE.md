# GKE Autopilot Setup Guide for Ecosystem v1.0

## Cluster Configuration

### Staging Cluster: eco-staging
- **Region**: asia-east1 (Taiwan)
- **Type**: GKE Autopilot
- **Status**: Provisioning...

### Production Cluster: eco-production
- **Region**: asia-east1 (Taiwan)
- **Type**: GKE Autopilot
- **Status**: To be created

---

## Generating Kubeconfig Files

Once both clusters are Running, generate the kubeconfig files:

### For Staging Cluster:
```bash
# Get credentials for staging cluster
gcloud container clusters get-credentials eco-staging --region asia-east1 --project <your-project-id>

# Export to base64 (works on both Linux and macOS)
cat ~/.kube/config | base64 | tr -d '\n' > kubeconfig-staging-base64.txt
```

### For Production Cluster:
```bash
# Get credentials for production cluster
gcloud container clusters get-credentials eco-production --region asia-east1 --project <your-project-id>

# Export to base64 (works on both Linux and macOS)
cat ~/.kube/config | base64 | tr -d '\n' > kubeconfig-production-base64.txt
```

### Important Notes:
- Run these commands **separately** for each cluster
- The kubeconfig file will be updated each time you run `get-credentials`
- You may need to merge kubeconfigs if you want to access both clusters simultaneously

---

## Merging Multiple Kubeconfigs (Optional)

If you want to access both clusters from a single kubeconfig:

```bash
# Export staging config
gcloud container clusters get-credentials eco-staging --region asia-east1 --project <your-project-id>
cp ~/.kube/config config-staging

# Export production config
gcloud container clusters get-credentials eco-production --region asia-east1 --project <your-project-id>
cp ~/.kube/config config-production

# Merge configs
KUBECONFIG=config-staging:config-production kubectl config view --flatten > merged-config

# Use merged config
export KUBECONFIG=merged-config

# Verify contexts
kubectl config get-contexts
```

---

## GKE Autopilot Benefits

✅ **Serverless Experience**: No node management required
✅ **Automatic Scaling**: Pods scale based on resource needs
✅ **Security Best Practices**: Secure by default
✅ **Cost Optimization**: Pay only for what you use
✅ **Regional Deployment**: asia-east1 for Taiwan region
✅ **Managed Updates**: Google manages control plane

---

## Estimated Costs

### Staging Cluster
- With minimal traffic: ~$30-50/month
- Scaling: Based on actual usage

### Production Cluster
- With moderate traffic: ~$100-200/month
- Scaling: Based on actual usage

### Cost Optimization Tips:
1. Use horizontal pod autoscaling (HPA)
2. Set appropriate resource requests and limits
3. Monitor usage regularly
4. Consider spot/preemptible VMs for non-critical workloads

---

## Post-Cluster Setup Steps

Once clusters are Running and kubeconfigs are provided:

### 1. Create Namespaces

First, create the namespaces for staging and production:

```bash
# Staging
kubectl create namespace ecosystem-staging --context=gke_<project-id>_asia-east1_eco-staging

# Production
kubectl create namespace ecosystem-production --context=gke_<project-id>_asia-east1_eco-production
```

### 2. Add GitHub Secrets

**⚠️ Security Note**: For production environments, prefer using GitHub OIDC with GCP Workload Identity Federation instead of storing long-lived kubeconfig files. This provides short-lived credentials with better security. See the [Workload Identity Federation Guide](https://github.com/google-github-actions/auth#setup) for setup instructions.

**For development/testing**, you can use base64-encoded kubeconfigs:
- `KUBE_CONFIG_STAGING`: Base64 staging kubeconfig (least-privilege service account)
- `KUBE_CONFIG_PRODUCTION`: Base64 production kubeconfig (least-privilege service account)

**Recommended**: Create dedicated service accounts with minimal required permissions:
```bash
# Create a deployment service account with limited permissions
kubectl create serviceaccount github-deployer -n ecosystem-staging
kubectl create rolebinding github-deployer-binding \
  --clusterrole=edit \
  --serviceaccount=ecosystem-staging:github-deployer \
  --namespace=ecosystem-staging
```

### 3. Verify Cluster Access
```bash
# Test staging access
kubectl get nodes --context=gke_<project-id>_asia-east1_eco-staging

# Test production access
kubectl get nodes --context=gke_<project-id>_asia-east1_eco-production
```

### 4. Verify Namespaces
```bash
# Verify namespaces were created successfully
kubectl get namespace ecosystem-staging --context=gke_<project-id>_asia-east1_eco-staging
kubectl get namespace ecosystem-production --context=gke_<project-id>_asia-east1_eco-production
```

### 5. Deploy to Staging
- Push changes to main branch
- CI/CD pipeline will automatically deploy to staging
- Monitor deployment health

### 6. Deploy to Production
- Manual approval in GitHub Actions
- Deploy to production namespace
- Verify production deployment

---

## DNS Configuration

You'll need to configure DNS records for your domains:

### Required DNS Records:
```
# Frontend
ecosystem.machops.io → Load Balancer IP

# API
api.ecosystem.machops.io → Load Balancer IP

# Optional: Subdomains for staging
staging.ecosystem.machops.io → Staging Load Balancer IP
api-staging.ecosystem.machops.io → Staging Load Balancer IP
```

### DNS Setup Steps:
1. Get Load Balancer IP after deployment:
   ```bash
   kubectl get svc -n ecosystem-staging
   kubectl get svc -n ecosystem-production
   ```

2. Add A records in your DNS provider
3. Verify DNS propagation:
   ```bash
   dig ecosystem.machops.io
   dig api.ecosystem.machops.io
   ```

---

## SSL Certificates

### Option 1: Let's Encrypt (Recommended)
Free, automatic certificate renewal using cert-manager:

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
# Replace 'your-email@example.com' with your actual email address
cat << 'EOF' | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Option 2: Google Managed Certificates
Google Cloud SSL certificate management.

Save the following to a file (e.g., `managed-cert.yaml`) and apply it with: `kubectl apply -f managed-cert.yaml`

```yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: ecosystem-cert
  namespace: ecosystem-production
spec:
  domains:
    - ecosystem.machops.io
    - api.ecosystem.machops.io
```

After creating the ManagedCertificate, reference it in your Ingress annotation:
```yaml
metadata:
  annotations:
    networking.gke.io/managed-certificates: ecosystem-cert
```

---

## Monitoring and Logging

GKE Autopilot integrates with:
- **Cloud Monitoring**: Metrics and dashboards
- **Cloud Logging**: Log aggregation and analysis
- **Cloud Trace**: Distributed tracing
- **Error Reporting**: Error tracking

Additional monitoring options include:
- Prometheus + Grafana (custom monitoring)
- Loki for centralized logging
- Custom dashboards for your ecosystem

---

## Security Best Practices

### Recommended: GitHub OIDC + Workload Identity Federation

For production deployments, use GitHub's OIDC provider with GCP Workload Identity Federation to avoid storing long-lived credentials.

#### Step 1: Set up Workload Identity Federation on GCP

```bash
# Set your GCP project ID
export PROJECT_ID="your-project-id"
export PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
export GITHUB_REPO="machops/ecosystem"

# Create a Workload Identity Pool
gcloud iam workload-identity-pools create "github-pool" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --display-name="GitHub Actions Pool"

# Create a Workload Identity Provider
gcloud iam workload-identity-pools providers create-oidc "github-provider" \
  --project="${PROJECT_ID}" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub Provider" \
  --attribute-mapping="google.subject=assertion.sub,attribute.actor=assertion.actor,attribute.repository=assertion.repository" \
  --issuer-uri="https://token.actions.githubusercontent.com"

# Create a service account for GitHub Actions
gcloud iam service-accounts create github-actions \
  --project="${PROJECT_ID}" \
  --display-name="GitHub Actions Deployer"

# Grant necessary permissions to the service account
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/container.developer"

# Allow the GitHub repository to impersonate the service account
gcloud iam service-accounts add-iam-policy-binding "github-actions@${PROJECT_ID}.iam.gserviceaccount.com" \
  --project="${PROJECT_ID}" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/attribute.repository/${GITHUB_REPO}"

# Get the Workload Identity Provider resource name (save this for GitHub Actions)
echo "projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
```

#### Step 2: Configure GitHub Actions workflow

```yaml
# In your GitHub Actions workflow:
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider'
    service_account: 'github-actions@PROJECT_ID.iam.gserviceaccount.com'

- name: Get GKE credentials
  uses: google-github-actions/get-gke-credentials@v2
  with:
    cluster_name: eco-production
    location: asia-east1
```

**Benefits:**
- No long-lived credentials stored in GitHub
- Automatic credential rotation
- Fine-grained IAM permissions
- Audit trail in GCP logs

### Alternative: Least-Privilege Service Accounts

If using kubeconfig files, create dedicated service accounts with minimal permissions:

```bash
# Create namespace-scoped service account
kubectl create serviceaccount github-deployer -n ecosystem-production

# Grant only necessary permissions (edit role scoped to namespace)
kubectl create rolebinding github-deployer-binding \
  --clusterrole=edit \
  --serviceaccount=ecosystem-production:github-deployer \
  --namespace=ecosystem-production

# For Kubernetes 1.24+, create a long-lived service account token manually
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Secret
metadata:
  name: github-deployer-token
  namespace: ecosystem-production
  annotations:
    kubernetes.io/service-account.name: github-deployer
type: kubernetes.io/service-account-token
EOF

# Wait for the token to be populated (typically takes a few seconds)
echo "Waiting for token to be populated..."
for i in {1..30}; do
  TOKEN_CHECK=$(kubectl get secret github-deployer-token -n ecosystem-production -o jsonpath='{.data.token}' 2>/dev/null)
  if [ -n "$TOKEN_CHECK" ]; then
    echo "Token ready!"
    break
  fi
  sleep 1
done

# Get the service account token (decode base64 in a cross-platform way)
# Note: base64 flags differ between GNU (Linux) and BSD (macOS)
ENCODED_TOKEN=$(kubectl get secret github-deployer-token \
  -n ecosystem-production \
  -o jsonpath='{.data.token}')

# Try Linux/GNU base64 first, then macOS/BSD base64
if SA_TOKEN=$(echo "$ENCODED_TOKEN" | base64 -d 2>/dev/null) && [ -n "$SA_TOKEN" ]; then
  true  # Successfully decoded with -d flag (Linux/GNU)
elif SA_TOKEN=$(echo "$ENCODED_TOKEN" | base64 -D 2>/dev/null) && [ -n "$SA_TOKEN" ]; then
  true  # Successfully decoded with -D flag (macOS/BSD)
else
  echo "Error: Failed to decode service account token with both 'base64 -d' and 'base64 -D'."
  echo "Please verify that:"
  echo "  1. The github-deployer-token secret exists in the ecosystem-production namespace"
  echo "  2. The base64 command is available on your system"
  exit 1
fi

# Alternative: Use kubectl create token for short-lived tokens (valid for 1 hour by default)
# For longer validity, adjust duration as needed (e.g., --duration=168h for 7 days)
# SA_TOKEN=$(kubectl create token github-deployer -n ecosystem-production --duration=1h)

# Get the API server URL and CA data for the eco-production cluster
# Note: The actual cluster name in kubeconfig is typically gke_<project-id>_asia-east1_eco-production
# JSONPath doesn't support wildcards, so we list all clusters and grep for the match
# Use grep with end-of-line anchor to ensure exact matching of the cluster name suffix
CLUSTER_NAME=$(kubectl config view --raw -o jsonpath='{.clusters[*].name}' | tr ' ' '\n' | grep 'eco-production$' | head -n1)

# Validate that the cluster name was found
if [ -z "$CLUSTER_NAME" ]; then
  echo "Error: Could not find a cluster matching 'eco-production' in your kubeconfig."
  echo "Available clusters:"
  kubectl config view --raw -o jsonpath='{.clusters[*].name}' | tr ' ' '\n'
  echo ""
  echo "Please verify that:"
  echo "  1. You have run 'gcloud container clusters get-credentials' for the eco-production cluster"
  echo "  2. Your current kubeconfig contains the correct cluster configuration"
  exit 1
fi

CLUSTER_SERVER=$(kubectl config view --raw \
  -o jsonpath="{.clusters[?(@.name==\"${CLUSTER_NAME}\")].cluster.server}")
CLUSTER_CA_DATA=$(kubectl config view --raw \
  -o jsonpath="{.clusters[?(@.name==\"${CLUSTER_NAME}\")].cluster.certificate-authority-data}")

# Create a restricted kubeconfig for the github-deployer service account
cat <<EOF > kubeconfig-ecosystem-production-github-deployer
apiVersion: v1
kind: Config
clusters:
- name: eco-production
  cluster:
    server: ${CLUSTER_SERVER}
    certificate-authority-data: ${CLUSTER_CA_DATA}
contexts:
- name: github-deployer@eco-production
  context:
    cluster: eco-production
    namespace: ecosystem-production
    user: github-deployer
current-context: github-deployer@eco-production
users:
- name: github-deployer
  user:
    token: ${SA_TOKEN}
EOF

# (Optional) Encode the restricted kubeconfig for use as a GitHub secret
cat kubeconfig-ecosystem-production-github-deployer | base64 | tr -d '\n' \
  > kubeconfig-ecosystem-production-github-deployer-base64.txt

# ⚠️  SECURITY WARNING: Long-lived Service Account Tokens
# This kubeconfig contains a long-lived service account token that does NOT automatically rotate.
# On Kubernetes 1.24+, this pattern is discouraged because:
#   - If the GitHub secret or token is leaked, an attacker gains persistent access
#     to the ecosystem-production namespace (including all Secrets) until manually revoked.
#   - These tokens have no expiration and no automatic rotation.
#
# RECOMMENDED ALTERNATIVE: Use GitHub OIDC + GCP Workload Identity Federation
#   See: https://cloud.google.com/kubernetes-engine/docs/how-to/workload-identity-github-actions
#   This provides short-lived, automatically rotated credentials with no static secrets.
#
# IF YOU MUST USE SERVICE ACCOUNT TOKENS:
#   1. Use short-lived tokens generated at workflow runtime:
#      SA_TOKEN=$(kubectl create token github-deployer --duration=3600s)
#   2. Inject the token into a minimal kubeconfig in the workflow
#   3. Never persist the token to disk or GitHub Secrets
#   4. Implement tight RBAC policies and explicit token rotation procedures
#
# This kubeconfig is restricted to the ecosystem-production namespace
```

### Network Policies

**Important:** GKE Autopilot clusters have network policy enforcement enabled by default and it cannot be disabled. You do not need to run any command to enable it.

To verify that network policy is enabled on your clusters:

```bash
# Verify staging cluster network policy is enabled
gcloud container clusters describe eco-staging --region asia-east1 --project <your-project-id> \
  --format="value(networkPolicy.enabled)"

# Verify production cluster network policy is enabled
gcloud container clusters describe eco-production --region asia-east1 --project <your-project-id> \
  --format="value(networkPolicy.enabled)"

# Example: default deny all ingress traffic in the ecosystem-production namespace
kubectl apply -n ecosystem-production -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all-ingress
spec:
  podSelector: {}
  policyTypes:
    - Ingress
EOF

# Example: allow ingress to pods labeled app=api from any pod in the same namespace
kubectl apply -n ecosystem-production -f - <<'EOF'
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-api-from-namespace
spec:
  podSelector:
    matchLabels:
      app: api
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector: {}
EOF
```

### RBAC Configuration

Example: namespace-scoped deployer service account for staging

```bash
# 1. Create a service account in the staging namespace
kubectl create serviceaccount deploy-bot -n ecosystem-staging

# 2. Define a least-privilege Role allowing basic deployment operations
cat << 'EOF' | kubectl apply -f -
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer-role
  namespace: ecosystem-staging
rules:
  - apiGroups: ["apps"]
    resources: ["deployments", "statefulsets", "replicasets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: [""]
    resources: ["pods", "services", "configmaps", "secrets"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
  - apiGroups: ["autoscaling"]
    resources: ["horizontalpodautoscalers"]
    verbs: ["get", "list", "watch", "create", "update", "patch"]
EOF

# 3. Bind the Role to the service account
kubectl create rolebinding deploy-bot-binding \
  --role=deployer-role \
  --serviceaccount=ecosystem-staging:deploy-bot \
  --namespace=ecosystem-staging

# Repeat similar Role and RoleBinding definitions for the ecosystem-production namespace
# with only the permissions required for your production workflows.
```

### Secrets Management
Consider using:
- Google Secret Manager
- External Secrets Operator
- Sealed Secrets

---

## Troubleshooting

### Check Cluster Status:
```bash
gcloud container clusters list --region asia-east1 --project <your-project-id>
```

### View Cluster Details:
```bash
gcloud container clusters describe eco-staging --region asia-east1 --project <your-project-id>
gcloud container clusters describe eco-production --region asia-east1 --project <your-project-id>
```

### Check Pod Status:
```bash
kubectl get pods -n ecosystem-staging
kubectl get pods -n ecosystem-production
```

### View Logs:
```bash
kubectl logs -f deployment/client -n ecosystem-staging
kubectl logs -f deployment/server -n ecosystem-production
```

### Access GKE Console:

To view and manage your clusters using the GKE web console:

- Open the Google Cloud Console in your browser: https://console.cloud.google.com/
- Navigate to **Kubernetes Engine → Clusters**.
- Select the `eco-staging` or `eco-production` cluster to view its details and workloads.

---

## Ready to Deploy Checklist

Once both clusters are Running:

- [ ] Both clusters show "Running" status
- [ ] Generate and provide base64 kubeconfigs
- [ ] Add kubeconfigs as GitHub secrets
- [ ] Verify cluster access
- [ ] Create namespaces
- [ ] Configure DNS records
- [ ] Set up SSL certificates
- [ ] Deploy to staging
- [ ] Verify staging deployment
- [ ] Deploy to production
- [ ] Verify production deployment

---

## Support Resources

If you encounter any issues during cluster provisioning:
1. Check GKE console for error messages
2. Verify project permissions
3. Ensure quotas are sufficient
4. Check network configuration

For additional assistance, refer to:
- [GKE Autopilot Documentation](https://cloud.google.com/kubernetes-engine/docs/concepts/autopilot-overview)
- [Workload Identity Federation Guide](https://github.com/google-github-actions/auth#setup)
- [Kubernetes Documentation](https://kubernetes.io/docs/home/)

---

**Last Updated**: 2026-02-16
**Status**: Awaiting GKE cluster provisioning to complete