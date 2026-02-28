# AutoOps Enforced Workflow — v1.0

## UI output rules

Only these output types are allowed:

| Type | Description |
|------|-------------|
| `PATCH` | git diff / unified diff |
| `COMMANDS` | executable CLI commands |
| `FILES` | full file content (new or updated) |
| `TASKS` | actionable to-dos with path/command/acceptance |
| `NEED_INPUT` | produced when entry fields are missing |

Everything else (analysis, commentary, rationale, speculation) is **forbidden** in UI output.
Internal reasoning goes to `artifacts/_internal/`.

## Entry contract (all 5 required)

| Field | Description |
|-------|-------------|
| `TARGET` | deliverable to complete |
| `REPO_CONTEXT` | repo / branch / path / related files |
| `SUCCESS_CRITERIA` | verifiable acceptance conditions |
| `CONSTRAINTS` | security red lines, network, tools, forbidden paths |
| `PRIORITY` | P0 / P1 / P2 |

Missing any field → produce `artifacts/NEED_INPUT.md` and stop.

## Stage DAG

```
Stage 0 (P0): Define problem → problem.statement / success.criteria / constraints
    │
Stage 1 (P0): Repo search → baseline.facts / hypotheses / gaps / security.redlines
    │
Stage 2/3 (P1, optional): External search → sources.index / verification.matrix
    │
Core (P0): Cross-verify → decision.record / plan
    │
Deliver: PATCH / COMMANDS / FILES / TASKS (+ verify + rollback)
```

Each stage has: input → output → gate → failure action.
No stage may end silently; blocked stages must produce `NEED_INPUT` or `gaps.yaml`.

## Artifacts layout

```
artifacts/
├── _internal/          # evidence, matrices, decisions (not shown in UI)
│   ├── problem.statement.json
│   ├── success.criteria.json
│   ├── constraints.json
│   ├── baseline.facts.yaml
│   ├── hypotheses.yaml
│   ├── gaps.yaml
│   ├── security.redlines.yaml
│   ├── sources.index.yaml
│   ├── verification.matrix.yaml
│   ├── decision.record.yaml
│   └── plan.yaml
├── reports/            # external-facing reports
├── runbooks/           # replay/rollback scripts
│   ├── verify.sh
│   └── rollback.sh
├── manifests/          # artifact index
│   └── run.manifest.yaml
├── patches/            # generated patches
└── tasks/              # generated task files
```

## Triggers

1. **ChatOps**: issue/PR comment containing `/autoops run`
2. **CI failure**: `workflow_run` on ci failure
3. **Manual**: `workflow_dispatch` with form fields

## Guards (hard fail)

- Missing manifest → fail
- Output outside allowed dirs/types → fail
- Missing entry fields without NEED_INPUT → fail
- Every deliverable must include verify + rollback
