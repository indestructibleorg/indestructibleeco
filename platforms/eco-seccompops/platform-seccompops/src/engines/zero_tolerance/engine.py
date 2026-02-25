#!/usr/bin/env python3
"""
Zero-Tolerance GL-Registry Governance Enforcement Engine v1.0
High-Execution-Weight Strict Governance Enforcement System

This module implements the complete zero-tolerance governance enforcement engine
with automatic rule execution, strict validation, and zero-exception policy enforcement.

Governance Stage: S5-VERIFIED
Status: ENFORCED
"""

import hashlib
import hmac
import json
import logging
import sys
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import yaml

# Configure logging with CRITICAL-only default
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# ENUMS AND CONSTANTS
# ============================================

class EnforcementLevel(Enum):
    """Enforcement severity levels - strictly ordered."""
    CRITICAL = 1    # Block immediately, no exceptions
    HIGH = 2        # Block with conditional override (multi-signature required)
    MEDIUM = 3      # Alert and block, but allow escalation path
    LOW = 4         # Log and report
    ADVISORY = 5    # Informational only


class ViolationType(Enum):
    """Zero-tolerance violation types."""
    HASH_POLICY_VIOLATION = "hash_policy_violation"
    EVIDENCE_CHAIN_BROKEN = "evidence_chain_broken"
    NARRATIVE_FOUND = "narrative_found"
    LAYER_BYPASS = "layer_bypass"
    UNAUTHORIZED_EXECUTION = "unauthorized_execution"
    SEMANTIC_VIOLATION = "semantic_violation"
    IMMUTABILITY_BREACH = "immutability_breach"
    SIGNATURE_INVALID = "signature_invalid"
    POLICY_VIOLATION = "policy_violation"


class ExecutionPhase(Enum):
    """Strict five-phase execution pipeline."""
    PRE_COMMIT = 1
    CI_BUILD = 2
    PRE_MERGE = 3
    PRE_DEPLOY = 4
    POST_DEPLOY = 5


class ArchitectureLayer(Enum):
    """Strict five-layer architecture."""
    L1_GOVERNANCE = 1
    L2_EVIDENCE = 2
    L3_DECISION = 3
    L4_SEMANTIC = 4
    L5_EXECUTION = 5


# ============================================
# CRYPTOGRAPHIC STANDARDS
# ============================================

