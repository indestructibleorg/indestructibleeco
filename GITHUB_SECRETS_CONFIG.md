# GitHub Organization Secrets Configuration

## Organization Secrets
**URL**: https://github.com/organizations/indestructibleorg/settings/secrets/actions

### Required Secrets

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `GCP_SA_KEY` | *(Service Account JSON)* | Google Cloud Service Account key for deployment |
| `SUPABASE_URL` | `https://yrfxijooswpvdpdseswy.supabase.co` | Supabase project URL |
| `SUPABASE_ANON_KEY` | `REDACTED_SUPABASE_ANON_KEY` | Supabase anonymous key |
| `SUPABASE_SECRET_KEY` | `REDACTED_SUPABASE_SERVICE_ROLE_KEY` | Supabase service role key |
| `CLOUDFLARE_API_TOKEN` | `REDACTED_CLOUDFLARE_API_TOKEN` | Cloudflare Global API Token |
| `CLOUDFLARE_ACCOUNT_ID` | `YOUR_CLOUDFLARE_ACCOUNT_ID` | Cloudflare Account ID |
| `CLOUDFLARE_ZONE_ID` | `YOUR_CLOUDFLARE_ZONE_ID` | Cloudflare Zone ID |
| `GITHUB_PAT` | *(Configure manually)* | GitHub Personal Access Token |
| `GRAFANA_ADMIN_PASSWORD` | *(Generate secure password)* | Grafana admin password |

### GCP Service Account Key

**Service Account**: `eco-deploy-sa@my-project-ops-1991.iam.gserviceaccount.com`

**Roles**:
- Security Admin
- Role Administrator
- IAM Workload Identity Pool Admin (Beta)
- Service Account User
- Service Account Key Admin
- Service Account Credential Creator
- Project IAM Admin
- Database Admin
- AI Platform Admin
- Artifact Registry Admin
- AutoML Admin (Beta)
- Compute Admin
- Edge Container Zone IAM Policy Admin
- IAM OAuth Client Viewer
- Kubernetes Engine Admin
- Storage Admin

**Key IDs**:
- `YOUR_GCP_SA_KEY_ID_1`
- `YOUR_GCP_SA_KEY_ID_2`

**OAuth 2 Client ID**: `YOUR_OAUTH2_CLIENT_ID`

**Additional Token**: `REDACTED_ADDITIONAL_TOKEN`

---

## Organization Variables
**URL**: https://github.com/organizations/indestructibleorg/settings/variables/actions

### Required Variables

| Variable Name | Value | Description |
|---------------|-------|-------------|
| `GCP_PROJECT` | `my-project-ops-1991` | Google Cloud Project ID |
| `GCP_REGION` | `asia-east1` | Default GCP region |
| `GCP_ZONE` | `asia-east1-a` | Default GCP zone |
| `CLUSTER_NAME_STAGING` | `eco-staging` | Staging cluster name |
| `CLUSTER_NAME_PRODUCTION` | `eco-production` | Production cluster name |
| `DOCKER_REGISTRY` | `asia-east1-docker.pkg.dev/my-project-ops-1991/eco-base` | Artifact Registry URI |
| `KUBERNETES_NAMESPACE_STAGING` | `eco-staging` | Staging namespace |
| `KUBERNETES_NAMESPACE_PRODUCTION` | `eco-base` | Production namespace |
| `MONITORING_NAMESPACE` | `monitoring` | Monitoring namespace |

---

## OAuth Application Configuration

### OAuth App Registration
**URL**: https://github.com/settings/developers

### Application Details

| Field | Value |
|-------|-------|
| Application name | eco-base Production |
| Homepage URL | https://eco-base.io |
| Application description | Production OAuth app for eco-base platform |
| Authorization callback URL | https://eco-base.io/auth/callback |

### OAuth Secrets to Add

After registering the OAuth app, add these secrets to the organization:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `OAUTH_CLIENT_ID` | *(From OAuth app)* | OAuth Client ID |
| `OAUTH_CLIENT_SECRET` | *(From OAuth app)* | OAuth Client Secret |

---

## Configuration Steps

### Step 1: Configure Organization Secrets

1. Navigate to: https://github.com/organizations/indestructibleorg/settings/secrets/actions
2. Click "New organization secret"
3. Add each secret from the table above
4. Select repositories that need access (or select "All repositories")

### Step 2: Configure Organization Variables

1. Navigate to: https://github.com/organizations/indestructibleorg/settings/variables/actions
2. Click "New organization variable"
3. Add each variable from the table above
4. Select repositories that need access (or select "All repositories")

### Step 3: Register OAuth Application

1. Navigate to: https://github.com/settings/developers
2. Click "New OAuth App"
3. Fill in the application details
4. Click "Register application"
5. Copy the Client ID and generate a new Client Secret
6. Add these as organization secrets

### Step 4: Verify Configuration

Run the CI validator to ensure all workflows can access the required secrets:

```bash
cd /workspace/repo
python3 tools/ci-validator/validate.py
```

---

## Security Notes

1. **Secret Rotation**: Regularly rotate sensitive secrets (especially GCP_SA_KEY, SUPABASE_SECRET_KEY, CLOUDFLARE_API_TOKEN)
2. **Access Control**: Limit secret access to only necessary repositories
3. **Audit Logging**: Enable audit logging for all secret access
4. **Backup**: Keep secure backups of all secrets in a password manager
5. **GCP Service Account**: Use workload identity federation instead of long-lived keys when possible

---

## Troubleshooting

### Common Issues

1. **Secret not found in workflow**: Ensure the secret is added to the organization and the repository has access
2. **Invalid GCP credentials**: Verify the service account key is valid and has proper permissions
3. **Supabase connection failed**: Check SUPABASE_URL and keys are correct
4. **Cloudflare API errors**: Verify API token has proper permissions

### Debug Commands

```bash
# Test GCP authentication
gcloud auth activate-service-account --key-file=<(echo "$GCP_SA_KEY")
gcloud projects list

# Test Supabase connection
curl -H "apikey: $SUPABASE_ANON_KEY" "$SUPABASE_URL/rest/v1/"

# Test Cloudflare API
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

---

**Document Version**: 1.0  
**Last Updated**: 2024-02-21  
**Status**: Pending Configuration