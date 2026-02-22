# Supabase Pro Monitoring Setup Guide

## Overview

This guide explains how to set up comprehensive monitoring for your Supabase Pro project using Prometheus and Grafana. This setup provides full control over retention, alert routing, and dashboards.

## Prerequisites

- Supabase Pro account
- Kubernetes cluster (GKE recommended)
- kubectl configured
- Supabase Secret API key (sb_secret_...)

## Architecture

```
┌─────────────────┐
│   Supabase Pro  │
│  Metrics API    │
└────────┬────────┘
         │ HTTPS (Basic Auth)
         │ service_role:secret_key
         ▼
┌─────────────────┐
│   Prometheus    │
│  (Scrapes 60s)  │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│     Grafana     │
│  (Dashboards)   │
└─────────────────┘
```

## Quick Start

### 1. Get Your Supabase Credentials

1. Navigate to your Supabase project dashboard
2. Go to **Project Settings → API Keys**
3. Copy your **Secret API key** (starts with `sb_secret_`)
4. Note your **Project Reference** (e.g., `yrfxijooswpvdpdseswy`)

### 2. Get Cloudflare Certificates

1. Navigate to Cloudflare Dashboard → SSL/TLS → Origin Server
2. Download the **Origin Certificate** and **Private Key**
3. Save them as:
   - `cloudflare-origin-cert.pem`
   - `cloudflare-origin-key.key`

### 3. Run the Setup Script

```bash
# Navigate to the repository
cd repo

# Run the monitoring setup script
./scripts/setup_supabase_monitoring.sh

# Run the Cloudflare certificate setup script
./scripts/setup_cloudflare_certs.sh
```

The scripts will:

- Create the monitoring namespace
- Deploy Prometheus with Supabase configuration
- Deploy Grafana with pre-configured dashboards
- Deploy Node Exporter for Kubernetes metrics
- Configure secrets with your credentials
- Set up Cloudflare SSL certificates

### 4. Configure Cloudflare DNS

Create CNAME records in Cloudflare:

- `prometheus._cf-custom-hostname.autoecoops.io` → `<INGRESS_IP>`
- `grafana._cf-custom-hostname.autoecoops.io` → `<INGRESS_IP>`

### 5. Access the Monitoring Stack

After deployment, access the services:

- **Grafana**: https://grafana._cf-custom-hostname.autoecoops.io
  - Username: `admin`
  - Password: (set via `GRAFANA_PASSWORD` environment variable, no default)

- **Prometheus**: https://prometheus._cf-custom-hostname.autoecoops.io

## Manual Deployment

If you prefer manual deployment:

### 1. Create Namespace

```bash
kubectl apply -f monitoring/k8s/namespace.yaml
```

### 2. Deploy Node Exporter

```bash
kubectl apply -f monitoring/k8s/node-exporter-daemonset.yaml
```

### 3. Deploy Prometheus

```bash
# Create secret with Supabase credentials
kubectl create secret generic prometheus-secrets \
  --from-literal=SUPABASE_SECRET_KEY='your-sb-secret-key' \
  --namespace=monitoring

# Deploy Prometheus
kubectl apply -f monitoring/k8s/prometheus-deployment.yaml
```

### 4. Deploy Grafana

```bash
# Create secret with admin credentials
kubectl create secret generic grafana-secrets \
  --from-literal=admin-user='admin' \
  --from-literal=admin-password='your-secure-password' \
  --namespace=monitoring

# Deploy Grafana
kubectl apply -f monitoring/k8s/grafana-deployment.yaml
```

### 5. Configure Cloudflare Certificates

```bash
# Create secret with Cloudflare certificates
kubectl create secret tls cloudflare-origin-cert \
  --cert=cloudflare-origin-cert.pem \
  --key=cloudflare-origin-key.key \
  --namespace=monitoring

# Update Ingress resources to use Cloudflare certificate
kubectl patch ingress prometheus-ingress -n monitoring -p '{
  "spec": {
    "tls": [{
      "hosts": ["prometheus._cf-custom-hostname.autoecoops.io"],
      "secretName": "cloudflare-origin-cert"
    }]
  }
}' --type=merge

kubectl patch ingress grafana-ingress -n monitoring -p '{
  "spec": {
    "tls": [{
      "hosts": ["grafana._cf-custom-hostname.autoecoops.io"],
      "secretName": "cloudflare-origin-cert"
    }]
  }
}' --type=merge
```

## Configuration

### Cloudflare Domain Configuration

The monitoring stack uses Cloudflare custom hostname:

- **Base Domain**: `_cf-custom-hostname.autoecoops.io`
- **Prometheus**: `prometheus._cf-custom-hostname.autoecoops.io`
- **Grafana**: `grafana._cf-custom-hostname.autoecoops.io`

### Setting Up Cloudflare Certificates

1. **Get Certificates from Cloudflare**:
   - Go to Cloudflare Dashboard → SSL/TLS → Origin Server
   - Download the Origin Certificate and Private Key
   - Save them as `cloudflare-origin-cert.pem` and `cloudflare-origin-key.key`

