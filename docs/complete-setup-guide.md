# IndestructibleEco - Complete Setup Guide

**Date**: February 21, 2026
**Project**: IndestructibleEco
**Status**: Production Ready

---

## 🎯 Overview

This guide provides complete instructions for deploying the IndestructibleEco infrastructure with all configurations, secrets, and monitoring systems.

---

## 📋 Prerequisites

### Required Tools

- `kubectl` - Kubernetes command-line tool
- `gcloud` - Google Cloud SDK
- `git` - Version control
- `bash` - Shell environment

### Required Access

- GCP Project: `my-project-ops-1991`
- GKE Cluster: `eco-staging` (asia-east1)
- Supabase Project: `yrfxijooswpvdpdseswy`
- Cloudflare Account: indestructibleorg

---

## 🔐 Token Manifest

All tokens and credentials are documented in `TOKENS_MANIFEST.md`. This file contains:

- GCP Service Account credentials
- Supabase API keys and database credentials
- Cloudflare SSL/TLS certificates
- Environment variables

⚠️ **WARNING**: Never commit `TOKENS_MANIFEST.md` to version control.

---

## 🚀 Quick Start

### Option 1: Complete Automated Deployment (Recommended)

```bash
# Clone the repository
git clone https://github.com/indestructibleorg/indestructibleeco.git
cd indestructibleeco

# Run the complete deployment script
./scripts/deploy_complete_infrastructure.sh
```

This script will:

1. Configure all secrets (GCP, Supabase, Cloudflare)
2. Deploy monitoring stack (Prometheus, Grafana, Node Exporter)
3. Verify all deployments
4. Test Supabase metrics API
5. Provide access URLs and credentials

### Option 2: Step-by-Step Deployment

#### Step 1: Configure Secrets

```bash
./scripts/configure_all_secrets.sh
```

This will configure:

- GCP Service Account secret
- Supabase secrets (URL, keys, database connection)
- Cloudflare origin certificate
- Prometheus secrets
- Grafana secrets

#### Step 2: Deploy Monitoring Stack

```bash
./scripts/setup_supabase_monitoring.sh
```

This will deploy:

- Prometheus with Supabase configuration
- Grafana with pre-configured dashboards
- Node Exporter for Kubernetes metrics

#### Step 3: Configure Cloudflare DNS

Create CNAME records in Cloudflare:

1. **Prometheus**:
   - Type: CNAME
   - Name: `prometheus._cf-custom-hostname`
   - Target: `<INGRESS_IP>`
   - Proxy status: Proxied (orange cloud)

2. **Grafana**:
   - Type: CNAME
   - Name: `grafana._cf-custom-hostname`
   - Target: `<INGRESS_IP>`
   - Proxy status: Proxied (orange cloud)

Get the Ingress IP:
```bash
kubectl get ingress -n monitoring
```

---

## 🔧 Manual Configuration

### GCP Authentication

```bash
# Authenticate with GCP
gcloud auth login

# Set project
gcloud config set project my-project-ops-1991

# Get GKE credentials
gcloud container clusters get-credentials eco-staging --region asia-east1
```

### Create Secrets Manually

#### GCP Service Account Secret
```bash
kubectl create secret generic gcp-sa-key \
  --from-file=.gcp/eco-deployer-key.json \
  --namespace=indestructibleeco
```

#### Supabase Secrets
```bash
kubectl create secret generic supabase-secrets \
  --from-literal=SUPABASE_URL="https://yrfxijooswpvdpdseswy.supabase.co" \
  --from-literal=SUPABASE_ANON_KEY="YOUR_SUPABASE_ANON_KEY" \
  --from-literal=SUPABASE_SERVICE_ROLE_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY" \
  --from-literal=SUPABASE_DB_URL="postgresql://postgres:YOUR_PASSWORD@db.yrfxijooswpvdpdseswy.supabase.co:5432/postgres" \
  --from-literal=SUPABASE_JWT_SECRET="YOUR_JWT_SECRET" \
  --from-literal=SUPABASE_PROJECT_REF="yrfxijooswpvdpdseswy" \
  --namespace=indestructibleeco
```

#### Cloudflare Certificate Secret

```bash
kubectl create secret tls cloudflare-origin-cert \
  --cert=.cloudflare/cloudflare-origin-cert.pem \
  --key=.cloudflare/cloudflare-origin-key.key \
  --namespace=monitoring
```

#### Prometheus Secret
```bash
kubectl create secret generic prometheus-secrets \
  --from-literal=SUPABASE_SECRET_KEY="YOUR_SUPABASE_SERVICE_ROLE_KEY" \
  --namespace=monitoring
```

#### Grafana Secret
```bash
kubectl create secret generic grafana-secrets \
  --from-literal=admin-user="admin" \
  --from-literal=admin-password="IndestructibleEco2026!" \
  --namespace=monitoring
```

---

## 📊 Access URLs

### Monitoring Stack

- **Prometheus**: https://prometheus._cf-custom-hostname.autoecoops.io
- **Grafana**: https://grafana._cf-custom-hostname.autoecoops.io
  - Username: `admin`
  - Password: `IndestructibleEco2026!`

### Supabase

- **Dashboard**: https://supabase.com/dashboard/project/yrfxijooswpvdpdseswy
- **API**: https://yrfxijooswpvdpdseswy.supabase.co
- **Database**: db.yrfxijooswpvdpdseswy.supabase.co:5432

### GCP

- **Console**: https://console.cloud.google.com/project/my-project-ops-1991
- **GKE**: https://console.cloud.google.com/kubernetes/list?project=my-project-ops-1991

---

## ✅ Verification

### Verify Secrets

