# skill-creator

Internal tool for authoring and validating indestructibleeco YAML governance skills.

## Usage

```bash
# Create a new skill scaffold
python3 scripts/init_skill.py --name my-skill --category my-category

# Validate a skill manifest
python3 scripts/quick_validate.py tools/skill-creator/skills/my-skill

# Validate all skills (JS validator)
node scripts/validate.js tools/skill-creator/skills

# Create a .qyaml governance skill
node scripts/create-skill.js --name my-skill --target k8s
```

## Skill Structure

```
skills/<skill-name>/
├── skill.json          # Manifest: DAG, governance, metadata
├── actions/            # Shell scripts for each DAG action
├── schemas/            # JSON Schema for input/output
├── references/         # Supporting documentation
└── tests/              # pytest test suite
```

## Reference documents

See `references/` for canonical examples and schema documentation:

- `workflows.md` — Sequential, conditional, parallel, and self-healing workflow patterns
- `output-patterns.md` — Structured report, error taxonomy, governance stamp patterns
- `progressive-disclosure-patterns.md` — Content splitting strategies for skills
