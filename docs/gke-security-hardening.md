# GKE Security Hardening Guide - IndestructibleEco

## Overview

This guide explains how to secure GKE clusters by removing insecure `0.0.0.0/0` from master authorized networks.

## Current Security Status

### eco-staging Cluster

- **Master Authorized Networks**: ⚠️ 0.0.0.0/0 (INSECURE)
- **Risk**: Allows access from any IP address
- **Priority**: HIGH

### eco-production Cluster

- **Status**: Not yet created
- **Action**: Configure secure networks during creation

## Security Risks

### 0.0.0.0/0 in Authorized Networks

**Risks:**

- Allows unauthorized access to Kubernetes API server
- Exposes cluster to brute-force attacks
- Violates zero-trust security principles
- Non-compliant with security best practices

**Impact:**

- Unauthorized cluster management
- Potential data exfiltration
- Service disruption
- Compliance violations

## Manual Security Hardening

### Step 1: Get Current IP

```bash
# Get your current public IP
curl https://api.ipify.org
```

### Step 2: Add Your IP to Authorized Networks

```bash
# Add your IP to authorized networks
gcloud container clusters update eco-staging \
  --region=asia-east1 \
  --enable-master-authorized-networks \
  --master-authorized-networks=YOUR_IP/32
```

### Step 3: Remove 0.0.0.0/0

```bash
# Remove 0.0.0.0/0 from authorized networks
gcloud container clusters update eco-staging \
  --region=asia-east1 \
  --enable-master-authorized-networks \
  --master-authorized-networks=YOUR_IP/32,OTHER_IP/32
```

### Step 4: Verify Changes

```bash
# Check current authorized networks
gcloud container clusters describe eco-staging \
  --region=asia-east1 \
  --format="value(masterAuthorizedNetworks.cidrBlocks)"
```

## Automated Security Hardening

Use the provided script to automate the process:

```bash
# Make script executable
chmod +x scripts/harden-gke-security.sh

# Run script
./scripts/harden-gke-security.sh
```

The script will:

- Check current authorized networks
- Add your current IP to authorized networks
- Remove 0.0.0.0/0 from authorized networks
- Verify security hardening

## IP Address Management

### Required IPs

Add the following IPs to authorized networks:

**Administrator IPs:**

- Your office IP
- Your home IP
- VPN gateway IP

**CI/CD IPs:**

- GitHub Actions IPs (dynamic)
- Cloud Build IPs
- Other CI/CD system IPs

**Service IPs:**

- Monitoring systems
- Logging systems
- Backup systems

### GitHub Actions IPs

GitHub Actions uses dynamic IPs. Use one of these approaches:

**Option 1: Use GitHub-hosted runners with private network**

- Configure GitHub Actions to use self-hosted runners
- Add self-hosted runner IPs to authorized networks

**Option 2: Use Cloud NAT**

- Configure Cloud NAT for GKE nodes
- Allow GitHub Actions through Cloud NAT

**Option 3: Use IAP (Identity-Aware Proxy)**

- Configure IAP for GKE
- Use OAuth for authentication instead of IP restrictions

## Production Cluster Security

### Create Secure Production Cluster

```bash
gcloud container clusters create-auto eco-production \
  --region=asia-east1 \
  --project=my-project-ops-1991 \
  --release-channel=regular \
  --network=default \
  --subnetwork=default \
  --enable-master-authorized-networks \
  --master-authorized-networks=ADMIN_IP_1/32,ADMIN_IP_2/32,CI_CD_IP/32 \
  --enable-private-nodes \
  --enable-private-endpoint \
  --enable-master-authorized-networks \
  --quiet
```

### Private Cluster Configuration

For enhanced security, use private clusters:

```bash
gcloud container clusters create-auto eco-production \
  --region=asia-east1 \
  --project=my-project-ops-1991 \
  --enable-private-nodes \
  --enable-private-endpoint \
  --master-authorized-networks=ADMIN_IP_1/32,ADMIN_IP_2/32 \
  --enable-master-authorized-networks \
  --quiet
```

## Monitoring and Alerting

### Set Up Monitoring

```bash
# Create monitoring policy
gcloud alpha monitoring policies create \
  --policy-from-file=monitoring/gke-security-policy.yaml
```

### Alert on Unauthorized Access

Configure alerts for:

- Failed authentication attempts
- Access from unauthorized IPs
- Unusual API server activity

## Troubleshooting

### Cannot Access Cluster After Hardening

If you cannot access the cluster:

1. Verify your IP is in authorized networks
2. Check if you're using VPN
3. Try accessing from a different network
4. Contact GCP support if needed

### CI/CD Failures

If CI/CD fails after hardening:

1. Add CI/CD system IPs to authorized networks
2. Use self-hosted runners
3. Configure Cloud NAT
4. Use IAP for authentication

### Multiple Administrators

For multiple administrators:

1. Collect all administrator IPs
2. Add all IPs to authorized networks
3. Use VPN for consistent IP
4. Consider using IAP for better access control

## Security Best Practices

1. **Use Private Clusters**: Enable private nodes and endpoints
2. **Limit Authorized Networks**: Only add necessary IPs
3. **Use IAP**: Use Identity-Aware Proxy for access control
4. **Monitor Access**: Monitor API server access logs
5. **Regular Audits**: Regularly audit authorized networks
6. **Use VPN**: Use VPN for consistent IP addresses
7. **Rotate Keys**: Regularly rotate service account keys
8. **Enable Audit Logs**: Enable Cloud Audit Logs

## Governance

- **Owner**: indestructibleorg
- **Policy**: zero-trust
- **Compliance**: indestructibleeco v1.0
- **Audit**: All security changes logged in GCP

## References

- [GKE Security Best Practices](https://cloud.google.com/kubernetes-engine/docs/how-to/hardening-your-cluster)
- [Master Authorized Networks](https://cloud.google.com/kubernetes-engine/docs/how-to/private-clusters#add_authorized_networks)
- [Identity-Aware Proxy](https://cloud.google.com/iap/docs/using-tcp-forwarding)

## Next Steps

1. Add your current IP to authorized networks
2. Remove 0.0.0.0/0 from authorized networks
3. Add all administrator IPs
4. Configure CI/CD access
5. Set up monitoring and alerting
6. Create secure production cluster
7. Regularly audit authorized networks