2. **Create Kubernetes Secret**:
   ```bash
   ./scripts/setup_cloudflare_certs.sh
   ```

   Or manually:
   ```bash
   kubectl create secret tls cloudflare-origin-cert \
     --cert=cloudflare-origin-cert.pem \
     --key=cloudflare-origin-key.key \
     --namespace=monitoring
   ```

3. **Configure DNS Records**:
   - Create CNAME records in Cloudflare:
     - `prometheus._cf-custom-hostname.autoecoops.io` → `<INGRESS_IP>`
     - `grafana._cf-custom-hostname.autoecoops.io` → `<INGRESS_IP>`

### Prometheus Configuration

The Prometheus configuration is located in `monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'supabase-production'
    scrape_interval: 60s
    metrics_path: /customer/v1/privileged/metrics
    scheme: https
    basic_auth:
      username: service_role
      password: '${SUPABASE_SECRET_KEY}'
    static_configs:
      - targets:
          - 'yrfxijooswpvdpdseswy.supabase.co:443'
        labels:
          project: 'yrfxijooswpvdpdseswy'
          environment: 'production'
          service: 'supabase'
```

### Alert Rules

Alert rules are defined in `monitoring/prometheus/alerts.yml`:

- **Database Alerts**: CPU, memory, disk usage, connection pool
- **API Alerts**: Error rate, latency, request rate
- **Kubernetes Alerts**: Node resources, pod health

### Grafana Dashboards

Pre-configured dashboards include:

1. **Supabase Overview**: Database health, API performance
2. **Kubernetes Cluster**: Node and pod metrics
3. **IndestructibleEco**: Application-specific metrics

## Testing the Setup

### Test Supabase Metrics API

```bash
curl https://yrfxijooswpvdpdseswy.supabase.co/customer/v1/privileged/metrics \
  --user 'service_role:sb_secret_YOUR_SECRET_KEY'
```

Expected output: Prometheus metrics in text format

### Verify Prometheus Scraping

1. Access Prometheus at https://prometheus._cf-custom-hostname.autoecoops.io
2. Go to **Status → Targets**
3. Verify `supabase-production` job is **UP**

### Verify Grafana Dashboards

1. Access Grafana at https://grafana._cf-custom-hostname.autoecoops.io
2. Login with admin credentials
3. Navigate to **Dashboards → Supabase → Supabase Overview**
4. Verify metrics are displaying

## Available Metrics

### Database Metrics

- `supabase_cpu_usage_percent` - Database CPU usage
- `supabase_memory_usage_percent` - Database memory usage
- `supabase_disk_usage_percent` - Disk space usage
- `supabase_connections_active` - Active connections
- `supabase_connections_max` - Maximum connections
- `supabase_query_duration_seconds` - Query latency (percentiles)
- `supabase_replication_lag_seconds` - Replication lag
- `supabase_wal_size_bytes` - WAL size

### API Metrics

- `supabase_api_requests_total` - Total API requests
- `supabase_api_errors_total` - Total API errors
- `supabase_api_duration_seconds` - API latency (percentiles)

## Alerting

### Configured Alerts

#### Database Alerts

- **SupabaseHighCPUUsage**: CPU > 80% for 5m
- **SupabaseCriticalCPUUsage**: CPU > 95% for 2m
- **SupabaseHighMemoryUsage**: Memory > 85% for 5m
- **SupabaseDiskSpaceLow**: Disk > 80% for 5m
- **SupabaseDiskSpaceCritical**: Disk > 90% for 2m
- **SupabaseConnectionPoolHigh**: Pool > 80% for 5m
- **SupabaseConnectionPoolCritical**: Pool > 95% for 2m
- **SupabaseLongRunningQuery**: p99 > 10s for 5m
- **SupabaseReplicationLag**: Lag > 30s for 5m
- **SupabaseWALSizeHigh**: WAL > 1GB for 10m

#### API Alerts

- **SupabaseHighErrorRate**: Error rate > 5% for 5m
- **SupabaseHighLatency**: p99 > 5s for 5m

### Configuring Alert Notifications

To receive alert notifications, configure Alertmanager:

1. Create an Alertmanager configuration file
2. Add notification channels (email, Slack, PagerDuty)
3. Update Prometheus to use Alertmanager

Example Alertmanager configuration:

```yaml
route:
  receiver: 'default-receiver'
  group_by: ['alertname', 'severity']

receivers:
  - name: 'default-receiver'
    email_configs:
      - to: 'alerts@indestructibleeco.io'
        from: 'prometheus@indestructibleeco.io'
        smarthost: 'smtp.gmail.com:587'
        auth_username: 'your-email@gmail.com'
        auth_password: 'your-app-password'
```

## Maintenance

### Updating Supabase Secret Key

```bash
kubectl create secret generic prometheus-secrets \
  --from-literal=SUPABASE_SECRET_KEY='new-sb-secret-key' \
  --namespace=monitoring \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl rollout restart deployment/prometheus -n monitoring
```

