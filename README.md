# IndestructibleEco v1.0.0

Enterprise-grade AI Inference Backend with multi-engine routing, code folding/indexing engines, governance automation, and Kubernetes-native deployment.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Ingress (NGINX + TLS)                    │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                     API Gateway (FastAPI)                        │
│  ┌──────────┐ ┌───────────┐ ┌──────────┐ ┌──────────────────┐  │
│  │   Auth   │ │Rate Limit │ │ Metrics  │ │  Error Handler   │  │
│  └──────────┘ └───────────┘ └──────────┘ └──────────────────┘  │
└──────────────────────────────┬──────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────┐
│                    Inference Router                              │
│  Model Registry │ Load Balancer │ Request Queue │ Health Check  │
└───┬──────┬──────┬──────┬──────┬──────┬──────┬───────────────────┘
    │      │      │      │      │      │      │
    ▼      ▼      ▼      ▼      ▼      ▼      ▼
┌──────┐┌─────┐┌──────┐┌──────┐┌────────┐┌────────┐┌──────────┐
│ vLLM ││ TGI ││SGLang││Ollama││TRT-LLM ││LMDeploy││DeepSpeed │
└──────┘└─────┘└──────┘└──────┘└────────┘└────────┘└──────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    Engine Subsystems                             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────────────────┐│
│  │Code Folding  │ │  Compute     │ │  Index Engine            ││
│  │• Vector      │ │• Similarity  │ │• FAISS (vector)          ││
│  │• Graph       │ │• Clustering  │ │• Neo4j (graph)           ││
│  │• Hybrid      │ │• Reasoning   │ │• Elasticsearch (text)    ││
│  │• Realtime    │ │• Ranking     │ │• Hybrid Router           ││
│  └──────────────┘ └──────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

## Monorepo Structure

```
indestructibleeco/
├── packages/                    # Shared libraries
│   ├── ui-kit/                  # UI component library
│   ├── api-client/              # Backend API client SDK
│   ├── shared-types/            # Cross-platform TypeScript types
│   └── templates/               # Page templates
├── backend/
│   ├── services/
│   │   ├── api/                 # Main API service (Node.js)
│   │   ├── ai/                  # AI engine service (Python/FastAPI)
│   │   └── worker/              # Background task service
│   ├── libs/database/           # Shared DB models & migrations
│   └── k8s/                     # Kubernetes manifests
├── platforms/
│   ├── web-app/                 # React concept map & dashboard
│   ├── desktop-app/             # Electron app
│   └── *-bot/                   # Chat platform bots
├── ecosystem/                   # Monitoring, tracing, service discovery
├── tools/
│   └── skill-creator/           # Skill definition & validation toolchain
└── .github/workflows/           # CI/CD (shell-only, no third-party actions)
```

## Engine Subsystems

### Multi-Engine Inference (7 backends)
- **vLLM**: PagedAttention, continuous batching, prefix caching
- **TGI**: HuggingFace ecosystem, Flash Attention 2
- **SGLang**: RadixAttention, structured generation, 6.4x throughput
- **Ollama**: One-command local deployment, GGUF quantization
- **TensorRT-LLM**: NVIDIA FP8/FP4, kernel fusion
- **LMDeploy**: Dual-engine TurboMind + PyTorch, KV-cache quantization
- **DeepSpeed**: ZeRO optimization, distributed inference

### Code Folding Engine
- **Vector Folding**: Embedding + dimensionality reduction
- **Graph Folding**: Knowledge graph construction from code/docs
- **Hybrid Folding**: Combined vector + graph features
- **Realtime Index**: Incremental updates with LRU cache

### Compute Engine
- **Similarity**: Cosine, euclidean, dot product metrics
- **Clustering**: K-Means, DBSCAN, hierarchical with auto-k
- **Reasoning**: Deductive, inductive, abductive over graphs
- **Ranking**: BM25, vector reranking, RRF hybrid fusion

### Index Engine
- **FAISS**: High-performance vector similarity search
- **Neo4j**: Graph pattern matching and traversal
- **Elasticsearch**: Full-text search with code-aware tokenization
- **Hybrid Router**: Auto-routing with Reciprocal Rank Fusion

## Quick Start

```bash
# Local development
docker compose up -d
cd backend/services/ai && pip install -e ".[dev]"
uvicorn src.app:app --reload --port 8000

# Kubernetes
kubectl apply -k backend/k8s/base

# Validate skills
node tools/skill-creator/scripts/validate.js tools/skill-creator/skills/
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /v1/folding/fold` | Code folding (vector/graph/hybrid) |
| `POST /v1/compute/similarity` | Similarity computation |
| `POST /v1/compute/cluster` | Clustering analysis |
| `POST /v1/compute/reason` | Graph reasoning |
| `POST /v1/compute/rank` | Result ranking |
| `POST /v1/index/ingest` | Multi-backend ingestion |
| `POST /v1/index/search` | Hybrid search |
| `GET /health` | Service health |
| `GET /metrics` | Prometheus metrics |

## License

Apache-2.0