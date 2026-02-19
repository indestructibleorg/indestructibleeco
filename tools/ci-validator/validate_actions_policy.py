#!/usr/bin/env python3
"""
GitHub Actions Policy Validator

Validates that all GitHub Actions used in workflows comply with repository policy:
1. All actions must be from approved organizations (e.g., indestructibleorg)
2. All actions must be pinned to full-length commit SHAs (40 characters)
3. No tag references allowed (e.g., @v1, @v2, @main)
"""

import os
import re
import sys
import yaml
import argparse
from pathlib import Path
from typing import List, Dict, Tuple


class ActionsPolicyValidator:
    def __init__(self, repo_root: str, policy_file: str):
        self.repo_root = Path(repo_root)
        self.policy_file = Path(policy_file)
        self.policy = self._load_policy()
        self.violations = []
        
    def _load_policy(self) -> Dict:
        """Load the actions policy configuration"""
        if not self.policy_file.exists():
            print(f"Warning: Policy file not found at {self.policy_file}")
            return {
                'policy': {
                    'require_org_ownership': True,
                    'allowed_organizations': ['indestructibleorg'],
                    'require_sha_pinning': True,
                    'block_tag_references': True,
                    'enforcement_level': 'error'
                },
                'blocked_actions': [],
                'approved_actions': [],
                'exceptions': []
            }
        
        with open(self.policy_file, 'r') as f:
            return yaml.safe_load(f)
    
    def _extract_actions_from_workflow(self, workflow_file: Path) -> List[Dict]:
        """Extract all 'uses:' statements from a workflow file"""
        try:
            with open(workflow_file, 'r') as f:
                content = f.read()
            
            # Find all 'uses:' statements
            # Pattern: uses: owner/repo@ref or uses: owner/repo/path@ref
            pattern = r'uses:\s*([^\s#]+)'
            actions = []
            
            for line_num, line in enumerate(content.split('\n'), 1):
                match = re.search(pattern, line)
                if match:
                    action_ref = match.group(1).strip()
                    actions.append({
                        'action': action_ref,
                        'line': line_num,
                        'file': str(workflow_file.relative_to(self.repo_root))
                    })
            
            return actions
        except Exception as e:
            print(f"Error parsing workflow {workflow_file}: {e}")
            return []
    
    def _validate_action(self, action_info: Dict) -> List[str]:
        """Validate a single action reference against policy"""
        action_ref = action_info['action']
        violations = []
        
        # Parse action reference: owner/repo@ref or owner/repo/path@ref
        if '@' not in action_ref:
            violations.append(
                f"Action '{action_ref}' missing version/ref specifier"
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
        repo = parts[1]
        action_base = f"{owner}/{repo}"
        
        # Check if action is explicitly blocked
        blocked_actions = self.policy.get('blocked_actions', [])
        for blocked in blocked_actions:
            if action_path.startswith(blocked):
                violations.append(
                    f"Action '{action_base}' is explicitly blocked by policy. "
                    f"Use manual commands instead."
                )
        
        # Check organization ownership requirement
        policy_config = self.policy.get('policy', {})
        if policy_config.get('require_org_ownership', False):
            allowed_orgs = policy_config.get('allowed_organizations', [])
            if owner not in allowed_orgs:
                violations.append(
                    f"Action from '{owner}' is not allowed. "
                    f"Only actions from {', '.join(allowed_orgs)} are permitted."
                )
        
        # Check SHA pinning requirement
        if policy_config.get('require_sha_pinning', False):
            # SHA should be 40 characters hex
            sha_pattern = re.compile(r'^[a-f0-9]{40}$', re.IGNORECASE)
            if not sha_pattern.match(ref):
                # Check if it's a tag reference
                if policy_config.get('block_tag_references', False):
                    violations.append(
                        f"Action '{action_base}@{ref}' must be pinned to full-length commit SHA (40 characters), "
                        f"not tag '{ref}'"
                    )
                else:
                    violations.append(
                        f"Action '{action_base}@{ref}' is not pinned to full-length commit SHA"
                    )
        
        return violations
    
    def validate_all_workflows(self) -> Tuple[int, int]:
        """Validate all workflow files in .github/workflows/"""
        workflows_dir = self.repo_root / '.github' / 'workflows'
        
        if not workflows_dir.exists():
            print(f"No workflows directory found at {workflows_dir}")
            return 0, 0
        
        workflow_files = list(workflows_dir.glob('*.yml')) + list(workflows_dir.glob('*.yaml'))
        
        if not workflow_files:
            print("No workflow files found")
            return 0, 0
        
        total_actions = 0
        total_violations = 0
        
        for workflow_file in workflow_files:
            actions = self._extract_actions_from_workflow(workflow_file)
            
            for action_info in actions:
                total_actions += 1
                action_violations = self._validate_action(action_info)
                
                if action_violations:
                    total_violations += len(action_violations)
                    for violation in action_violations:
                        self.violations.append({
                            'file': action_info['file'],
                            'line': action_info['line'],
                            'action': action_info['action'],
                            'violation': violation
                        })
        
        return total_actions, total_violations
    
    def report(self) -> None:
        """Print validation report"""
        if not self.violations:
            print("✓ All GitHub Actions comply with repository policy")
            return
        
        print(f"✗ Found {len(self.violations)} policy violation(s):\n")
        
        for v in self.violations:
            print(f"  {v['file']}:{v['line']}")
            print(f"    Action: {v['action']}")
            print(f"    Violation: {v['violation']}")
            print()
        
        policy_config = self.policy.get('policy', {})
        enforcement_level = policy_config.get('enforcement_level', 'error')
        
        if enforcement_level == 'error':
            print("Policy enforcement level: ERROR")
            print("Build will fail due to policy violations.")
            return False
        else:
            print("Policy enforcement level: WARNING")
            print("Policy violations detected but build will continue.")
            return True


def main():
    parser = argparse.ArgumentParser(
        description='Validate GitHub Actions against repository policy'
    )
    parser.add_argument(
        '--repo-root',
        default='.',
        help='Repository root directory (default: current directory)'
    )
    parser.add_argument(
        '--policy-file',
        default='.github/allowed-actions.yaml',
        help='Policy configuration file (default: .github/allowed-actions.yaml)'
    )
    parser.add_argument(
        '--exit-zero',
        action='store_true',
        help='Always exit with status 0 even if violations are found'
    )
    
    args = parser.parse_args()
    
    repo_root = os.path.abspath(args.repo_root)
    policy_file = os.path.join(repo_root, args.policy_file)
    
    validator = ActionsPolicyValidator(repo_root, policy_file)
    total_actions, total_violations = validator.validate_all_workflows()
    
    print(f"\nScanned {total_actions} GitHub Actions usage(s)")
    
    success = validator.report()
    
    if total_violations > 0 and not args.exit_zero:
        policy_config = validator.policy.get('policy', {})
        if policy_config.get('enforcement_level', 'error') == 'error':
            sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
