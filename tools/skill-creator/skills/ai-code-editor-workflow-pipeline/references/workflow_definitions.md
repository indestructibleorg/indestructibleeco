# Workflow Definitions — AI Code Editor Pipeline

## 7-Phase Remediation Cycle

### Phase 1: Understand
**Purpose:** Build a complete mental model by answering: What is the current behavior? What is the expected behavior? What is the gap?

**Inputs:** Source code (AST parsing), execution logs (traceId, spanId), system state (K8s resources, configs, env vars), user descriptions.

**Processing:** Parse code structure → Analyze execution logs → Capture system state → Synthesize mental model.

**Outputs:**
```json
{
  "current_behavior": { "description": "...", "symptoms": [...], "frequency": "..." },
  "expected_behavior": { "description": "...", "slo": { "availability": 0.9999, "latency_p95_ms": 200 } },
  "gap_analysis": { "latency_gap_ms": 5000, "error_rate_gap": 0.5 },
  "code_structure": { "files": [...], "functions": 45, "dependencies": [...] }
}
```

**Verification:** Current behavior is observable and reproducible. Expected behavior is quantified. Gap is specific and measurable.

### Phase 2: Retrieve
**Purpose:** Fetch traceable, citable information from code repositories, documentation, knowledge bases, and external dependencies.

**Sources:** Code repository (symbol search, call graphs, dependency trees, git history), documentation (API docs, architecture docs, runbooks), knowledge base (vector search via Memory Hub, similar past cases), external data (CVE databases, license info).

**Outputs:**
```json
{
  "code_snippets": [{ "file": "pool.py", "line": 42, "context": "..." }],
  "documentation": [{ "title": "...", "url": "..." }],
  "similar_cases": [{ "incident_id": "INC-2024-001", "resolution": "..." }],
  "dependency_info": { "psycopg2": { "version": "2.9.1", "cves": [...] } }
}
```

**Verification:** Every retrieved item is traceable with source, location, and context. No vague associations.

### Phase 3: Analyze
**Purpose:** Identify root cause through structured decomposition and causal verification.

**Techniques:** Static analysis (code quality, security patterns, complexity), dynamic analysis (debugging, execution tracing, profiling), causal graphs (variable flow, control flow, data flow), root cause methods (5 Why, Fishbone, Change analysis), hypothesis generation (create falsifiable hypotheses and test them).

**Outputs:**
```json
{
  "root_causes": [{ "cause": "...", "evidence": "...", "impact": "..." }],
  "hypotheses": [{ "hypothesis": "...", "verified": true }],
  "causal_graph": {...}
}
```

**Verification:** Root cause is structural (system flaw, logic error, process gap), not symptomatic.

### Phase 4: Reason
**Purpose:** Derive concrete solutions by evaluating multiple options and selecting the optimal path.

**Steps:** Generate candidates → Evaluate side effects → Assess complexity → Estimate resources → Select optimal path.

**Outputs:**
```json
{
  "candidate_solutions": [{ "id": "SOL-1", "strategy": "...", "complexity": "low", "risk": "minimal" }],
  "selected_solution": "SOL-1",
  "modification_plan": [{ "file": "pool.py", "change": "...", "line": 42 }]
}
```

### Phase 5: Remediate (Consolidate → Integrate)
**Purpose:** Execute the complete fix from code changes through deployment.

**5a Consolidate:** Merge all pending changes into a single unified patch. Eliminate duplicates, resolve conflicts, ensure logical consistency.

**5b Integrate:** Apply the consolidated patch to the target system. Commit, push, trigger CI/CD. Verify the system compiles and runs.

**Outputs:**
```json
{
  "code_changes": [{ "file": "pool.py", "diff": "..." }],
  "commit_sha": "abc123",
  "test_results": { "unit_tests": { "passed": 45, "failed": 0 } },
  "deployment_status": "deployed"
}
```

### Phase 6: Validate (Recursive)
**Purpose:** Ensure the fix is correct through multiple validation layers.

**Layers:** Static analysis (SAST, code quality) → Integration tests (API contracts, dependency compatibility) → Security patterns (dangerous function detection) → CI Validator Engine (governance, identity) → Policy validation (OPA/Kyverno).

**Recursive Loop:** Propose Fix → Test → Confirm No New Risk → Pass? YES → Approve. NO → Refine → Repeat.

**Success Criteria:** All layers pass. No new risks. False positive rate < 10%. Success rate >= 90%.

### Phase 7: Audit
**Purpose:** Create complete, immutable traceability for compliance and accountability.

**Components:** PBOM/AI-BOM tracking, cosign signatures, SLSA provenance, immutable storage (Object Lock, append-only DB), compliance reports (SOC2, ISO27001).

**Outputs:**
```json
{
  "trace_id": "uuid",
  "actor": "ai-code-editor-workflow-pipeline",
  "commit_sha": "abc123",
  "content_hash": "sha256:...",
  "compliance_tags": ["slsa-l3", "sbom", "soc2"],
  "governance_stamp": { "uri": "indestructibleeco://...", "urn": "urn:indestructibleeco:..." }
}
```

## Data Flow Between Phases

```
Understand → { mental_model } → Retrieve
Retrieve → { code_snippets, docs, cases } → Analyze
Analyze → { root_causes, hypotheses } → Reason
Reason → { selected_solution, plan } → Consolidate
Consolidate → { unified_patch } → Integrate
Integrate → { commit_sha } → Validate
Validate → { pass/fail, success_rate } → Audit
Audit → { trace_id, signatures, compliance } → DONE
```