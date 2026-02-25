# @ECO-layer: GQS-L0
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: documentation
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
# Quantum Naming Governance Scripts

This directory contains automation scripts for the MachineNativeOps Quantum-Enhanced Naming Governance system.

## Files

### QUICK_INSTALL.sh

One-click deployment script for quantum governance infrastructure.

## Usage

```bash
# Navigate to scripts directory
cd governance/quantum-naming-v4.0.0/scripts/

# Make script executable
chmod +x QUICK_INSTALL.sh

# Run installation
./QUICK_INSTALL.sh
```

## Script Features

### Prerequisites Check
- Verifies kubectl installation and cluster access
- Validates Helm version (3.8+)
- Checks available cluster resources

### Deployment Steps
1. **Namespace Setup**: Creates `quantum-governance` namespace with proper labels
2. **Secrets Installation**: Generates and stores quantum API tokens and keys
3. **Configuration Deployment**: Applies quantum config and naming policies
4. **Service Deployment**: Deploys 3-replica governance service
5. **Monitoring Setup**: Configures Prometheus ServiceMonitor and rules
6. **Validation**: Runs health checks and endpoint tests

### Configuration Variables

| Variable | Default | Description |
|----------|---------|-------------|
| QUANTUM_VERSION | v4.0.0-quantum | Deployment version |
| QUANTUM_NAMESPACE | quantum-governance | Kubernetes namespace |
| QUANTUM_BACKEND | ibm_quantum_falcon | Quantum computing backend |
| COHERENCE_THRESHOLD | 0.9999 | Minimum coherence level |
| ENTANGLEMENT_DEPTH | 7 | Entanglement depth setting |

## Output

After successful installation, the script displays:
- Deployment summary with version and configuration
- Service URLs for API, metrics, and health endpoints
- Monitoring commands for pods and logs
- Testing commands for validation

## Troubleshooting

### Common Issues

**Cluster Access Error**
```bash
# Verify kubeconfig
kubectl cluster-info
kubectl get nodes
```

**Resource Constraints**
```bash
# Check available resources
kubectl top nodes
```

**Namespace Conflict**
```bash
# Delete existing namespace (caution: destroys data)
kubectl delete namespace quantum-governance
./QUICK_INSTALL.sh
```

## Related Documentation

- [Parent README](../README.md) - Main project documentation
- [Deployment Manifest](../deployment/README.md) - Manual deployment guide
- [Configuration](../config/README.md) - Configuration options