```bash
# Check all secrets
kubectl get secrets -n indestructibleeco
kubectl get secrets -n monitoring

# Verify specific secret
kubectl describe secret supabase-secrets -n indestructibleeco
```

### Verify Deployments

```bash
# Check deployments
kubectl get deployments -n monitoring

# Check pods
kubectl get pods -n monitoring

# Check services
kubectl get services -n monitoring

# Check ingress
kubectl get ingress -n monitoring
```

### Verify Prometheus Scraping

1. Access Prometheus: https://prometheus._cf-custom-hostname.autoecoops.io
2. Go to **Status → Targets**
3. Verify `supabase-production` job is **UP**

### Verify Grafana Dashboards

1. Access Grafana: https://grafana._cf-custom-hostname.autoecoops.io
2. Login with admin credentials
3. Navigate to **Dashboards → Supabase → Supabase Overview**
4. Verify metrics are displaying

### Test Supabase Metrics API

```bash
curl https://yrfxijooswpvdpdseswy.supabase.co/customer/v1/privileged/metrics \
  --user 'service_role:YOUR_SERVICE_ROLE_KEY'
```

---

## 🔒 Security Best Practices

### 1. Secret Management

- ✅ All secrets stored in Kubernetes secrets
- ✅ Never commit secrets to version control
- ✅ Use environment variables for sensitive data
- ✅ Rotate keys regularly (every 90 days)

### 2. Access Control

- ✅ GCP Service Account has Owner permissions
- ✅ Supabase Service Role key has full access
- ✅ Grafana has secure admin password
- ✅ Cloudflare certificates for SSL/TLS

### 3. Network Security

- ✅ All communications use HTTPS
- ✅ Cloudflare proxy enabled
- ✅ TLS certificates configured
- ✅ Network policies enforced

### 4. Monitoring & Alerting

- ✅ Prometheus scraping every 60 seconds
- ✅ 20+ pre-configured alerts
- ✅ Grafana dashboards for monitoring
- ✅ Log aggregation enabled

---

## 📝 Environment Variables

### GCP Environment Variables
```bash
export GCP_PROJECT="my-project-ops-1991"
export GCP_REGION="asia-east1"
export GCP_ZONE="asia-east1-a"
export GKE_CLUSTER="eco-staging"
export GCP_SA_EMAIL="eco-deployer@my-project-ops-1991.iam.gserviceaccount.com"
```

### Supabase Environment Variables
```bash
export SUPABASE_URL="https://yrfxijooswpvdpdseswy.supabase.co"
export SUPABASE_ANON_KEY="sb_publishable_rhTyBa4IqqV14n_B87S7g_zKzDSYTd"
export SUPABASE_SERVICE_ROLE_KEY="sb_secret_YOUR_SERVICE_ROLE_KEY"
export SUPABASE_DB_URL="postgresql://postgres:Wei412011$@db.yrfxijooswpvdpdseswy.supabase.co:5432/postgres"
export SUPABASE_PROJECT_REF="yrfxijooswpvdpdseswy"
```

### Cloudflare Environment Variables
```bash
export CLOUDFLARE_CUSTOM_HOSTNAME="_cf-custom-hostname.autoecoops.io"
export CLOUDFLARE_HOSTNAME_ID="21c5d22a-4512-485b-9557-8aa9fa7c96ed"
```

---

## 🚨 Troubleshooting

### Secrets Not Found

```bash
# Check if secrets exist
kubectl get secrets -n indestructibleeco
kubectl get secrets -n monitoring

# Reconfigure secrets
./scripts/configure_all_secrets.sh
```

### Pods Not Starting

```bash
# Check pod status
kubectl get pods -n monitoring

# Check pod logs
kubectl logs -n monitoring deployment/prometheus
kubectl logs -n monitoring deployment/grafana

# Describe pod for details
kubectl describe pod <pod-name> -n monitoring
```

### SSL/TLS Certificate Issues

```bash
# Verify certificate secret exists
kubectl get secret cloudflare-origin-cert -n monitoring

# Check ingress configuration
kubectl describe ingress prometheus-ingress -n monitoring

# Test SSL certificate
curl -v https://prometheus._cf-custom-hostname.autoecoops.io
```

### Prometheus Not Scraping Supabase

```bash
# Check Prometheus logs
kubectl logs -n monitoring deployment/prometheus

# Verify Supabase secret
kubectl get secret prometheus-secrets -n monitoring -o yaml

# Test metrics endpoint manually
curl https://yrfxijooswpvdpdseswy.supabase.co/customer/v1/privileged/metrics \
  --user 'service_role:YOUR_SERVICE_ROLE_KEY'
```

---

## 📚 Additional Documentation

- **Token Manifest**: `TOKENS_MANIFEST.md`
- **Supabase Monitoring Guide**: `docs/supabase-monitoring-guide.md`
- **Monitoring Summary**: `SUPABASE_MONITORING_SUMMARY.md`
- **Project TODO**: `todo.md`

---

## 🎉 Success Criteria

Your infrastructure is successfully deployed when:

- ✅ All secrets are configured in Kubernetes
- ✅ Prometheus is scraping Supabase metrics
- ✅ Grafana dashboards are displaying data
- ✅ SSL/TLS certificates are working
- ✅ Cloudflare DNS records are configured
- ✅ All pods are running and healthy
- ✅ Alerts are configured and evaluating

---

## 📞 Support

For issues or questions:

1. Check the troubleshooting section
2. Review logs: `kubectl logs -n monitoring <pod-name>`
3. Consult the documentation
4. Check Prometheus targets status
5. Verify Grafana dashboard data

---

**End of Complete Setup Guide**

🚀 Your IndestructibleEco infrastructure is ready for production!
