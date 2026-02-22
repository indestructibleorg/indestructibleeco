# IndestructibleEco - Complete Token Manifest

**Date**: February 21, 2026
**Project**: IndestructibleEco
**Environment**: Production

---

## 🔐 GCP Service Account Token

### Service Account Details

- **Email**: `eco-deployer@my-project-ops-1991.iam.gserviceaccount.com`
- **Name**: IndestructibleEco Deployer
- **Key ID**: `YOUR_GCP_SA_KEY_ID`

### Permissions

- ✅ Owner
- ✅ Editor
- ✅ Viewer
- ✅ Service Account User
- ✅ Service Account Key Admin
- ✅ Service Account Token Creator
- ✅ Service Account Credential Creator
- ✅ Create Service Accounts
- ✅ View Service Accounts
- ✅ Database Admin
- ✅ Site Reliability Engineer
- ✅ Data Scientist
- ✅ Machine Learning Engineer
- ✅ Developer Operations
- ✅ Workload Identity User
- ✅ Security Auditor
- ✅ Service Account API Key Binding Admin

### Usage

- GKE cluster authentication
- GCP resource management
- Deployment automation

---

## 🔑 Supabase Tokens

### Project Details

- **Project Name**: indestructibleeco
- **Project Reference**: `yrfxijooswpvdpdseswy`
- **Project URL**: `https://yrfxijooswpvdpdseswy.supabase.co`
- **Region**: ap-south-1

### API Keys

#### Publishable Key (Client)
```
YOUR_SUPABASE_PUBLISHABLE_KEY
```

- **Usage**: Client-side applications
- **Permissions**: Anonymous access (with RLS policies)
- **Security**: Safe to use in browser

#### Secret Key (Service Role)

```
sb_secret_YOUR_SERVICE_ROLE_KEY_HERE
```

- **Usage**: Server-side applications
- **Permissions**: Full access, bypasses RLS
- **Security**: Never expose to client

#### Anon Key (Legacy)
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlyZnhpam9vc3dwdmRwZHNlc3d5Iiwicm9s
```

- **Usage**: Legacy authentication
- **Status**: Migrated to new JWT keys

### JWT Configuration

#### JWT Signing Keys

- **JWT Key ID**: `d8cfd2f1-cb4d-4f15-925f-1cd9faadebfc`
- **Access Token Expiry**: 3600 seconds (1 hour)

#### Legacy JWT Secret
```
YOUR_JWT_SECRET_HERE
```

- **Usage**: JWT token verification
- **Status**: Legacy, consider rotating

### Database Connection

#### Direct Connection String
```
postgresql://postgres:YOUR_PASSWORD@db.yrfxijooswpvdpdseswy.supabase.co:5432/postgres
```

#### Connection Parameters

- **Host**: `db.yrfxijooswpvdpdseswy.supabase.co`
- **Port**: `5432`
- **Database**: `postgres`
- **User**: `postgres`
- **Password**: YOUR_PASSWORD

### S3 Configuration

#### S3 Protocol Connection

- **Endpoint**: `https://yrfxijooswpvdpdseswy.storage.supabase.co/storage/v1/s3`
- **Region**: `ap-south-1`
- **Bucket**: `autoecoops_keys`
- **Access Key**: `7bc8a0a036fbd497ba54ef47d76b5be4`

### Edge Functions

#### Function Deployment
```bash
supabase functions new hello-world
supabase functions deploy hello-world --project-ref yrfxijooswpvdpdseswy
```

#### Function Invocation
```bash
curl -L -X POST 'https://YOUR_PROJECT_REF.supabase.co/functions/v1/hello-world' \
  -H 'Authorization: Bearer YOUR_SUPABASE_PUBLISHABLE_KEY' \
  --data '{"name":"Functions"}'
```

---

## 🌐 Cloudflare Tokens

### Custom Hostname

- **Hostname**: `_cf-custom-hostname.autoecoops.io`
- **Hostname ID**: `21c5d22a-4512-485b-9557-8aa9fa7c96ed`

### SSL/TLS Certificates

