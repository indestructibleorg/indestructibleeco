# Decentralized Platform Architecture v2

## Overview

This directory contains the **decentralized platform ecosystem** — a clean restructuring
of the previous monolithic `platforms/` layout into independently deployable, self-contained
platform units. Every platform ships with built-in **sandbox**, **container**, and
**environment** isolation.

## Architecture Principles

1. **Decentralized** — Each platform is fully self-contained. No cross-platform imports.
   Communication happens exclusively through the EventBus protocol or HTTP APIs.
2. **Sandbox-First** — Every workload runs inside a sandbox with resource limits,
   filesystem isolation, and network policies. No platform trusts external input.
3. **Clean Architecture** — Each platform follows domain / engines / sandbox / presentation
   layering. Domain has zero dependencies on infrastructure.
4. **Protocol-Driven** — The `_shared` kernel provides protocols (Engine, EventBus,
   HealthCheck, Lifecycle). Platforms depend on protocols, never on concrete implementations
   from other platforms.

## Platform Catalog

| Platform | Purpose | Key Engines |
|---|---|---|
| **_shared** | Shared kernel — sandbox/container/environment framework, cross-cutting protocols | ProcessSandbox, ContainerRuntime, EnvironmentManager |
| **automation-platform** | Instant execution, multi-agent pipelines, event-driven tasks | ExecutionEngine, PipelineOrchestrator, AgentPool |
| **governance-platform** | Policy enforcement, quality gates, dual-path reasoning | PolicyEngine, QualityGateEngine, ReasoningEngine |
| **runtime-platform** | Workflow DAGs, ETL pipelines, job scheduling | WorkflowEngine, ETLEngine, Scheduler |
| **data-platform** | Evidence lifecycle, data quality, replay debugging | EvidenceEngine, QualityEngine, ReplayEngine |
| **observability-platform** | Metrics, alerts, health monitoring | MetricsEngine, AlertEngine, HealthEngine |
| **security-platform** | Zero-tolerance enforcement, audit trails, isolation | EnforcementEngine, AuditEngine, IsolationEngine |
| **semantic-platform** | Semantic folding, vector indexing, inference | FoldingEngine, IndexingEngine, InferenceEngine |
| **infrastructure-platform** | Deployments, services, namespace provisioning | DeploymentEngine, ServiceEngine, Provisioner |
| **registry-platform** | Platform discovery, dependency tracking, namespaces | CatalogEngine, NamespaceEngine, DependencyEngine |

## Directory Layout

```
platforms/
├── _shared/                       # Shared kernel (protocols + sandbox framework)
│   ├── src/platform_shared/
│   │   ├── sandbox/               # Sandbox / Container / Environment
│   │   │   ├── runtime.py         # ProcessSandbox, InProcessSandbox
│   │   │   ├── container.py       # LocalContainerRuntime (docker/podman)
│   │   │   ├── environment.py     # LocalEnvironmentManager (dev/staging/prod)
│   │   │   ├── resource.py        # ResourceLimits, ResourceMonitor
│   │   │   ├── network.py         # NetworkPolicy, NetworkNamespace
│   │   │   └── storage.py         # VolumeManager, VolumeMount
│   │   ├── protocols/             # Cross-cutting contracts
│   │   │   ├── engine.py          # Engine protocol
│   │   │   ├── event_bus.py       # EventBus + LocalEventBus
│   │   │   ├── health.py          # HealthCheck + HealthReport
│   │   │   └── lifecycle.py       # Lifecycle states
│   │   └── domain/                # Shared value objects
│   │       ├── errors.py          # Error hierarchy
│   │       ├── platform_id.py     # PlatformId
│   │       └── version.py         # SemVer
│   └── tests/
│
├── {name}-platform/               # Each platform follows this layout
│   ├── pyproject.toml
│   ├── conftest.py
│   ├── src/{name}_platform/
│   │   ├── domain/                # Entities, value objects, events, exceptions
│   │   ├── engines/               # Core business logic
│   │   ├── sandbox/               # Platform-specific sandbox integration
│   │   └── presentation/          # FastAPI routers, CLI
│   └── tests/
│
├── automation/                    # ← Legacy (archived)
├── gl/                            # ← Legacy (archived)
├── gov-platform-assistant/        # ← Legacy (archived)
├── gov-platform-ide/              # ← Legacy (archived)
├── infrastructure/                # ← Legacy (archived)
├── ng-era-platforms/              # ← Legacy (archived)
├── quantum/                       # ← Legacy (archived)
└── registry/                      # ← Legacy (archived)
```

## Sandbox / Container / Environment

### Three Isolation Pillars

```
┌─────────────────────────────────────────────────────────────────┐
│                     Environment Manager                         │
│  Profiles: dev │ staging │ prod │ sandbox │ preview              │
│  Config injection · Secret management · Service discovery        │
├─────────────────────────────────────────────────────────────────┤
│                     Container Runtime                            │
│  OCI-compatible · Image management · Volume mounts               │
│  Health checks · Resource constraints · Security hardening       │
├─────────────────────────────────────────────────────────────────┤
│                     Sandbox Runtime                              │
│  Process isolation · Resource limits (CPU/mem/fds/procs)         │
│  Network policies · Filesystem isolation · Timeout enforcement   │
│  Audit logging · InProcessSandbox (for tests)                    │
└─────────────────────────────────────────────────────────────────┘
```

### Resource Limits

Every sandbox and container declares explicit resource budgets:

```python
ResourceLimits(
    cpu_cores=1.0,       # CPU cores
    memory_mb=512,       # Memory cap
    disk_mb=1024,        # Disk cap
    max_open_fds=256,    # File descriptor limit
    max_processes=32,    # PID limit
    max_threads=64,      # Thread limit
)
```

### Network Policies

Built-in policies: `POLICY_NO_NETWORK`, `POLICY_EGRESS_ONLY`, `POLICY_HTTP_ONLY`, `POLICY_ALLOW_ALL`.
Custom policies compose `NetworkRule` objects with direction, port, protocol, CIDR, and action.

### Environment Tiers

| Tier | Purpose | TTL |
|------|---------|-----|
| `dev` | Local development | ∞ |
| `staging` | Pre-production validation | ∞ |
| `prod` | Production | ∞ |
| `sandbox` | Ephemeral per-branch | configurable |
| `preview` | PR-based preview | configurable |

## Running Tests

```bash
# Shared kernel
cd platforms/_shared && python3 -m pytest tests/ -v

# Any platform
cd platforms/automation-platform && python3 -m pytest tests/ -v

# All platforms at once
for d in platforms/*-platform platforms/_shared; do
  echo "=== $d ===" && (cd "$d" && python3 -m pytest tests/ -v --override-ini="addopts=") || true
done
```

## Migration from Legacy

The legacy directories (`automation/`, `gl/`, `gov-platform-assistant/`, etc.) are preserved
for reference. Their functionality has been migrated into the new `*-platform/` directories:

| Legacy | New Platform |
|--------|-------------|
| `automation/instant/` | `automation-platform/` |
| `gov-platform-assistant/` | `governance-platform/` |
| `ng-era2-platforms/runtime/engine/` | `runtime-platform/` |
| `ng-era2-platforms/*/processing/` | `data-platform/` |
| `gl/observability/` | `observability-platform/` |
| `ng-era1-platforms/*/GL90-99-semantic-engine/` | `semantic-platform/` |
| `infrastructure/` | `infrastructure-platform/` |
| `registry/` | `registry-platform/` |
