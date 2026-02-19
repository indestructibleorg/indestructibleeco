#!/usr/bin/env python3
"""
Core GitHub Actions Policy Validation Logic

Shared validation functions used by both the standalone validator and CI engine integration.
This module eliminates code duplication and ensures consistent validation behavior.
"""

import re
from pathlib import Path
from typing import List, Dict, Optional

# Compile SHA pattern once at module level for performance
SHA_PATTERN = re.compile(r'^[a-f0-9]{40}$', re.IGNORECASE)


def extract_actions_from_workflow(workflow_file: Path, repo_root: Path) -> List[Dict]:
    """Extract all 'uses:' statements from a workflow file"""
    try:
        with open(workflow_file, 'r') as f:
            content = f.read()
        
        # Find all 'uses:' statements in actual workflow steps
        # Pattern matches: "- uses:" or "  uses:" (with indentation) at line start
        # Explicitly skip commented lines to avoid false positives
        actions = []
        
        for line_num, line in enumerate(content.split('\n'), 1):
            stripped = line.lstrip()
            
            # Skip comment lines (including inline comments after whitespace)
            if stripped.startswith('#'):
                continue
            
            # Match actual step definitions: "- uses:" or indented "uses:"
            # This anchors to step structure and avoids matching uses: in run: commands or comments
            if re.match(r'^-?\s*uses:\s*', stripped):
                match = re.search(r'uses:\s*([^\s#]+)', stripped)
                if match:
                    action_ref = match.group(1).strip()
                    actions.append({
                        'action': action_ref,
                        'line': line_num,
                        'file': str(workflow_file.relative_to(repo_root))
                    })
        
        return actions
    except Exception as e:
        raise RuntimeError(f"Error parsing workflow {workflow_file}: {e}") from e


def is_local_action(action_ref: str) -> bool:
    """Check if action is a local action reference (./path/to/action)"""
    return action_ref.startswith('./')


def is_docker_action(action_ref: str) -> bool:
    """Check if action is a docker:// action reference"""
    return action_ref.startswith('docker://')


def validate_docker_action(action_ref: str, policy: Dict) -> List[str]:
    """
    Validate docker:// action reference for security
    
    Docker actions should be pinned to immutable SHA256 digests to prevent
    supply-chain attacks via mutable tags.
    
    Args:
        action_ref: The docker action reference (e.g., 'docker://alpine:latest')
        policy: The policy configuration dictionary
    
    Returns:
        List of violation messages (empty if valid)
    """
    violations = []
    
    policy_config = policy.get('policy', {})
    require_docker_digest = policy_config.get('require_docker_digest_pinning', True)
    
    if not require_docker_digest:
        return violations
    
    # Check if docker image is pinned to SHA256 digest
    # Valid format: docker://image@sha256:<64-hex-chars> or docker://registry/image@sha256:<64-hex-chars>
    if '@sha256:' not in action_ref:
        violations.append(
            f"Docker action '{action_ref}' must be pinned to immutable SHA256 digest "
            f"(e.g., docker://alpine@sha256:...). Mutable tags like ':latest' undermine "
            f"supply-chain security."
        )
    else:
        # Validate the digest format: must be exactly 64 hex characters after @sha256:
        match = re.search(r'@sha256:([a-f0-9]+)$', action_ref, re.IGNORECASE)
        if not match or len(match.group(1)) != 64:
            violations.append(
                f"Docker action '{action_ref}' has invalid SHA256 digest format. "
                f"Digest must be exactly 64 hexadecimal characters "
                f"(e.g., docker://alpine@sha256:c5b1261d...)."
            )
    
    return violations


