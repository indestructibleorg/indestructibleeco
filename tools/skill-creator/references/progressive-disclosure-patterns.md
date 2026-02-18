# Progressive Disclosure Patterns

Keep skill manifests focused. Split complex skills into modular components.

## Pattern 1: Core Manifest with Action Scripts

Keep `skill.json` lean — move implementation to `actions/` scripts:

```
skills/ci-repair/
├── skill.json              # DAG definition, inputs, outputs, governance
├── actions/
│   ├── understand.sh       # Step 1: gather context
│   ├── retrieve.sh         # Step 2: fetch logs and configs
│   ├── analyze.py          # Step 3: root cause analysis
│   ├── repair.sh           # Step 4: apply fix
│   └── verify.sh           # Step 5: confirm fix
├── schemas/
│   ├── input.schema.json   # Input validation
│   └── output.schema.json  # Output validation
└── tests/
    └── test_ci_repair.py   # End-to-end tests
```

The manifest defines the DAG; scripts contain the logic.

## Pattern 2: Domain-Specific Schemas

For skills that handle multiple resource types, split schemas:

```
skills/governance-validator/
├── skill.json
├── schemas/
│   ├── qyaml.schema.json       # .qyaml governance validation
│   ├── dockerfile.schema.json   # Dockerfile structure validation
│   ├── workflow.schema.json     # GitHub Actions workflow validation
│   └── identity.schema.json     # Identity consistency validation
└── actions/
    ├── validate_qyaml.sh
    ├── validate_dockerfile.sh
    └── validate_workflow.sh
```

Each schema validates one artifact type. The skill orchestrates all validators.

## Pattern 3: Shared Action Libraries

When multiple skills share common operations, extract to a shared location:

```
tools/skill-creator/
├── lib/
│   ├── governance.sh        # Governance stamp generation
│   ├── identity.sh          # URI/URN builders
│   └── git_ops.sh           # Git commit, push, branch operations
├── skills/
│   ├── ci-repair/
│   │   └── actions/
│   │       └── repair.sh    # Sources ../../lib/git_ops.sh
│   └── governance-audit/
│       └── actions/
│           └── audit.sh     # Sources ../../lib/governance.sh
```

## Guidelines

- **skill.json** should be under 200 lines — it defines structure, not implementation
- **Action scripts** contain the actual logic — they can be any language
- **Schemas** validate inputs and outputs — use JSON Schema draft-07
- **Tests** verify end-to-end behavior — run against real or mock data
- Avoid deeply nested dependencies between skills
- Each skill must be independently executable