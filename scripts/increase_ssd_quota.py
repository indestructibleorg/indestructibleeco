#!/usr/bin/env python3
"""
SSD Quota Increase Script for IndestructibleEco

This script automates the process of requesting SSD quota increases for GKE clusters.
"""

import argparse
import json
import os
import sys
from datetime import datetime

try:
    from google.cloud import compute_v1
    from google.auth import default
except ImportError:
    print("Error: google-cloud-compute not installed")
    print("Install with: pip install google-cloud-compute")
    sys.exit(1)


class SSDQuotaManager:
    """SSD Quota Management"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.regions_client = compute_v1.RegionsClient()
        
    def get_current_quota(self, region: str) -> dict:
        """Get current SSD quota for a region"""
        try:
            region_obj = self.regions_client.get(project=self.project_id, region=region)
            
            for quota in region_obj.quotas:
                if quota.metric == "SSD_TOTAL_STORAGE_GB":
                    return {
                        "metric": quota.metric,
                        "limit": quota.limit,
                        "usage": quota.usage,
                        "unit": quota.unit,
                        "region": region,
                        "timestamp": datetime.now().isoformat()
                    }
            
            return {"error": "SSD_TOTAL_STORAGE_GB quota not found"}
        except Exception as e:
            return {"error": str(e)}
    
    def request_quota_increase(
        self,
        region: str,
        current_limit: float,
        requested_limit: float,
        justification: str
    ) -> dict:
        """Request SSD quota increase"""
        # Note: Actual quota requests require GCP Console UI
        # This script generates the request details for manual submission
        
        request = {
            "request_id": f"quota-{region}-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "project_id": self.project_id,
            "region": region,
            "metric": "SSD_TOTAL_STORAGE_GB",
            "current_limit": current_limit,
            "requested_limit": requested_limit,
            "increase_amount": requested_limit - current_limit,
            "increase_percentage": ((requested_limit - current_limit) / current_limit) * 100,
            "justification": justification,
            "status": "pending_manual_submission",
            "timestamp": datetime.now().isoformat(),
            "console_url": f"https://console.cloud.google.com/iam-admin/quotas?project={self.project_id}"
        }
        
        return request
    
    def generate_request_summary(self, request: dict) -> str:
        """Generate human-readable request summary"""
        summary = f"""
## SSD Quota Increase Request Summary

**Request ID**: {request['request_id']}
**Project**: {request['project_id']}
**Region**: {request['region']}
**Metric**: {request['metric']}

### Quota Details
- **Current Limit**: {request['current_limit']} GB
- **Requested Limit**: {request['requested_limit']} GB
- **Increase Amount**: {request['increase_amount']} GB
- **Increase Percentage**: {request['increase_percentage']:.1f}%

### Justification
{request['justification']}

### Next Steps
1. Open GCP Console: {request['console_url']}
2. Filter by Service: Compute Engine, Metric: SSD Total Storage, Region: {request['region']}
3. Click "Edit Quotas"
4. Enter new limit: {request['requested_limit']} GB
5. Paste justification
6. Submit request

### Approval Timeline
- Standard requests: 1-2 business days
- Auto-approved: Small increases (< 50%) may be auto-approved

### After Approval
1. Verify quota: gcloud compute regions describe {request['region']}
2. Recreate production cluster
3. Deploy production workloads
"""
        return summary


def main():
    parser = argparse.ArgumentParser(
        description='Manage SSD quota for IndestructibleEco GKE clusters'
    )
    parser.add_argument(
        '--action',
        choices=['check', 'request', 'summary'],
        required=True,
        help='Action to perform'
    )
    parser.add_argument(
        '--region',
        default=os.getenv('GCP_REGION', 'asia-east1'),
        help='GCP region'
    )
    parser.add_argument(
        '--project-id',
        default=os.getenv('GCP_PROJECT', 'my-project-ops-1991'),
        help='GCP project ID'
    )
    parser.add_argument(
        '--current-limit',
        type=float,
        help='Current SSD limit in GB'
    )
    parser.add_argument(
        '--requested-limit',
        type=float,
        help='Requested SSD limit in GB'
    )
    parser.add_argument(
        '--justification',
        help='Justification for quota increase'
    )
    parser.add_argument(
        '--output-json',
        action='store_true',
        help='Output results as JSON'
    )
    
    args = parser.parse_args()
    
    # Initialize quota manager
    quota_manager = SSDQuotaManager(args.project_id)
    
    if args.action == 'check':
        print(f"Checking SSD quota for {args.region}...", file=sys.stderr if args.output_json else sys.stdout)
        quota = quota_manager.get_current_quota(args.region)
        
        if 'error' in quota:
            print(f"Error: {quota['error']}", file=sys.stderr)
            sys.exit(1)
        
        if args.output_json:
            print(json.dumps(quota, indent=2))
        else:
            print(f"\n✓ Current SSD Quota for {args.region}:")
            print(f"  Limit: {quota['limit']} GB")
            print(f"  Usage: {quota['usage']} GB")
            print(f"  Available: {quota['limit'] - quota['usage']} GB")
            print(f"  Utilization: {(quota['usage'] / quota['limit']) * 100:.1f}%")
    
    elif args.action == 'request':
        print(f"Requesting SSD quota increase for {args.region}...", file=sys.stderr if args.output_json else sys.stdout)
        
        if not args.current_limit or not args.requested_limit:
            print("Error: --current-limit and --requested-limit are required", file=sys.stderr)
            sys.exit(1)
        
        if not args.justification:
            print("Error: --justification is required", file=sys.stderr)
            sys.exit(1)
        
        request = quota_manager.request_quota_increase(
            args.region,
            args.current_limit,
            args.requested_limit,
            args.justification
        )
        
        if args.output_json:
            print(json.dumps(request, indent=2))
        else:
            summary = quota_manager.generate_request_summary(request)
            print(summary)
    
    elif args.action == 'summary':
        print("Generating quota summary...")
        quota = quota_manager.get_current_quota(args.region)
        
        if 'error' in quota:
            print(f"Error: {quota['error']}")
            sys.exit(1)
        
        summary = f"""
## SSD Quota Summary

**Project**: {args.project_id}
**Region**: {args.region}

### Current Status
- **Limit**: {quota['limit']} GB
- **Usage**: {quota['usage']} GB
- **Available**: {quota['limit'] - quota['usage']} GB
- **Utilization**: {(quota['usage'] / quota['limit']) * 100:.1f}%

### Recommendations
"""
        if quota['usage'] / quota['limit'] > 0.8:
            summary += "- ⚠️  WARNING: Quota usage is above 80%\n"
            summary += "- Consider requesting a quota increase\n"
            summary += f"- Recommended new limit: {quota['limit'] * 2} GB\n"
        else:
            summary += "- ✓ Quota usage is healthy\n"
            summary += "- No immediate action required\n"
        
        print(summary)


if __name__ == '__main__':
    main()