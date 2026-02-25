#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: __init__
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification Package
This package provides enterprise-grade supply chain verification capabilities
for MachineNativeOps, including seven-stage verification workflow.
"""
from .hash_manager import HashManager
from .stage1_lint_format import Stage1LintFormatVerifier
from .stage2_schema_semantic import Stage2SchemaSemanticVerifier
from .stage3_dependency import Stage3DependencyVerifier
from .stage4_sbom_scan import Stage4SbomScanVerifier
from .stage5_sign_attestation import Stage5SignAttestationVerifier
from .stage6_admission_policy import Stage6AdmissionPolicyVerifier
from .stage7_runtime_monitoring import Stage7RuntimeMonitoringVerifier
from .supply_chain_types import (
    ChainVerificationResult,
    VerificationEvidence,
    VerificationStage,
)
from .supply_chain_verifier import UltimateSupplyChainVerifier
__all__ = [
    # Main verifier
    "UltimateSupplyChainVerifier",
    # Hash management
    "HashManager",
    # Stage verifiers
    "Stage1LintFormatVerifier",
    "Stage2SchemaSemanticVerifier",
    "Stage3DependencyVerifier",
    "Stage4SbomScanVerifier",
    "Stage5SignAttestationVerifier",
    "Stage6AdmissionPolicyVerifier",
    "Stage7RuntimeMonitoringVerifier",
    # Types
    "VerificationStage",
    "VerificationEvidence",
    "ChainVerificationResult",
]
__version__ = "1.0.0"
