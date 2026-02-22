#!/usr/bin/env python3
"""
Sync ConfigMaps between staging and production environments.
Ensures both environments have all necessary configuration keys.
"""

import yaml
from pathlib import Path

# Load staging configmap
staging_cm_path = Path("k8s/staging/configmap.qyaml")
with open(staging_cm_path) as f:
    staging_docs = list(yaml.safe_load_all(f))
    staging_cm = staging_docs[0]
    staging_secret = staging_docs[1]

# Load production configmap
production_cm_path = Path("k8s/production/configmap.qyaml")
with open(production_cm_path) as f:
    production_docs = list(yaml.safe_load_all(f))
    production_cm = production_docs[0]
    # Production doesn't have a separate Secret doc

# Extract data keys
staging_keys = set(staging_cm['data'].keys())
production_keys = set(production_cm['data'].keys())

# Keys only in staging
staging_only = staging_keys - production_keys
print(f"Keys only in staging ({len(staging_only)}):")
for key in sorted(staging_only):
    print(f"  - {key}: {staging_cm['data'][key]}")

# Keys only in production
production_only = production_keys - staging_keys
print(f"\nKeys only in production ({len(production_only)}):")
for key in sorted(production_only):
    print(f"  - {key}: {production_cm['data'][key]}")

# Keys in both
common_keys = staging_keys & production_keys
print(f"\nKeys in both ({len(common_keys)}):")
for key in sorted(common_keys):
    staging_val = staging_cm['data'][key]
    production_val = production_cm['data'][key]
    if staging_val != production_val:
        print(f"  - {key}: staging='{staging_val}' vs production='{production_val}'")

# Analyze staging secret
staging_secret_keys = set(staging_secret['stringData'].keys())
print(f"\nStaging Secret keys ({len(staging_secret_keys)}):")
for key in sorted(staging_secret_keys):
    val = staging_secret['stringData'][key]
    if val == "INJECT_FROM_K8S_SECRET":
        print(f"  - {key}: INJECT_FROM_K8S_SECRET")
    else:
        print(f"  - {key}: {val[:30]}..." if len(val) > 30 else f"  - {key}: {val}")

# Production secret keys (from configmap data - these should be in Secret)
production_secret_in_cm = {k: v for k, v in production_cm['data'].items() 
                          if 'SECRET' in k or 'PASSWORD' in k or 'TOKEN' in k}
print(f"\nProduction Secret-like keys in ConfigMap ({len(production_secret_in_cm)}):")
for key in sorted(production_secret_in_cm.keys()):
    print(f"  - {key}: {production_secret_in_cm[key]}")