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

### 1. Add GitHub Secrets

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

### 2. Verify Cluster Access
```bash
# Test staging access
kubectl get nodes --context=gke_<project-id>_asia-east1_eco-staging

# Test production access
kubectl get nodes --context=gke_<project-id>_asia-east1_eco-production
```

### 3. Create Namespaces
```bash
# Staging
kubectl create namespace ecosystem-staging --context=gke_<project-id>_asia-east1_eco-staging

# Production
kubectl create namespace ecosystem-production --context=gke_<project-id>_asia-east1_eco-production
```

### 4. Deploy to Staging
- Push changes to main branch
- CI/CD pipeline will automatically deploy to staging
- Monitor deployment health

### 5. Deploy to Production
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
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.16.0/cert-manager.yaml

# Create ClusterIssuer
kubectl apply -f infrastructure/cert-manager/cluster-issuer.yaml
```

### Option 2: Google Managed Certificates
Google Cloud SSL certificate management:

```yaml
apiVersion: networking.gke.io/v1
kind: ManagedCertificate
metadata:
  name: ecosystem-cert
spec:
  domains:
    - ecosystem.machops.io
    - api.ecosystem.machops.io
```

---

## Monitoring and Logging

GKE Autopilot integrates with:
- **Cloud Monitoring**: Metrics and dashboards
- **Cloud Logging**: Log aggregation and analysis
- **Cloud Trace**: Distributed tracing
- **Error Reporting**: Error tracking

I can set up:
- Prometheus + Grafana (custom monitoring)
- Loki for centralized logging
- Custom dashboards for your ecosystem

---

## Security Best Practices

### Recommended: GitHub OIDC + Workload Identity Federation

For production deployments, use GitHub's OIDC provider with GCP Workload Identity Federation to avoid storing long-lived credentials:

```yaml
# In your GitHub Actions workflow:
- name: Authenticate to Google Cloud
  uses: google-github-actions/auth@v2
  with:
    workload_identity_provider: 'projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL_NAME/providers/PROVIDER_NAME'
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

# Get the service account token and create a restricted kubeconfig
# This kubeconfig will only have access to the specific namespace
```

### Network Policies
```bash
# Enable network policy enforcement
# Add network policies to restrict traffic
```

### RBAC Configuration
```bash
# Create service accounts
# Configure role-based access control
# Implement least privilege principle
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
gcloud container clusters list --region asia-east1
```

### View Cluster Details:
```bash
gcloud container clusters describe eco-staging --region asia-east1
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

### Access Dashboard:
```bash
# Open GKE Console
gcloud container clusters get-credentials eco-staging --region asia-east1
kubectl proxy
# Open http://localhost:8001/ui
```

---

## Ready to Deploy Checklist

Once both clusters are Running:

- [ ] Both clusters show "Running" status
- [ ] Generate and provide base64 kubeconfigs
- [ ] I add kubeconfigs as GitHub secrets
- [ ] Verify cluster access
- [ ] Create namespaces
- [ ] Configure DNS records
- [ ] Set up SSL certificates
- [ ] Deploy to staging
- [ ] Verify staging deployment
- [ ] Deploy to production
- [ ] Verify production deployment

---

## Questions?

If you encounter any issues during cluster provisioning:
1. Check GKE console for error messages
2. Verify project permissions
3. Ensure quotas are sufficient
4. Check network configuration

I'm ready to help with:
- Adding kubeconfig secrets
- Configuring deployments
- Setting up monitoring
- Troubleshooting any issues

---

**Last Updated**: 2026-02-16
**Status**: Awaiting GKE cluster provisioning to complete