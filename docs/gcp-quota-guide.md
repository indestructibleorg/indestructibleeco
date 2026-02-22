# GCP SSD Quota Increase Guide - IndestructibleEco

## Overview

This guide explains how to request and manage SSD quota increases for the IndestructibleEco production cluster deployment.

## Current Situation

### Cluster Status

- **eco-staging**: ✅ RUNNING (asia-east1)
- **eco-production**: ❌ DELETED (SSD quota exceeded)

### Quota Details

- **Region**: asia-east1
- **Current Limit**: 250 GB
- **Current Usage**: ~100 GB (staging cluster)
- **Required**: ~200 GB (production cluster)
- **Requested**: 500 GB (for future growth)

## Manual Quota Request

### Step 1: Open GCP Console

Navigate to the Quotas page:
```
https://console.cloud.google.com/iam-admin/quotas?project=my-project-ops-1991
```

### Step 2: Filter Quotas

1. Click "Filter" button
2. Set filters:
   - **Service**: Compute Engine
   - **Metric**: SSD Total Storage
   - **Region**: asia-east1

### Step 3: Select Quota

1. Find "SSD Total Storage" in asia-east1
2. Click the quota entry
3. Click "Edit Quotas" button

### Step 4: Request Increase

1. **New Limit**: Enter `500` (GB)
2. **Justification**: Provide the following:
   ```
   Production cluster deployment for IndestructibleEco platform.
   Current staging cluster uses ~100 GB. Production cluster requires ~200 GB.
   Requesting 500 GB to accommodate future growth and high availability.
   ```

### Step 5: Submit Request

1. Review request details
2. Click "Submit Request"
3. Note the request ID for tracking

## Automated Request

Use the provided script to automate the process:

```bash
# Make script executable
chmod +x scripts/setup-gcp-quota.sh

# Run script
./scripts/setup-gcp-quota.sh
```

The script will:

- Check gcloud CLI installation
- Verify GCP authentication
- Display current quota status
- Open GCP Console with pre-filtered quotas page
- Provide step-by-step instructions

## Monitoring Quota Status

### Check Current Quota

```bash
gcloud compute regions describe asia-east1 \
  --format="json(quotas)" \
  --filter="quotas.metric='SSD_TOTAL_STORAGE_GB'"
```

### Check All Quotas

```bash
gcloud compute regions describe asia-east1 --format="json(quotas)"
```

### Expected Output

```json
{
  "quotas": [
    {
      "metric": "SSD_TOTAL_STORAGE_GB",
      "limit": 500.0,
      "usage": 100.0,
      "unit": "GB"
    }
  ]
}
```

## Approval Timeline

- **Standard Requests**: 1-2 business days
- **Emergency Requests**: Contact GCP Support
- **Auto-Approved**: Small increases (< 50%) may be auto-approved

## After Approval

Once quota is approved:

1. **Verify Quota**:
   ```bash
   gcloud compute regions describe asia-east1 \
     --format="json(quotas)" \
     --filter="quotas.metric='SSD_TOTAL_STORAGE_GB'"
   ```

2. **Recreate Production Cluster**:
   Follow `docs/gke-operations.md` for cluster recreation steps.

3. **Deploy Production Manifests**:
   ```bash
   kubectl apply -f k8s/production/
   ```

## Troubleshooting

### Request Denied

If request is denied:

1. Review denial reason in GCP Console
2. Contact GCP Support for clarification
3. Consider alternative regions with higher quotas

### Quota Not Updated

If quota is approved but not reflected:

1. Wait 15-30 minutes for propagation
2. Clear gcloud cache: `gcloud auth application-default revoke`
3. Re-authenticate: `gcloud auth login`
4. Check quota again

### Insufficient Quota

If 500 GB is still insufficient:

1. Monitor actual usage: `gcloud compute disks list`
2. Request additional quota
3. Consider using regional persistent disks instead of SSD

## Best Practices

1. **Monitor Usage**: Regularly check quota usage
2. **Plan Ahead**: Request quota increases before deployment
3. **Document Requests**: Keep track of request IDs and justifications
4. **Use Efficient Storage**: Use appropriate disk types (SSD vs Standard)
5. **Clean Up Resources**: Delete unused disks and clusters

## Governance

- **Owner**: indestructibleorg
- **Policy**: zero-trust
- **Compliance**: indestructibleeco v1.0
- **Audit**: All quota requests logged in GCP

## References

- [GCP Quotas Documentation](https://cloud.google.com/docs/quota)
- [Compute Engine Quotas](https://cloud.google.com/compute/quotas)
- [GKE Resource Limits](https://cloud.google.com/kubernetes-engine/quotas)

## Next Steps

1. Submit quota increase request
2. Monitor approval status
3. Recreate eco-production cluster after approval
4. Deploy production workloads
5. Set up monitoring and alerting