def validate_action_reference(
    action_ref: str,
    policy: Dict
) -> List[str]:
    """
    Validate a single action reference against policy
    
    Args:
        action_ref: The action reference (e.g., 'owner/repo@ref')
        policy: The policy configuration dictionary
    
    Returns:
        List of violation messages (empty if valid)
    """
    violations = []
    
    # Allow local actions (no remote dependencies)
    if is_local_action(action_ref):
        return violations
    
    # Validate docker actions for digest pinning
    if is_docker_action(action_ref):
        return validate_docker_action(action_ref, policy)
    
    # Parse action reference: owner/repo@ref or owner/repo/path@ref
    if '@' not in action_ref:
        violations.append(
            f"Action '{action_ref}' missing version/ref specifier (expected owner/repo@ref)"
        )
        return violations
    
    action_path, ref = action_ref.rsplit('@', 1)
    parts = action_path.split('/')
    
    if len(parts) < 2:
        violations.append(
            f"Invalid action format '{action_ref}' (expected owner/repo@ref)"
        )
        return violations
    
    owner = parts[0]
    repository_name = parts[1]
    action_base = f"{owner}/{repository_name}"
    
    # Check if action is explicitly blocked
    blocked_actions = policy.get('blocked_actions', [])
    for blocked in blocked_actions:
        if action_path.startswith(blocked):
            violations.append(
                f"Action '{action_base}' is explicitly blocked by policy. "
                f"Use manual commands instead."
            )
            break  # Only report one blocklist violation per action
    
    # Check organization ownership requirement
    policy_config = policy.get('policy', {})
    if policy_config.get('require_org_ownership', False):
        allowed_orgs = policy_config.get('allowed_organizations', [])
        if owner not in allowed_orgs:
            violations.append(
                f"Action from '{owner}' is not allowed. "
                f"Only actions from {', '.join(allowed_orgs)} are permitted."
            )
    
    # Check SHA pinning requirement
    is_sha = bool(SHA_PATTERN.match(ref))
    require_sha_pinning = policy_config.get('require_sha_pinning', False)
    block_tag_references = policy_config.get('block_tag_references', False)

    if require_sha_pinning:
        if not is_sha:
            violations.append(
                f"Action '{action_base}@{ref}' must be pinned to a full-length commit SHA "
                f"(40 hex characters); '{ref}' is not a full-length commit SHA."
            )
    elif block_tag_references and not is_sha:
        violations.append(
            f"Action '{action_base}@{ref}' uses a tag or branch reference ('{ref}'), "
            f"which is blocked by policy. Use a specific commit SHA instead."
        )
    
    return violations


def get_default_policy() -> Dict:
    """Get the default policy configuration"""
    return {
        'policy': {
            'require_org_ownership': True,
            'allowed_organizations': ['indestructibleorg'],
            'require_sha_pinning': True,
            'block_tag_references': True,
            'require_docker_digest_pinning': True
        },
        'blocked_actions': [],
        'approved_actions': []
    }


def load_policy_file(policy_file: Path) -> tuple[Optional[Dict], Optional[str]]:
    """
    Load policy from YAML file with graceful fallback
    
    Returns:
        Tuple of (policy_dict, error_message)
        - (None, None) if file doesn't exist (use default policy)
        - (None, "message") if PyYAML not available or parse error (caller should emit warning/error)
        - (dict, None) if successfully loaded
    """
    if not policy_file.exists():
        return (None, None)
    
    try:
        import yaml
    except ImportError:
        # PyYAML not available - caller should warn but use default policy
        return (None, "PyYAML not installed; using default policy. Install PyYAML to use custom policy file.")
    
    try:
        with open(policy_file, 'r') as f:
            loaded = yaml.safe_load(f)
        
        if loaded is None:
            # Empty file - use default policy
            return (None, f"Policy file {policy_file} is empty; using default policy.")
        
        return (loaded, None)
    except yaml.YAMLError as e:
        # Parse error - this is a misconfiguration that should be reported
        return (None, f"Failed to parse policy file {policy_file}: {e}")
    except Exception as e:
        # Other error - report it
        return (None, f"Error reading policy file {policy_file}: {e}")
