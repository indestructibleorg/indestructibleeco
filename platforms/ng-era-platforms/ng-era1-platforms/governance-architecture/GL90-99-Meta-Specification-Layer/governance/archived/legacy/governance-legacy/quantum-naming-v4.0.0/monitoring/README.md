# @ECO-layer: GQS-L0
<!-- @ECO-governed -->
<!-- @ECO-layer: GL90-99 -->
<!-- @ECO-semantic: governed-documentation -->
<!-- @ECO-audit-trail: engine/governance/GL_SEMANTIC_ANCHOR.json -->

# Quantum Naming Governance Monitoring

This directory contains observability configurations for the MachineNativeOps Quantum-Enhanced Naming Governance system.

## Files

### prometheus-quantum-rules.yaml

Prometheus alerting and recording rules for quantum metrics monitoring:

**Alert Rules (25+ rules):**
- `QuantumNamingDecoherence` - Coherence below 0.999 threshold
- `QuantumCoherenceDegradation` - Declining coherence trend
- `QuantumEntanglementWeak` - Entanglement strength below 0.95
- `QuantumEntanglementLoss` - Critical entanglement loss
- `QuantumConflictEntropyHigh` - High conflict entropy
- `QuantumDecoherenceRateHigh` - Elevated decoherence rate
- `QuantumNamingViolation` - Policy violations detected
- `QuantumStateImbalance` - State distribution issues
- `QuantumBellInequalityViolation` - Quantum correlation failures
- `QuantumGovernanceServiceDown` - Service availability alerts

**Recording Rules:**
- `quantum:naming_coherence:rate5m`
- `quantum:entanglement_strength:avg5m`
- `quantum:conflict_entropy:max1h`
- `quantum:circuit_duration:p95`
- `quantum:circuit_duration:p99`
- `quantum:qubit_utilization:ratio`
- `quantum:requests_success_rate:5m`

### grafana-quantum-dashboard.json

10-panel Grafana dashboard for quantum metrics visualization:

| Panel | Type | Description |
|-------|------|-------------|
| Quantum Coherence Waveform | Time Series | Real-time coherence monitoring |
| Quantum Entanglement Strength | Time Series | Entanglement tracking |
| Quantum Conflict Entropy Heatmap | Heatmap | Conflict visualization |
| Quantum Decoherence Rate | Time Series | Decoherence trend analysis |
| Quantum State Distribution | Pie Chart | State distribution overview |
| Bell Inequality Test | Table | Correlation verification |
| Quantum Naming Violations | Pie Chart | Violations by severity |
| Quantum Resource Utilization | Bar Gauge | Qubit utilization |
| Quantum Circuit Performance | Time Series | Execution metrics |
| Quantum Service Status | Stat | Service health indicator |
| Quantum Success Rate | Stat | Request success rate |

## Setup

### Import Prometheus Rules

```bash
kubectl apply -f prometheus-quantum-rules.yaml
```

### Import Grafana Dashboard

1. Access Grafana at `[EXTERNAL_URL_REMOVED]
2. Navigate to **Dashboards** → **Import**
3. Upload `grafana-quantum-dashboard.json`
4. Select Prometheus data source
5. Click **Import**

## Key Metrics

| Metric | Threshold | Severity |
|--------|-----------|----------|
| naming_coherence_quantum | < 0.999 | Critical |
| entanglement_strength | < 0.95 | Warning |
| conflict_entropy_quantum | > 0.1 | Warning |
| decoherence_rate | > 0.001 | Warning |
| bell_inequality_value | < 2.0 | Warning |

## Related Documentation

- [Parent README](../README.md) - Main project documentation
- [Deployment](../deployment/README.md) - Kubernetes deployment
- [Configuration](../config/README.md) - Governance configuration
