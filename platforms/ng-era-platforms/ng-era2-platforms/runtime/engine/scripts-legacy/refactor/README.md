# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Refactoring Automation Scripts

This directory contains automation scripts for the three-phase system refactoring process.

## 📜 Available Scripts

### Master Orchestration

- **`leader-refactor.sh`** - Main orchestration script that runs all three phases
  ```bash
  bash scripts/refactor/leader-refactor.sh [--skip-phase PHASE] [--dry-run]
  ```

### Rollback Scripts

- **`rollback.sh`** - Automated rollback at various levels
  ```bash
  # Rollback single file
  bash scripts/refactor/rollback.sh file <filepath>
  
  # Rollback module
  bash scripts/refactor/rollback.sh module <module-name>
  
  # Rollback phase
  bash scripts/refactor/rollback.sh phase <1|2|3>
  
  # Full rollback
  bash scripts/refactor/rollback.sh full [commit-id]
  ```

## 🚀 Quick Start

### Run Complete Refactoring Pipeline

```bash
# Dry run (no changes)
bash scripts/refactor/leader-refactor.sh --dry-run

# Execute all phases
bash scripts/refactor/leader-refactor.sh

# Skip specific phase
bash scripts/refactor/leader-refactor.sh --skip-phase 1
```

### Emergency Rollback

```bash
# Rollback last phase
bash scripts/refactor/rollback.sh phase 3

# Full system rollback
bash scripts/refactor/rollback.sh full
```

## 📋 Phase-Specific Scripts

### Phase 1: Deconstruction
- `phase1-deconstruction.sh` - Analysis and documentation
- Location: `scripts/refactor/phase1-deconstruction.sh`

### Phase 2: Integration
- `phase2-integration.sh` - Design and integration planning
- Location: `scripts/refactor/phase2-integration.sh`

### Phase 3: Refactor
- `phase3-refactor.sh` - Code refactoring execution
- Location: `scripts/refactor/phase3-refactor.sh`

## 🔧 Validation Tools

Validation tools are located in `tools/refactor/`:
- `validate-phase1.py` - Phase 1 deliverables validation
- `validate-phase2.py` - Phase 2 deliverables validation
- `validate-phase3.py` - Phase 3 deliverables validation

## 📊 Logging

All scripts generate logs in the repository root:
- Format: `refactor-YYYYMMDD-HHMMSS.log`
- Contains detailed execution traces
- Includes timestamps and status indicators

## ⚠️ Important Notes

1. **Always backup before refactoring**: Scripts create automatic backups
2. **Test in dry-run mode first**: Use `--dry-run` flag
3. **Validate prerequisites**: Scripts check for required tools
4. **Monitor checkpoints**: Each phase creates a checkpoint for rollback
5. **Review logs**: Check log files for detailed execution information

## 🔗 Related Documentation

- Main Plan: `workspace/docs/THREE_PHASE_REFACTORING_EXECUTION_PLAN.md`
- Playbooks: `workspace/docs/refactor_playbooks/README.md`
- INSTANT Plan: `INSTANT-EXECUTION-REFACTOR-PLAN.md`

## 🤝 Support

For issues or questions:
- GitHub Issues: Label `refactor-execution`
- Documentation: See main execution plan
