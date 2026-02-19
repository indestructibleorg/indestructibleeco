#!/usr/bin/env python3
"""
GitHub Actions Policy Validator

Validates that all GitHub Actions used in workflows comply with repository policy:
1. All actions must be from approved organizations (e.g., indestructibleorg)
2. All actions must be pinned to full-length commit SHAs (40 characters)
3. No tag references allowed (e.g., @v1, @v2, @main)
4. Docker actions must be pinned to immutable SHA256 digests
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Tuple

# Import shared validation logic
try:
    from . import actions_policy_core
except ImportError:
    # Support running as script directly
    import actions_policy_core


class ActionsPolicyValidator:
    def __init__(self, repo_root: str, policy_file: str):
        self.repo_root = Path(repo_root)
        self.policy_file = Path(policy_file)
        self.policy = self._load_policy()
        self.violations = []
        
    def _load_policy(self) -> dict:
        """Load the actions policy configuration
        
        Uses the shared load_policy_file function for consistency with the CI validator.
        For the standalone tool, we exit on parse errors rather than falling back to defaults.
        """
        policy, error = actions_policy_core.load_policy_file(self.policy_file)
        
        if error:
            # Distinguish between missing file (warning) and parse errors (fatal)
            if not self.policy_file.exists():
                print(f"Warning: Policy file not found at {self.policy_file}")
                print("Using default policy configuration.")
            elif "parse" in error.lower() or "yaml" in error.lower():
                print(f"Error: {error}")
                sys.exit(1)
            else:
                print(f"Warning: {error}")
                print("Using default policy configuration.")
        
        return policy if policy is not None else actions_policy_core.get_default_policy()
    
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
            # Extract actions using shared function
            actions = actions_policy_core.extract_actions_from_workflow(
                workflow_file, self.repo_root
            )
            
            for action_info in actions:
                total_actions += 1
                action_ref = action_info['action']
                
                # Validate using shared function
                violation_messages = actions_policy_core.validate_action_reference(
                    action_ref, self.policy
                )
                
                if violation_messages:
                    total_violations += len(violation_messages)
                    for message in violation_messages:
                        self.violations.append({
                            'file': action_info['file'],
                            'line': action_info['line'],
                            'action': action_ref,
                            'violation': message
                        })
        
        return total_actions, total_violations
    
    def report(self) -> None:
        """Print validation report"""
        if not self.violations:
            print("✓ All GitHub Actions comply with repository policy")
            return
        
        policy_config = self.policy.get('policy', {})
        enforcement_level = policy_config.get('enforcement_level', 'error')
        
        print(f"✗ Found {len(self.violations)} policy violation(s):\n")
        
        for v in self.violations:
            level_str = "ERROR" if enforcement_level == 'error' else "WARNING"
            print(f"  [{level_str}] {v['file']}:{v['line']}")
            print(f"    Action: {v['action']}")
            print(f"    Violation: {v['violation']}")
            print()
        
        if enforcement_level == 'error':
            print("Policy enforcement level: ERROR")
            print("Build will fail due to policy violations.")
        else:
            print("Policy enforcement level: WARNING")
            print("Policy violations detected but build will continue.")


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
    
    validator.report()
    
    if total_violations > 0 and not args.exit_zero:
        policy_config = validator.policy.get('policy', {})
        if policy_config.get('enforcement_level', 'error') == 'error':
            sys.exit(1)
    
    sys.exit(0)


if __name__ == '__main__':
    main()
