# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# GL Layer Mapping Guide
**ECO-Layer: GL00-99 (Meta)**
**Closure-Signal: policy, manifest**

## Overview

This document describes how the ETL Pipeline components map to the GL (Governance Layer) framework defined in Machine-Native-Ops.

## GL Layer Structure

### GL00-09: Strategic Layer

**Purpose:** Vision, architecture, decisions, risk, compliance

**Components:**
- `controlplane/governance/policies/etl-pipeline-governance.yaml`
  - Governance principles and policies
  - Compliance requirements (GDPR, SOC2, HIPAA)
  - Risk mitigation strategies
  - Evidence generation requirements

**Closure Signals:** policy, audit, evidence

---

### GL01: Baseline Layer

**Purpose:** Baseline standards and configuration

**Components:**
- `controlplane/baseline/etl-pipeline-baseline.yaml`
  - Performance baselines (throughput, latency)
  - Reliability standards (uptime, error rate)
  - Security baselines (encryption, authentication)
  - Data quality standards

**Closure Signals:** baseline, manifest

---

### GL06: Root Policy Layer

**Purpose:** Naming, authorization, validation policies

**Components:**
- `root-policy/naming-convention/etl-naming-registry.yaml`
  - Directory naming rules (kebab-case)
  - File naming rules (kebab/snake_case)
  - Database naming conventions (snake_case)
  - Reserved words and forbidden extensions

**Closure Signals:** naming, schema

---

### GL30-49: Execution Layer

**Purpose:** Templates, Schema, automation, configuration

**Components:**
- `workspace/projects/etl-pipeline/src/extractors/`
- `workspace/projects/etl-pipeline/src/transformers/`
- `workspace/projects/etl-pipeline/src/loaders/`
- `workspace/projects/etl-pipeline/src/pipeline/`
- `workspace/projects/etl-pipeline/src/sync/`

**Closure Signals:** artifact, manifest

---

### GL50-59: Observability Layer

**Purpose:** Monitoring, metrics, alerts, insights

**Components:**
- `workspace/projects/etl-pipeline/src/monitoring/`

**Closure Signals:** metrics, alerts, insights

---

### GL90-99: Meta Layer

**Purpose:** Naming conventions, semantic definitions, validation

**Components:**
- `tools/etl/pipeline_validator.py`
- `root-policy/naming-convention/etl-naming-registry.yaml`

**Closure Signals:** validation, schema, naming