#### Client Certificate (for Cloudflare Client Authentication)
**Certificate**:
```
-----BEGIN CERTIFICATE-----
YOUR_CLIENT_CERTIFICATE_HERE
-----END CERTIFICATE-----
```

**Private Key**:
```
-----BEGIN PRIVATE KEY-----
YOUR_CLIENT_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
```

#### Origin Certificate (for Kubernetes Ingress)
**Certificate**:
```
-----BEGIN CERTIFICATE-----
YOUR_ORIGIN_CERTIFICATE_HERE
-----END CERTIFICATE-----
```

**Private Key**:
```
-----BEGIN PRIVATE KEY-----
YOUR_ORIGIN_PRIVATE_KEY_HERE
-----END PRIVATE KEY-----
```

---

## 📋 Environment Variables Summary

### GCP Environment Variables
```bash
export GCP_PROJECT="my-project-ops-1991"
export GCP_REGION="asia-east1"
export GCP_ZONE="asia-east1-a"
export GKE_CLUSTER="eco-staging"
export GCP_SA_EMAIL="eco-deployer@my-project-ops-1991.iam.gserviceaccount.com"
export GCP_SA_KEY="YOUR_GCP_SA_KEY_ID"
```

### Supabase Environment Variables
```bash
export SUPABASE_URL="https://yrfxijooswpvdpdseswy.supabase.co"
export SUPABASE_ANON_KEY="YOUR_SUPABASE_PUBLISHABLE_KEY"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_YOUR_SERVICE_ROLE_KEY"
export SUPABASE_DB_URL="postgresql://postgres:YOUR_PASSWORD@db.yrfxijooswpvdpdseswy.supabase.co:5432/postgres"
export SUPABASE_JWT_SECRET="YOUR_JWT_SECRET"
export SUPABASE_PROJECT_REF="yrfxijooswpvdpdseswy"
```

### Cloudflare Environment Variables

```bash
export CLOUDFLARE_CUSTOM_HOSTNAME="_cf-custom-hostname.autoecoops.io"
export CLOUDFLARE_HOSTNAME_ID="21c5d22a-4512-485b-9557-8aa9fa7c96ed"
```

### Monitoring Environment Variables
```bash
export PROMETHEUS_URL="https://prometheus._cf-custom-hostname.autoecoops.io"
export GRAFANA_URL="https://grafana._cf-custom-hostname.autoecoops.io"
export GRAFANA_ADMIN_USER="admin"
export GRAFANA_ADMIN_PASSWORD="YOUR_SECURE_PASSWORD"
```

---

## 🔒 Security Notes

### Critical Security Practices

1. **Never commit secrets to version control**
2. **Rotate keys regularly** (every 90 days recommended)
3. **Use environment variables** for all sensitive data
4. **Implement RBAC** for all services
5. **Enable audit logging** for all GCP resources
6. **Use TLS** for all communications
7. **Monitor access logs** for suspicious activity

### Key Rotation Schedule

- **GCP Service Account Keys**: Every 90 days
- **Supabase Service Role Keys**: Every 90 days
- **Cloudflare Certificates**: Every 15 years (Origin Certs)
- **JWT Secrets**: Every 6 months

### Access Control

- **GCP Service Account**: Owner permissions (use with caution)
- **Supabase Service Role**: Full database access (server-side only)
- **Supabase Anon Key**: Client-side access (with RLS)
- **Cloudflare Certificates**: SSL/TLS termination

---

## 📞 Emergency Contacts

### GCP Support

- **Project**: my-project-ops-1991
- **Service Account**: eco-deployer@my-project-ops-1991.iam.gserviceaccount.com

### Supabase Support

- **Project**: indestructibleeco
- **Reference**: yrfxijooswpvdpdseswy
- **Dashboard**: https://supabase.com/dashboard/project/yrfxijooswpvdpdseswy

### Cloudflare Support

- **Account**: indestructibleorg
- **Custom Hostname**: _cf-custom-hostname.autoecoops.io

---

**End of Token Manifest**

⚠️ **WARNING**: This document contains sensitive credentials. Store securely and never commit to version control.
