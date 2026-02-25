<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Quick Start: Instant Execution Pipeline

## 🚀 快速開始:即時執行管線

**One-command execution of AI-powered deployment pipeline**

---

## ⚡ Fastest Way to Run

```bash
cd /path/to/MachineNativeOps
./scripts/run-instant-execution.sh --dry-run
```

**That's it!** 🎉

---

## 📋 Common Commands

### Complete Pipeline

```bash
# Dry run (safe, recommended for testing)
./scripts/run-instant-execution.sh --dry-run

# Production deployment
./scripts/run-instant-execution.sh --namespace production

# Save results to file
./scripts/run-instant-execution.sh --output results.json
```

### Individual Stages

```bash
# Run Stage 1 only (AI Analysis < 5s)
./scripts/run-instant-execution.sh --stage 1

# Run Stage 2 only (Validation < 30s)
./scripts/run-instant-execution.sh --stage 2

# Run Stage 3 only (Deployment < 30min)
./scripts/run-instant-execution.sh --stage 3
```

### Testing Components

```bash
# Test AI Governance Engine
python3 tools/ai/governance_engine.py

# Test Validation Engine
python3 tools/automation/engines/baseline_validation_engine.py

# Test Framework
python3 tests/automation/test_framework_patterns.py
```

---

## 🏗️ What It Does

```
Stage 1: AI Analysis (< 5s)
├─ Scan codebase (2,575 files)
├─ Detect patterns (ML-based)
├─ Check for conflicts
└─ Make AI decision

Stage 2: Validation (< 30s)
├─ Run automated tests
├─ Validate configurations
└─ Check Kubernetes resources

Stage 3: Deployment (< 30min)
├─ Deploy to Kubernetes
├─ Monitor health
└─ Auto-rollback on failure
```

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `scripts/run-instant-execution.sh` | Main entry point |
| `automation/pipelines/instant_execution_pipeline.py` | Pipeline orchestrator |
| `tools/ai/governance_engine.py` | AI decision engine |
| `config/instant-execution-pipeline.yaml` | Configuration |
| `docs/INSTANT_EXECUTION_INTEGRATION_MAP.md` | Full documentation |

---

## 🔧 Troubleshooting

### Problem: Permission Denied

```bash
chmod +x scripts/run-instant-execution.sh
```

### Problem: Import Errors

```bash
export PYTHONPATH="$PWD:$PWD/tools:$PWD/tools/automation/engines:$PWD/tests/automation"
```

### Problem: kubectl Not Found

```bash
# Use dry-run mode (doesn't need kubectl)
./scripts/run-instant-execution.sh --dry-run
```

---

## 📖 More Information

- **Full Documentation:** [docs/INSTANT_EXECUTION_INTEGRATION_MAP.md](./INSTANT_EXECUTION_INTEGRATION_MAP.md)
- **Summary:** [INSTANT_EXECUTION_SUMMARY.md](INSTANT_EXECUTION_SUMMARY.md)
- **Pipeline README:** [automation/pipelines/README.md](../src/automation/pipelines/README.md)

---

## ✅ Success Output Example

```
🚀 MachineNativeOps Instant Execution Pipeline
⚡ AI-Powered 3-Stage Automated Deployment

[12:34:56] ✅ Prerequisites check passed
[12:34:56] ✅ Environment ready

STAGE 1: AI-Driven Analysis & Synthesis
========================================
[12:34:56] ✓ Analyzed 2575 files (614604 lines)
[12:34:56] ✓ Pattern confidence: 91.0%
[12:34:56] ✓ No conflicts detected
[12:34:57] ✅ Decision: APPROVE
[12:34:57] ✅ Duration: 0.3s

✅ PIPELINE EXECUTION SUCCESSFUL
```

---

## 🎯 Next Steps

1. ✅ Run dry-run to test
2. ✅ Review results
3. ✅ Run production deployment
4. ✅ Monitor execution

---

**Ready to go!** 🚀
