#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: hash_manager
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Supply Chain Verification - Hash Manager
This module handles hash computation and management for verification.
"""
import hashlib
import secrets
from datetime import datetime, timezone
from typing import Dict, Tuple
class HashManager:
    """Manages hash computation and hash chain"""
    def __init__(self):
        """Initialize hash manager"""
        self.hash_chain: Dict[str, str] = {}
        self.reproducible_hashes: Dict[str, str] = {}
    def compute_dual_hash(self, data: str, stage: str) -> Tuple[str, str]:
        """
        Compute dual hash: verification hash + reproducible hash
        Args:
            data: Data to hash
            stage: Stage identifier for hash naming
        Returns:
            Tuple of (verification_hash, reproducible_hash)
        """
        # Verification Hash - for integrity checking
        verification_hash = hashlib.sha3_512(data.encode()).hexdigest()
        # Reproducible Hash - for reproducibility verification
        # (includes timestamp and random salt)
        timestamp = datetime.now(timezone.utc).isoformat()
        salt = secrets.token_hex(16)
        reproducible_data = f"{data}{timestamp}{salt}"
        reproducible_hash = hashlib.sha3_512(reproducible_data.encode()).hexdigest()
        # Store in hash chains
        self.hash_chain[f"{stage}_verification"] = verification_hash
        self.reproducible_hashes[f"{stage}_reproducible"] = reproducible_hash
        return verification_hash, reproducible_hash
    def get_hash_chain(self) -> Dict[str, str]:
        """Get the verification hash chain"""
        return self.hash_chain
    def get_reproducible_hashes(self) -> Dict[str, str]:
        """Get the reproducible hash chain"""
        return self.reproducible_hashes
    def clear_hashes(self) -> None:
        """Clear all hash chains"""
        self.hash_chain.clear()
        self.reproducible_hashes.clear()