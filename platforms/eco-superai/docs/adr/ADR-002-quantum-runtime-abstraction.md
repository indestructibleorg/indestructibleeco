# ADR-002: Quantum Runtime Backend Abstraction

**Status:** Accepted  
**Date:** 2025-02-11  
**Deciders:** Platform Architecture Team

## Context

The quantum computing landscape is rapidly evolving with multiple competing frameworks (Qiskit, Cirq, Pennylane). Locking into a single framework creates vendor risk and limits algorithm portability.

## Decision

Implement a **QuantumExecutor** abstraction layer that provides a unified interface for circuit compilation, execution, and result retrieval across multiple backends:

- `aer_simulator` — Qiskit Aer local simulation (default)
- `ibm_quantum` — IBM Quantum cloud execution
- `cirq_simulator` — Google Cirq simulation

Backend selection is configuration-driven via `QUANTUM_BACKEND` environment variable.

## Consequences

### Positive
- Algorithms are written once, run on any supported backend
- Easy to add new backends (Pennylane, Amazon Braket) without algorithm changes
- Local development uses fast simulators; production can target real quantum hardware

### Negative
- Abstraction may not expose backend-specific optimizations
- Lowest-common-denominator API limits advanced features
- Additional testing burden (each backend must be validated)

### Mitigations
- Allow backend-specific extension points for advanced use cases
- Maintain a compatibility matrix documenting feature support per backend
- Use CI matrix testing for all supported backends