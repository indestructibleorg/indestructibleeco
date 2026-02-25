#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: supply_chain_types
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Types and Data Structures
This module contains all type definitions and data structures used
across the supply chain verification system.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List
class VerificationStage(Enum):
    """Verification stage enumeration"""
    LINT_FORMAT = 1
    SCHEMA_SEMANTIC = 2
    DEPENDENCY_REPRODUCIBLE = 3
    SBOM_VULNERABILITY_SCAN = 4
    SIGN_ATTESTATION = 5
    ADMISSION_POLICY = 6
    RUNTIME_MONITORING = 7
@dataclass
class VerificationEvidence:
    """Verification evidence data structure"""
    stage: int
    stage_name: str
    evidence_type: str
    data: Dict[str, Any]
    hash_value: str
    timestamp: str
    artifacts: List[str]
    compliant: bool
    rollback_available: bool
    reproducible: bool
@dataclass
class ChainVerificationResult:
    """Complete chain verification result"""
    total_stages: int
    passed_stages: int
    failed_stages: int
    warning_stages: int
    overall_status: str
    final_hash: str
    evidence_chain: List[VerificationEvidence]
    audit_trail: List[Dict[str, Any]]
    compliance_score: float
    recommendations: List[str]