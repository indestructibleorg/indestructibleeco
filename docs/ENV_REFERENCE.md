# IndestructibleEco Environment Variables Reference

URI: indestructibleeco://docs/ENV_REFERENCE

All environment variables use the `ECO_*` prefix for namespace isolation. A complete template is available at `.env.example` in the repository root.

## Application

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_ENVIRONMENT` | `development` | Runtime environment (`development`, `staging`, `production`) |
| `ECO_LOG_LEVEL` | `info` | Log level (`debug`, `info`, `warn`, `error`) |
| `ECO_LOG_FORMAT` | `json` | Log format (`json`, `pretty`) |

## AI Service

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_AI_HTTP_PORT` | `8001` | AI service HTTP port |
| `ECO_AI_GRPC_PORT` | `8000` | AI service gRPC port |
| `ECO_AI_MODELS` | `vllm,ollama,tgi,sglang` | Comma-separated list of enabled engine adapters |
| `ECO_AI_SERVICE_URL` | `http://localhost:8001` | AI service URL (used by root gateway proxy) |

## API Gateway

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_API_PORT` | `3000` | API gateway HTTP port |
| `ECO_API_SERVICE_URL` | `http://localhost:3000` | API gateway URL (used by root gateway proxy) |
| `ECO_AI_SERVICE_HTTP` | `http://localhost:8001` | AI service HTTP URL (used by API gateway proxy) |
| `ECO_AI_SERVICE_GRPC` | `localhost:8000` | AI service gRPC address (used by API gateway) |

## Authentication

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_JWT_SECRET` | `dev-secret-change-in-production` | JWT signing secret. **Must change in production.** |
| `ECO_SUPABASE_URL` | `http://localhost:54321` | Supabase project URL |
| `ECO_SUPABASE_ANON_KEY` | (empty) | Supabase anonymous key (client-side) |
| `ECO_SUPABASE_SERVICE_KEY` | (empty) | Supabase service role key (server-side, bypasses RLS) |

## Redis / Celery

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_REDIS_URL` | `redis://localhost:6379` | Redis connection URL |
| `ECO_CELERY_BROKER` | `redis://localhost:6379/0` | Celery broker URL |
| `ECO_CELERY_BACKEND` | `redis://localhost:6379/1` | Celery result backend URL |

## Vector Alignment

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_VECTOR_DIM` | `1024` | Default vector dimension |
| `ECO_ALIGNMENT_MODEL` | `quantum-bert-xxl-v1` | Default alignment model |
| `ECO_ALIGNMENT_TOLERANCE` | `0.001` | Alignment tolerance threshold |

## FAISS Index

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_FAISS_ENABLED` | `true` | Enable FAISS vector index |
| `ECO_FAISS_INDEX_TYPE` | `IVFFlat` | FAISS index type (`IVFFlat`, `IVFPQ`, `Flat`) |
| `ECO_FAISS_NPROBE` | `16` | Number of clusters to probe during search |
| `ECO_FAISS_NLIST` | `256` | Number of Voronoi cells for IVF indexes |
| `ECO_FAISS_USE_GPU` | `false` | Enable GPU-accelerated FAISS |
| `ECO_FAISS_PERSIST_DIR` | `/tmp/eco-faiss` | Directory for persistent FAISS index storage |

## Elasticsearch Index

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_ES_ENABLED` | `false` | Enable Elasticsearch index |
| `ECO_ES_HOSTS` | `http://localhost:9200` | Comma-separated Elasticsearch hosts |
| `ECO_ES_INDEX_PREFIX` | `eco-vectors` | Index name prefix |
| `ECO_ES_USERNAME` | (empty) | Elasticsearch username |
| `ECO_ES_PASSWORD` | (empty) | Elasticsearch password |
| `ECO_ES_VERIFY_CERTS` | `true` | Verify TLS certificates |
| `ECO_ES_TIMEOUT` | `30` | Request timeout in seconds |
| `ECO_ES_MAX_RETRIES` | `3` | Maximum retry attempts |

## Neo4j Index

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_NEO4J_ENABLED` | `false` | Enable Neo4j graph index |
| `ECO_NEO4J_URI` | `bolt://localhost:7687` | Neo4j Bolt URI |
| `ECO_NEO4J_USERNAME` | `neo4j` | Neo4j username |
| `ECO_NEO4J_PASSWORD` | (empty) | Neo4j password |
| `ECO_NEO4J_DATABASE` | `neo4j` | Neo4j database name |
| `ECO_NEO4J_POOL_SIZE` | `50` | Connection pool size |

## Engine Endpoints

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_VLLM_URL` | `http://localhost:8100` | vLLM engine endpoint |
| `ECO_TGI_URL` | `http://localhost:8101` | TGI engine endpoint |
| `ECO_OLLAMA_URL` | `http://localhost:11434` | Ollama engine endpoint |
| `ECO_SGLANG_URL` | `http://localhost:8102` | SGLang engine endpoint |
| `ECO_TENSORRT_URL` | `http://localhost:8103` | TensorRT-LLM engine endpoint |
| `ECO_DEEPSPEED_URL` | `http://localhost:8104` | DeepSpeed engine endpoint |
| `ECO_LMDEPLOY_URL` | `http://localhost:8105` | LMDeploy engine endpoint |

## CORS

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated allowed CORS origins |

## Rate Limiting

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_RATE_LIMIT_AUTHENTICATED` | `100` | Requests per window for authenticated users |
| `ECO_RATE_LIMIT_PUBLIC` | `10` | Requests per window for unauthenticated users |
| `ECO_RATE_LIMIT_WINDOW_MS` | `60000` | Rate limit window in milliseconds |

## Service Discovery & Tracing

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_CONSUL_ENDPOINT` | `http://localhost:8500` | Consul service discovery endpoint |
| `ECO_JAEGER_ENDPOINT` | `http://localhost:14268/api/traces` | Jaeger tracing endpoint |

## Database

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_DB_PASSWORD` | `eco_dev_password` | PostgreSQL password (Docker Compose) |

## Monitoring

| Variable | Default | Description |
|----------|---------|-------------|
| `GF_ADMIN_PASSWORD` | `eco_grafana` | Grafana admin password |

## Audit

| Variable | Default | Description |
|----------|---------|-------------|
| `ECO_AUDIT_LOG_DIR` | `.eco-audit` | Directory for governance audit logs (JSONL) |

---

## Production Checklist

Before deploying to production, ensure these variables are properly configured:

- [ ] `ECO_ENVIRONMENT=production`
- [ ] `ECO_JWT_SECRET` set to a cryptographically random value (`openssl rand -hex 32`)
- [ ] `ECO_SUPABASE_URL` pointing to production Supabase instance
- [ ] `ECO_SUPABASE_SERVICE_KEY` set (never commit to Git)
- [ ] `ECO_REDIS_URL` pointing to production Redis (with TLS if applicable)
- [ ] `ECO_CORS_ORIGINS` restricted to production domains only
- [ ] `ECO_LOG_LEVEL=info` (not `debug`)
- [ ] `ECO_DB_PASSWORD` set to a strong password
- [ ] All engine URLs (`ECO_VLLM_URL`, etc.) pointing to production endpoints
- [ ] `ECO_FAISS_PERSIST_DIR` pointing to persistent storage (not `/tmp`)
- [ ] `GF_ADMIN_PASSWORD` changed from default

## Related Documentation

- [Deployment Guide](DEPLOYMENT.md)
- [Architecture Overview](ARCHITECTURE.md)
- [Developer Guide](DEVELOPER_GUIDE.md)
