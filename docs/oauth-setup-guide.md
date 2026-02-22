# OAuth Consent Screen Setup Guide - IndestructibleEco

## Overview

This guide explains how to configure the OAuth consent screen for the IndestructibleEco platform authentication.

## Prerequisites

- GCP project: `my-project-ops-1991`
- GCP account with appropriate permissions
- OAuth consent screen configuration access

## Manual Configuration

### Step 1: Open OAuth Consent Screen

Navigate to the OAuth consent screen page:
```
https://console.cloud.google.com/apis/credentials/consent?project=my-project-ops-1991
```

### Step 2: Select User Type

Choose the appropriate user type:

**External** (Recommended for Production):
- Available to any user with a Google Account
- Requires verification for publishing
- Suitable for public applications

**Internal** (Testing Only):
- Available only to users within your organization
- No verification required
- Suitable for internal testing

### Step 3: Fill in App Information

**Required Fields:**
- **App name**: `IndestructibleEco`
- **User support email**: `support@indestructibleeco.io`
- **Developer contact email**: `dev@indestructibleeco.io`

**Optional Fields:**
- **App logo**: Upload your company logo
- **Application home page**: `https://autoecoops.io`
- **Application privacy policy link**: `https://autoecoops.io/privacy`
- **Application terms of service link**: `https://autoecoops.io/terms`
- **Authorized domains**: `autoecoops.io`, `indestructibleorg.github.io`

### Step 4: Configure Scopes

Add the following OAuth scopes:

**Required Scopes:**
- `openid` - OpenID Connect
- `email` - User email address
- `profile` - User profile information

**Optional Scopes:**
- `https://www.googleapis.com/auth/userinfo.email` - Email access
- `https://www.googleapis.com/auth/userinfo.profile` - Profile access

### Step 5: Add Test Users (External Only)

If using External user type, add test users:
1. Click "Add Users"
2. Enter email addresses of test users
3. Click "Add"

### Step 6: Submit for Verification (External Only)

For production deployment:
1. Review all information
2. Click "Submit for Verification"
3. Wait for Google verification (1-3 business days)

## Automated Configuration

Use the provided script to automate the process:

```bash
# Make script executable
chmod +x scripts/configure-oauth-consent.sh

# Run script
./scripts/configure-oauth-consent.sh
```

The script will:
- Check gcloud CLI installation
- Verify GCP authentication
- Open GCP Console with OAuth consent screen page
- Provide step-by-step instructions

## OAuth Client Configuration

After consent screen is configured, create OAuth clients:

### Create OAuth 2.0 Client ID

1. Navigate to: https://console.cloud.google.com/apis/credentials
2. Click "Create Credentials" > "OAuth client ID"
3. Select application type:
   - **Web application**: For web frontend
   - **Desktop app**: For CLI tools
4. Configure authorized redirect URIs:
   - `https://staging.autoecoops.io/auth/callback`
   - `https://production.autoecoops.io/auth/callback`
   - `http://localhost:3000/auth/callback` (development)
5. Save client ID and client secret

### Create Service Account

1. Navigate to: https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Fill in details:
   - Name: `eco-auth-sa`
   - Description: `IndestructibleEco authentication service account`
4. Assign roles:
   - `roles/iam.serviceAccountUser`
   - `roles/cloudsql.client` (if using Cloud SQL)
5. Create and download key

## Environment Variables

Add the following to your environment:

```bash
# OAuth Client ID
export ECO_OAUTH_CLIENT_ID=your-client-id.apps.googleusercontent.com

# OAuth Client Secret
export ECO_OAUTH_CLIENT_SECRET=your-client-secret

# Service Account Key
export ECO_SA_KEY_PATH=/path/to/service-account-key.json
```

## Testing OAuth Flow

### Test Locally

```bash
# Start local development server
npm run dev

# Navigate to OAuth login
open http://localhost:3000/auth/login
```

### Test on Staging

```bash
# Deploy to staging
kubectl apply -f k8s/staging/

# Test OAuth flow
curl -X POST https://staging.autoecoops.io/auth/callback \
  -H "Content-Type: application/json" \
  -d '{"code": "auth-code"}'
```

## Troubleshooting

### Consent Screen Not Visible

If consent screen is not visible:
1. Verify user type selection
2. Check GCP project permissions
3. Ensure OAuth consent screen is configured

### Verification Failed

If verification fails:
1. Review verification requirements
2. Check all required fields are filled
3. Ensure privacy policy and terms of service links are valid
4. Contact Google Support if needed

### OAuth Client Not Working

If OAuth client is not working:
1. Verify redirect URIs match exactly
2. Check client ID and client secret are correct
3. Ensure consent screen is configured
4. Review OAuth client logs

## Security Best Practices

1. **Use HTTPS**: Always use HTTPS for OAuth callbacks
2. **Validate Redirect URIs**: Strictly validate redirect URIs
3. **Rotate Secrets**: Regularly rotate client secrets
4. **Limit Scopes**: Request only necessary scopes
5. **Monitor Usage**: Monitor OAuth usage for anomalies

## Governance

- **Owner**: indestructibleorg
- **Policy**: zero-trust
- **Compliance**: indestructibleeco v1.0
- **Audit**: All OAuth configurations logged in GCP

## References

- [GCP OAuth 2.0 Documentation](https://cloud.google.com/docs/authentication)
- [OAuth 2.0 Playground](https://developers.google.com/oauthplayground)
- [OpenID Connect Discovery](https://openid.net/connect/)

## Next Steps

1. Configure OAuth consent screen
2. Create OAuth clients
3. Set up environment variables
4. Test OAuth flow
5. Deploy to production
6. Monitor authentication logs