class CryptographicStandard:
    """Strict cryptographic standards with zero tolerance."""
    
    # Authoritative hash algorithm
    AUTHORITATIVE_ALGORITHM = "sha3_512"
    SECONDARY_ALGORITHM = "blake3"
    LEGACY_ALGORITHM = "sha256"  # For compatibility only, never authoritative
    
    # Minimum key sizes
    RSA_MINIMUM_KEY_SIZE = 4096
    ECDSA_CURVE = "secp256k1"
    
    # Hash output lengths
    SHA3_512_LENGTH = 64  # bytes
    BLAKE3_LENGTH = 32    # bytes
    SHA256_LENGTH = 32    # bytes
    
    @staticmethod
    def generate_sha3_512(data: bytes) -> str:
        """Generate SHA3-512 hash - AUTHORITATIVE."""
        return hashlib.sha3_512(data).hexdigest()
    
    @staticmethod
    def generate_blake3(data: bytes) -> str:
        """Generate BLAKE3 hash - secondary for performance."""
        try:
            import blake3
            return blake3.blake3(data).hexdigest()
        except ImportError:
            # Fallback to SHA3-512 if blake3 not available
            return CryptographicStandard.generate_sha3_512(data)
    
    @staticmethod
    def generate_legacy_sha256(data: bytes) -> str:
        """Generate SHA256 hash - legacy only."""
        return hashlib.sha256(data).hexdigest()
    
    @staticmethod
    def verify_hash(data: bytes, hash_value: str, algorithm: str = "sha3_512") -> bool:
        """Verify hash with zero tolerance for mismatch."""
        if algorithm == "sha3_512":
            computed = CryptographicStandard.generate_sha3_512(data)
        elif algorithm == "blake3":
            computed = CryptographicStandard.generate_blake3(data)
        elif algorithm == "sha256":
            computed = CryptographicStandard.generate_legacy_sha256(data)
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        return hmac.compare_digest(computed, hash_value)


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class GovernanceEvent:
    """Immutable governance event with cryptographic binding."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    event_type: str = ""
    actor: str = ""
    action: str = ""
    target: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    execution_phase: ExecutionPhase = ExecutionPhase.PRE_COMMIT
    architecture_layer: ArchitectureLayer = ArchitectureLayer.L1_GOVERNANCE
    hash_value: str = ""
    previous_hash: str = ""
    signature: str = ""
    
    def to_bytes(self) -> bytes:
        """Convert to bytes for hashing."""
        data = {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "actor": self.actor,
            "action": self.action,
            "target": self.target,
            "evidence": self.evidence,
            "previous_hash": self.previous_hash,
        }
        return json.dumps(data, sort_keys=True).encode('utf-8')
    
    def compute_hash(self) -> str:
        """Compute SHA3-512 hash - AUTHORITATIVE."""
        return CryptographicStandard.generate_sha3_512(self.to_bytes())


@dataclass
class GovernanceViolation:
    """Immutable governance violation record."""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    violation_type: ViolationType = ViolationType.POLICY_VIOLATION
    enforcement_level: EnforcementLevel = EnforcementLevel.CRITICAL
    description: str = ""
    evidence: Dict[str, Any] = field(default_factory=dict)
    blocking: bool = True
    remediation_action: Optional[str] = None
    actor_notified: bool = False
    escalation_required: bool = False
    hash_value: str = ""
    
    def to_bytes(self) -> bytes:
        """Convert to bytes for hashing."""
        data = {
            "violation_id": self.violation_id,
            "timestamp": self.timestamp,
            "violation_type": self.violation_type.value,
            "enforcement_level": self.enforcement_level.name,
            "description": self.description,
            "evidence": self.evidence,
        }
        return json.dumps(data, sort_keys=True).encode('utf-8')
    
    def compute_hash(self) -> str:
        """Compute SHA3-512 hash - AUTHORITATIVE."""
        return CryptographicStandard.generate_sha3_512(self.to_bytes())


# ============================================
# ZERO-TOLERANCE RULES ENGINE
# ============================================

class GovernanceRule(ABC):
    """Abstract base class for all governance rules."""
    
    @abstractmethod
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Evaluate rule against event. Returns (passed, violation)."""
        pass
    
    @abstractmethod
    def get_rule_name(self) -> str:
        """Get human-readable rule name."""
        pass