### Scaling Prometheus

Edit the Prometheus deployment:

```bash
kubectl edit deployment prometheus -n monitoring
```

Update resource limits:

```yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

### Backup Grafana Dashboards

```bash
# Export all dashboards
kubectl exec -n monitoring deployment/grafana -- \
  grafana-cli admin export-dashboards > dashboards-backup.json
```

## Troubleshooting

### Prometheus Not Scraping Supabase

1. Check Prometheus logs:
   ```bash
   kubectl logs -n monitoring deployment/prometheus
   ```

2. Verify secret is configured:
   ```bash
   kubectl get secret prometheus-secrets -n monitoring -o yaml
   ```

3. Test metrics endpoint manually:
   ```bash
   curl https://yrfxijooswpvdpdseswy.supabase.co/customer/v1/privileged/metrics \
     --user 'service_role:YOUR_SECRET_KEY'
   ```

### Grafana Not Connecting to Prometheus

1. Check Grafana logs:
   ```bash
   kubectl logs -n monitoring deployment/grafana
   ```

2. Verify Prometheus service:
   ```bash
   kubectl get svc prometheus -n monitoring
   ```

3. Test connection from Grafana pod:
   ```bash
   kubectl exec -n monitoring deployment/grafana -- \
     curl http://prometheus:9090/api/v1/query?query=up
   ```

### SSL/TLS Certificate Issues

1. Verify Cloudflare certificate secret exists:
   ```bash
   kubectl get secret cloudflare-origin-cert -n monitoring
   ```

2. Check Ingress configuration:
   ```bash
   kubectl get ingress -n monitoring
   kubectl describe ingress prometheus-ingress -n monitoring
   ```

3. Verify DNS records in Cloudflare:
   - Check CNAME records point to correct ingress IP
   - Ensure proxy status is set to "Proxied" (orange cloud)

4. Test SSL certificate:
   ```bash
   curl -v https://prometheus._cf-custom-hostname.autoecoops.io
   curl -v https://grafana._cf-custom-hostname.autoecoops.io
   ```

5. Check certificate expiration:
   ```bash
   echo | openssl s_client -connect prometheus._cf-custom-hostname.autoecoops.io:443 2>/dev/null | openssl x509 -noout -dates
   ```

### No Metrics Displaying in Dashboards

1. Verify Prometheus is scraping:
   - Go to Prometheus → Status → Targets
   - Check if `supabase-production` is UP

2. Check data retention:
   - Prometheus retains data for 30 days by default
   - Adjust `--storage.tsdb.retention.time` if needed

3. Verify time range:
   - Check Grafana dashboard time range
   - Ensure it covers the period when metrics were collected

## Security Best Practices

1. **Rotate Secret Keys Regularly**
   - Update Supabase secret key every 90 days
   - Update Prometheus secret and restart deployment

2. **Use RBAC**
   - Restrict access to monitoring namespace
   - Use service accounts with minimal permissions

3. **Enable TLS**
   - Use HTTPS for all external access
   - Configure Cloudflare Origin Certificates for SSL/TLS
   - Ensure Cloudflare DNS records are properly configured

4. **Secure Grafana**
   - Change default admin password
   - Enable anonymous viewing if needed
   - Configure authentication providers (OAuth, LDAP)

5. **Protect Cloudflare Certificates**
   - Store private keys securely
   - Never commit certificates to version control
   - Rotate certificates before expiration (15 years for Cloudflare Origin Certs)

## Performance Optimization

### Prometheus Optimization

1. **Adjust Scrape Interval**
   - Default: 60 seconds
   - Reduce to 30s for more granular data (increases load)

2. **Increase Retention**
   - Default: 30 days
   - Adjust based on storage capacity and requirements

3. **Enable Recording Rules**
   - Pre-compute expensive queries
   - Reduce dashboard load times

### Grafana Optimization

1. **Use Query Caching**
   - Enable caching in Prometheus datasource
   - Reduces load on Prometheus

2. **Optimize Dashboard Queries**
   - Use recording rules for complex queries
   - Limit time range for large datasets

## Next Steps

1. **Configure Alert Notifications**
   - Set up email, Slack, or PagerDuty integrations
   - Test alert delivery

2. **Create Custom Dashboards**
   - Add application-specific metrics
   - Create business intelligence dashboards

3. **Set Up Log Aggregation**
   - Integrate with Loki or ELK stack
   - Correlate logs with metrics

4. **Enable Distributed Tracing**
   - Integrate with Jaeger or Tempo
   - Trace requests across services

## References

- [Supabase Metrics API Documentation](https://supabase.com/docs/guides/platform/metrics-api)
- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kubernetes Monitoring](https://kubernetes.io/docs/tasks/debug/debug-cluster/resource-usage-monitoring/)

## Support

For issues or questions:

- Check the troubleshooting section
- Review Prometheus and Grafana logs
- Consult the official documentation

---

**Last Updated**: February 21, 2026
**Version**: 1.0.0
