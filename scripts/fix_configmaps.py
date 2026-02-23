#!/usr/bin/env python3
"""
Fix and sync ConfigMaps between staging and production environments.
This script will:
1. Add missing AI/engine config keys to production
2. Add missing security/observability keys to staging
3. Move secret-like keys from production ConfigMap to Secret
4. Ensure proper environment-specific values
"""

import yaml
from pathlib import Path

def load_qyaml(path):
    """Load a .qyaml file and return all documents."""
    with open(path) as f:
        return list(yaml.safe_load_all(f))

def save_qyaml(path, docs):
    """Save documents to a .qyaml file."""
    with open(path, 'w') as f:
        for i, doc in enumerate(docs):
            yaml.dump(doc, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
            if i < len(docs) - 1:
                f.write('---\n')

# Load staging configmap
staging_docs = load_qyaml("k8s/staging/configmap.qyaml")
staging_cm = staging_docs[0]
staging_secret = staging_docs[1]
staging_governance = staging_docs[2]

# Load production configmap
production_docs = load_qyaml("k8s/production/configmap.qyaml")
production_cm = production_docs[0]
# Check if there's a governance block (3rd doc)
if len(production_docs) >= 3 and 'document_metadata' in production_docs[2]:
    production_governance = production_docs[2]
else:
    # Create a new governance block for production
    production_governance = {
        'document_metadata': {
            'unique_id': 'eco-prod-cm-0001-0001-000000000001',
            'uri': 'eco-base://k8s/eco-production/configmap/eco-config',
            'urn': 'urn:eco-base:k8s:eco-production:configmap:eco-config:eco-prod-cm-0001-0001-000000000001',
            'target_system': 'gke-eco-production',
            'cross_layer_binding': ['api-gateway', 'ai-service', 'api-service', 'web-frontend'],
            'schema_version': 'v8',
            'generated_by': 'yaml-toolkit-v8',
            'created_at': '2026-02-20T00:00:00.000Z'
        },
        'governance_info': {
            'owner': 'platform-team',
            'approval_chain': ['platform-team'],
            'compliance_tags': ['zero-trust', 'soc2', 'config', 'production'],
            'lifecycle_policy': 'active'
        },
        'registry_binding': {
            'service_endpoint': 'n/a',
            'discovery_protocol': 'k8s-dns',
            'health_check_path': 'n/a',
            'registry_ttl': 0
        },
        'vector_alignment_map': {
            'alignment_model': 'BAAI/bge-large-en-v1.5',
            'coherence_vector_dim': 1024,
            'function_keyword': ['configmap', 'production', 'environment', 'config'],
            'contextual_binding': 'eco-config -> [api-gateway, ai-service, api-service, web-frontend]'
        }
    }

# === FIX STAGING CONFIGMAP ===
# Add missing security/observability keys from production
staging_cm['data']['ECO_CORS_ORIGINS'] = "https://staging.autoecoops.io,https://api-staging.autoecoops.io"
staging_cm['data']['ECO_RATE_LIMIT_RPS'] = "100"
staging_cm['data']['ECO_RATE_LIMIT_BURST'] = "200"
staging_cm['data']['ECO_METRICS_ENABLED'] = "true"
staging_cm['data']['ECO_LOG_FORMAT'] = "json"
staging_cm['data']['ECO_TRACING_ENABLED'] = "true"
staging_cm['data']['ECO_GATEWAY_PORT'] = "8000"

# === FIX PRODUCTION CONFIGMAP ===
# Add missing AI/engine config keys from staging
production_cm['data']['ECO_HOST'] = "0.0.0.0"
production_cm['data']['ECO_PORT'] = "8000"
production_cm['data']['ECO_WORKERS'] = "4"
production_cm['data']['ECO_DEFAULT_ENGINE'] = "vllm"
production_cm['data']['ECO_DEFAULT_MODEL'] = "meta-llama/Llama-3.1-8B-Instruct"
production_cm['data']['ECO_EMBEDDING_MODEL'] = "BAAI/bge-large-en-v1.5"
production_cm['data']['ECO_ENGINE_TIMEOUT_SECONDS'] = "120"
production_cm['data']['ECO_MAX_CONCURRENT_REQUESTS'] = "128"
production_cm['data']['ECO_REQUEST_QUEUE_SIZE'] = "2048"
production_cm['data']['ECO_MODEL_CACHE_DIR'] = "/models"

# VLLM config
production_cm['data']['ECO_VLLM_HOST'] = "vllm-svc"
production_cm['data']['ECO_VLLM_PORT'] = "8001"
production_cm['data']['ECO_VLLM_GPU_MEMORY_UTILIZATION'] = "0.90"
production_cm['data']['ECO_VLLM_MAX_MODEL_LEN'] = "32768"
production_cm['data']['ECO_VLLM_TENSOR_PARALLEL_SIZE'] = "1"

# TGI config
production_cm['data']['ECO_TGI_HOST'] = "tgi-svc"
production_cm['data']['ECO_TGI_PORT'] = "8002"

# SGLang config
production_cm['data']['ECO_SGLANG_HOST'] = "sglang-svc"
production_cm['data']['ECO_SGLANG_PORT'] = "8003"

# Ollama config
production_cm['data']['ECO_OLLAMA_HOST'] = "ollama-svc"
production_cm['data']['ECO_OLLAMA_PORT'] = "11434"

# Service URLs
production_cm['data']['ECO_AI_SERVICE_URL'] = "http://eco-ai-svc.eco-production.svc.cluster.local:8001"
production_cm['data']['ECO_API_SERVICE_URL'] = "http://eco-api-svc.eco-production.svc.cluster.local:3000"
production_cm['data']['ECO_ENABLE_TRACING'] = "true"

# Remove secret-like keys from production ConfigMap (they should be in Secret)
secret_keys_to_remove = ['ECO_SECRET_KEY', 'ECO_POSTGRES_PASSWORD', 'ECO_JWT_SECRET', 
                         'ECO_POSTGRES_USER', 'ECO_SUPABASE_URL', 'ECO_SUPABASE_ANON_KEY', 
                         'ECO_SUPABASE_SERVICE_ROLE_KEY']
for key in secret_keys_to_remove:
    if key in production_cm['data']:
        del production_cm['data'][key]

# === CREATE PRODUCTION SECRET ===
production_secret = {
    'apiVersion': 'v1',
    'kind': 'Secret',
    'metadata': {
        'name': 'eco-secrets',
        'namespace': 'eco-production',
        'labels': {
            'app.kubernetes.io/name': 'eco-base',
            'app.kubernetes.io/part-of': 'eco-base',
            'environment': 'production'
        }
    },
    'type': 'Opaque',
    'stringData': {
        'ECO_SECRET_KEY': 'INJECT_FROM_K8S_SECRET',
        'ECO_POSTGRES_USER': 'eco_app',
        'ECO_POSTGRES_PASSWORD': 'INJECT_FROM_K8S_SECRET',
        'ECO_REDIS_PASSWORD': '',
        'ECO_JWT_SECRET': 'INJECT_FROM_K8S_SECRET',
        'ECO_SUPABASE_URL': 'https://bqyghtwaitlfxysmoext.supabase.co',
        'ECO_SUPABASE_ANON_KEY': 'INJECT_FROM_K8S_SECRET',
        'ECO_SUPABASE_SERVICE_ROLE_KEY': 'INJECT_FROM_K8S_SECRET',
        'HF_TOKEN': '',
        'DATABASE_URL': 'INJECT_FROM_K8S_SECRET'
    }
}

# === SAVE UPDATED FILES ===

# Save staging (ConfigMap + Secret + Governance)
save_qyaml("k8s/staging/configmap.qyaml", [staging_cm, staging_secret, staging_governance])

# Save production (ConfigMap + Secret + Governance)
save_qyaml("k8s/production/configmap.qyaml", [production_cm, production_secret, production_governance])

print("✅ ConfigMaps synced successfully!")
print("\nStaging ConfigMap keys:", len(staging_cm['data']))
print("Staging Secret keys:", len(staging_secret['stringData']))
print("Production ConfigMap keys:", len(production_cm['data']))
print("Production Secret keys:", len(production_secret['stringData']))