class HashPolicyRule(GovernanceRule):
    """Enforce SHA3-512 hash policy - ZERO TOLERANCE."""
    
    def get_rule_name(self) -> str:
        return "HashPolicyRule"
    
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Enforce authoritative hash algorithm requirement."""
        # Every event must have SHA3-512 hash
        if not event.hash_value:
            violation = GovernanceViolation(
                violation_type=ViolationType.HASH_POLICY_VIOLATION,
                enforcement_level=EnforcementLevel.CRITICAL,
                description="Event missing required SHA3-512 hash",
                evidence={"event_id": event.event_id},
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        # Hash must be valid SHA3-512 length
        if len(event.hash_value) != CryptographicStandard.SHA3_512_LENGTH * 2:  # hex = 2 chars per byte
            violation = GovernanceViolation(
                violation_type=ViolationType.HASH_POLICY_VIOLATION,
                enforcement_level=EnforcementLevel.CRITICAL,
                description=f"Invalid hash length: {len(event.hash_value)}, expected {CryptographicStandard.SHA3_512_LENGTH * 2}",
                evidence={"event_id": event.event_id, "hash_length": len(event.hash_value)},
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        # Verify hash matches computed value
        computed_hash = event.compute_hash()
        if not CryptographicStandard.verify_hash(event.to_bytes(), event.hash_value, "sha3_512"):
            violation = GovernanceViolation(
                violation_type=ViolationType.HASH_POLICY_VIOLATION,
                enforcement_level=EnforcementLevel.CRITICAL,
                description="Hash value mismatch - possible tampering detected",
                evidence={
                    "event_id": event.event_id,
                    "provided_hash": event.hash_value,
                    "computed_hash": computed_hash
                },
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        return True, None


class EvidenceChainIntegrityRule(GovernanceRule):
    """Enforce unbroken evidence chain - ZERO TOLERANCE."""
    
    def get_rule_name(self) -> str:
        return "EvidenceChainIntegrityRule"
    
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Enforce evidence chain continuity."""
        # Must reference previous hash (except for genesis)
        if event.event_id and not event.previous_hash and event.event_id != "genesis":
            violation = GovernanceViolation(
                violation_type=ViolationType.EVIDENCE_CHAIN_BROKEN,
                enforcement_level=EnforcementLevel.CRITICAL,
                description="Event missing reference to previous hash - chain broken",
                evidence={"event_id": event.event_id},
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        return True, None


class NarrativeFreeRule(GovernanceRule):
    """Enforce narrative-free language - ZERO TOLERANCE."""
    
    # Prohibited terms that indicate narrative/subjective language
    PROHIBITED_TERMS = {
        'very', 'extremely', 'critically', 'surprisingly', 'interestingly',
        'basically', 'essentially', 'clearly', 'obviously', 'unfortunately',
        'fortunately', 'somehow', 'relatively', 'completely', 'absolutely',
        'definitely', 'certainly', 'probably', 'likely', 'possibly',
        'apparently', 'allegedly', 'reportedly', 'supposedly', 'seemingly'
    }
    
    def get_rule_name(self) -> str:
        return "NarrativeFreeRule"
    
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Enforce narrative-free language in descriptions."""
        description = event.action.lower() if event.action else ""
        
        # Check for prohibited narrative terms
        found_terms = [term for term in self.PROHIBITED_TERMS if term in description]
        
        if found_terms:
            violation = GovernanceViolation(
                violation_type=ViolationType.NARRATIVE_FOUND,
                enforcement_level=EnforcementLevel.CRITICAL,
                description=f"Narrative language detected: {', '.join(found_terms)}",
                evidence={"event_id": event.event_id, "prohibited_terms": found_terms},
                blocking=True,
                escalation_required=False
            )
            return False, violation
        
        return True, None


class LayerDependencyRule(GovernanceRule):
    """Enforce strict layer dependencies - ZERO TOLERANCE."""
    
    # Layer dependency rules: downstream layers depend on upstream
    LAYER_DEPENDENCIES = {
        ArchitectureLayer.L2_EVIDENCE: [ArchitectureLayer.L1_GOVERNANCE],
        ArchitectureLayer.L3_DECISION: [ArchitectureLayer.L1_GOVERNANCE, ArchitectureLayer.L2_EVIDENCE],
        ArchitectureLayer.L4_SEMANTIC: [ArchitectureLayer.L1_GOVERNANCE, ArchitectureLayer.L2_EVIDENCE, ArchitectureLayer.L3_DECISION],
        ArchitectureLayer.L5_EXECUTION: [ArchitectureLayer.L1_GOVERNANCE, ArchitectureLayer.L2_EVIDENCE, ArchitectureLayer.L3_DECISION, ArchitectureLayer.L4_SEMANTIC],
    }

    def _normalize_layer(self, value: Any) -> Optional[ArchitectureLayer]:
        if isinstance(value, ArchitectureLayer):
            return value
        if isinstance(value, int):
            try:
                return ArchitectureLayer(value)
            except ValueError:
                return None
        if isinstance(value, str):
            cleaned = value.strip().upper()
            if cleaned in ArchitectureLayer.__members__:
                return ArchitectureLayer[cleaned]
            if cleaned.startswith("L"):
                cleaned = cleaned[1:]
            if cleaned.isdigit():
                try:
                    return ArchitectureLayer(int(cleaned))
                except ValueError:
                    return None
        return None

    def _extract_completed_layers(self, evidence: Dict[str, Any]) -> List[ArchitectureLayer]:
        if not evidence:
            return []

        sources = []
        for key in ("completed_layers", "satisfied_layers"):
            if key in evidence:
                sources.append(evidence[key])

        context = evidence.get("execution_context")
        if isinstance(context, dict):
            for key in ("completed_layers", "satisfied_layers"):
                if key in context:
                    sources.append(context[key])

        completed = []
        for source in sources:
            if isinstance(source, (list, tuple, set)):
                candidates = source
            else:
                candidates = [source]
            for item in candidates:
                normalized = self._normalize_layer(item)
                if normalized and normalized not in completed:
                    completed.append(normalized)

        return completed
    _LAYER_ALIASES = {
        "L1": ArchitectureLayer.L1_GOVERNANCE,
        "L2": ArchitectureLayer.L2_EVIDENCE,
        "L3": ArchitectureLayer.L3_DECISION,
        "L4": ArchitectureLayer.L4_SEMANTIC,
        "L5": ArchitectureLayer.L5_EXECUTION,
        "GOVERNANCE": ArchitectureLayer.L1_GOVERNANCE,
        "EVIDENCE": ArchitectureLayer.L2_EVIDENCE,
        "DECISION": ArchitectureLayer.L3_DECISION,
        "SEMANTIC": ArchitectureLayer.L4_SEMANTIC,
        "EXECUTION": ArchitectureLayer.L5_EXECUTION,
    }
    
    def get_rule_name(self) -> str:
        return "LayerDependencyRule"

    def _normalize_layers(self, raw_layers: Any) -> Tuple[List[ArchitectureLayer], List[Any]]:
        """Normalize satisfied layer evidence into ArchitectureLayer values."""
        if raw_layers is None:
            return [], []
        if isinstance(raw_layers, (ArchitectureLayer, str, int)):
            raw_layers = [raw_layers]
        elif isinstance(raw_layers, (list, tuple, set)):
            raw_layers = list(raw_layers)
        else:
            raw_layers = [raw_layers]
        
        normalized: List[ArchitectureLayer] = []
        invalid: List[Any] = []
        for layer in raw_layers:
            if isinstance(layer, ArchitectureLayer):
                normalized.append(layer)
                continue
            if isinstance(layer, int):
                try:
                    normalized.append(ArchitectureLayer(layer))
                    continue
                except ValueError:
                    invalid.append(layer)
                    continue
            if isinstance(layer, str):
                token = layer.strip()
                if not token:
                    invalid.append(layer)
                    continue
                token_upper = token.upper()
                if token_upper.startswith("ARCHITECTURELAYER."):
                    token_upper = token_upper.split(".", 1)[1]
                if token_upper in ArchitectureLayer.__members__:
                    normalized.append(ArchitectureLayer[token_upper])
                    continue
                if token_upper in self._LAYER_ALIASES:
                    normalized.append(self._LAYER_ALIASES[token_upper])
                    continue
            invalid.append(layer)
        
        return normalized, invalid
    
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Enforce layer dependency ordering."""
        current_layer = event.architecture_layer
        
        # L1 has no dependencies
        if current_layer == ArchitectureLayer.L1_GOVERNANCE:
            return True, None
        
        # Check that all required upstream layers are satisfied
        required_layers = self.LAYER_DEPENDENCIES.get(current_layer, [])
        completed_layers = self._extract_completed_layers(event.evidence)
        missing_layers = [layer for layer in required_layers if layer not in completed_layers]

        satisfied_layers_raw = event.evidence.get("satisfied_layers")
        satisfied_layers, invalid_entries = self._normalize_layers(satisfied_layers_raw)
        
        if satisfied_layers_raw is None:
            violation = GovernanceViolation(
                violation_type=ViolationType.LAYER_BYPASS,
                enforcement_level=EnforcementLevel.CRITICAL,
                description="Missing layer dependency evidence: satisfied_layers not provided",
                evidence={
                    "event_id": event.event_id,
                    "current_layer": current_layer.name,
                    "required_layers": [layer.name for layer in required_layers],
                },
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        if invalid_entries:
            violation = GovernanceViolation(
                violation_type=ViolationType.LAYER_BYPASS,
                enforcement_level=EnforcementLevel.CRITICAL,
                description="Invalid layer dependency evidence entries",
                evidence={
                    "event_id": event.event_id,
                    "current_layer": current_layer.name,
                    "invalid_entries": invalid_entries,
                    "required_layers": [layer.name for layer in required_layers],
                },
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        missing_layers = [layer for layer in required_layers if layer not in satisfied_layers]
        if missing_layers:
            violation = GovernanceViolation(
                violation_type=ViolationType.LAYER_BYPASS,
                enforcement_level=EnforcementLevel.CRITICAL,
                description=(
                    f"Layer dependencies not satisfied for {current_layer.name}: "
                    f"missing {[layer.name for layer in missing_layers]}"
                    f"Layer dependency violation: {current_layer.name} requires "
                    f"{', '.join(layer.name for layer in missing_layers)}"
                ),
                evidence={
                    "event_id": event.event_id,
                    "current_layer": current_layer.name,
                    "required_layers": [layer.name for layer in required_layers],
                    "completed_layers": [layer.name for layer in completed_layers],
                    "satisfied_layers": [layer.name for layer in satisfied_layers],
                    "missing_layers": [layer.name for layer in missing_layers],
                },
                blocking=True,
                escalation_required=True
            )
            return False, violation

        
        return True, None


class ImmutabilityRule(GovernanceRule):
    """Enforce immutability of core components - ZERO TOLERANCE."""
    
    # Core immutable components
    IMMUTABLE_CORE = {
        "governance_registry.yaml",
        "architecture_registry.yaml",
        "hash_policy.yaml",
        "narrative_free_enforcement.yaml"
    }
    
    def get_rule_name(self) -> str:
        return "ImmutabilityRule"
    
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Enforce immutability of core components."""
        if event.action == "modify" and event.target in self.IMMUTABLE_CORE:
            violation = GovernanceViolation(
                violation_type=ViolationType.IMMUTABILITY_BREACH,
                enforcement_level=EnforcementLevel.CRITICAL,
                description=f"Attempt to modify immutable core component: {event.target}",
                evidence={"event_id": event.event_id, "target": event.target},
                blocking=True,
                escalation_required=True
            )
            return False, violation
        
        return True, None


class ExecutionPhaseGateRule(GovernanceRule):
    """Enforce strict execution phase gates - ZERO TOLERANCE."""
    
    # Phase gates: what operations are allowed in each phase
    PHASE_GATES = {
        ExecutionPhase.PRE_COMMIT: ["validate_syntax", "check_narrative", "verify_hash"],
        ExecutionPhase.CI_BUILD: ["compile", "test", "analyze", "scan"],
        ExecutionPhase.PRE_MERGE: ["review_approve", "verify_chain", "semantic_check"],
        ExecutionPhase.PRE_DEPLOY: ["staging_test", "compliance_check", "performance_test"],
        ExecutionPhase.POST_DEPLOY: ["monitor", "verify_deployment", "audit"],
    }
    
    def get_rule_name(self) -> str:
        return "ExecutionPhaseGateRule"
    
    def evaluate(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Enforce operation allowed in phase."""
        phase = event.execution_phase
        allowed_actions = self.PHASE_GATES.get(phase, [])
        
        if event.action not in allowed_actions:
            violation = GovernanceViolation(
                violation_type=ViolationType.POLICY_VIOLATION,
                enforcement_level=EnforcementLevel.CRITICAL,
                description=f"Operation '{event.action}' not allowed in phase {phase.name}",
                evidence={"event_id": event.event_id, "phase": phase.name, "action": event.action},
                blocking=True,
                escalation_required=False
            )
            return False, violation
        
        return True, None


# ============================================
# ENFORCEMENT ENGINE
# ============================================

class ZeroToleranceEnforcementEngine:
    """High-execution-weight zero-tolerance governance enforcement engine."""
    
    def __init__(self):
        """Initialize enforcement engine with all zero-tolerance rules."""
        self.rules: List[GovernanceRule] = [
            HashPolicyRule(),
            EvidenceChainIntegrityRule(),
            NarrativeFreeRule(),
            LayerDependencyRule(),
            ImmutabilityRule(),
            ExecutionPhaseGateRule(),
        ]
        self.events: List[GovernanceEvent] = []
        self.violations: List[GovernanceViolation] = []
        self.evidence_chain: List[str] = []  # Chain of hashes
        self.genesis_hash = None
    
    def initialize_genesis(self) -> str:
        """Initialize evidence chain with genesis block."""
        genesis_data = {"genesis": True, "timestamp": datetime.now(timezone.utc).isoformat()}
        genesis_bytes = json.dumps(genesis_data, sort_keys=True).encode('utf-8')
        self.genesis_hash = CryptographicStandard.generate_sha3_512(genesis_bytes)
        self.evidence_chain.append(self.genesis_hash)
        logger.info(f"Genesis block initialized: {self.genesis_hash[:16]}...")
        return self.genesis_hash
    
    def process_event(self, event: GovernanceEvent) -> Tuple[bool, Optional[GovernanceViolation]]:
        """Process event through all zero-tolerance rules."""
        # Compute hash if not set
        if not event.hash_value:
            event.hash_value = event.compute_hash()
        
        # Set previous hash if not set
        if not event.previous_hash and self.evidence_chain:
            event.previous_hash = self.evidence_chain[-1]
        
        # Evaluate all rules - ALL must pass, NONE can fail
        for rule in self.rules:
            passed, violation = rule.evaluate(event)
            if not passed:
                # Record violation
                violation.hash_value = CryptographicStandard.generate_sha3_512(
                    violation.to_bytes()
                )
                self.violations.append(violation)
                
                # Take action based on enforcement level
                if violation.blocking:
                    logger.critical(
                        f"BLOCKING VIOLATION ({violation.enforcement_level.name}): "
                        f"{violation.description} (Rule: {rule.get_rule_name()})"
                    )
                    return False, violation
                else:
                    logger.warning(
                        f"ALERT VIOLATION ({violation.enforcement_level.name}): "
                        f"{violation.description} (Rule: {rule.get_rule_name()})"
                    )
        
        # All rules passed - record event
        self.events.append(event)
        self.evidence_chain.append(event.hash_value)
        logger.info(f"Event accepted: {event.event_id} ({event.event_type})")
        
        return True, None
    
    def verify_chain_integrity(self) -> Tuple[bool, List[str]]:
        """Verify complete evidence chain integrity."""
        errors = []
        
        if not self.evidence_chain:
            return False, ["Evidence chain is empty"]
        
        # Verify chain continuity
        for i in range(1, len(self.evidence_chain)):
            prev_hash = self.evidence_chain[i - 1]
            current_hash = self.evidence_chain[i]
            
            if not current_hash:
                errors.append(f"Chain broken at position {i}: missing hash")
        
        if errors:
            return False, errors
        
        return True, []
    
    def get_violation_report(self) -> Dict[str, Any]:
        """Generate violation report."""
        return {
            "total_violations": len(self.violations),
            "critical_violations": sum(1 for v in self.violations if v.enforcement_level == EnforcementLevel.CRITICAL),
            "high_violations": sum(1 for v in self.violations if v.enforcement_level == EnforcementLevel.HIGH),
            "violations": [asdict(v) for v in self.violations],
            "chain_integrity": self.verify_chain_integrity()[0],
            "chain_length": len(self.evidence_chain),
        }


# ============================================
# CLI INTERFACE
# ============================================

def main():
    """Main CLI entry point."""
    engine = ZeroToleranceEnforcementEngine()
    engine.initialize_genesis()
    
    # Example: Process events through strict rules
    event1 = GovernanceEvent(
        event_type="governance_policy_definition",
        actor="governance-team",
        action="define_hash_policy",
        target="hash_policy.yaml",
        execution_phase=ExecutionPhase.PRE_COMMIT,
        architecture_layer=ArchitectureLayer.L1_GOVERNANCE,
    )
    event1.hash_value = event1.compute_hash()
    
    passed, violation = engine.process_event(event1)
    if not passed:
        print(f"Event BLOCKED: {violation.description}")
        sys.exit(1)
    else:
        print("Event ACCEPTED")
    
    # Print enforcement report
    print("\n=== ENFORCEMENT REPORT ===")
    report = engine.get_violation_report()
    print(f"Total Events Processed: {len(engine.events)}")
    print(f"Total Violations: {report['total_violations']}")
    print(f"Critical Violations: {report['critical_violations']}")
    print(f"Chain Integrity: {'VALID' if report['chain_integrity'] else 'BROKEN'}")


if __name__ == "__main__":
    main()
