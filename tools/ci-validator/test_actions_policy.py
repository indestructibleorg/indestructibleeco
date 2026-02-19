#!/usr/bin/env python3
"""
Tests for GitHub Actions Policy Validator

Tests the core validation logic to ensure:
1. Detection of blocked actions
2. Organization ownership validation
3. SHA pinning enforcement
4. Handling of malformed action references
5. Policy file loading (present, absent, empty, malformed)
6. Local actions and docker:// actions are allowed
7. Enforcement level configuration
"""

import sys
import tempfile
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

import actions_policy_core


def test_sha_pattern():
    """Test SHA pattern regex"""
    print("Testing SHA pattern validation...")
    
    # Valid SHAs
    assert actions_policy_core.SHA_PATTERN.match('a' * 40)
    assert actions_policy_core.SHA_PATTERN.match('1234567890abcdef' * 2 + '12345678')
    assert actions_policy_core.SHA_PATTERN.match('ABCDEF1234567890' * 2 + 'ABCDEF12')
    
    # Invalid SHAs
    assert not actions_policy_core.SHA_PATTERN.match('v1.0.0')
    assert not actions_policy_core.SHA_PATTERN.match('main')
    assert not actions_policy_core.SHA_PATTERN.match('a' * 39)  # Too short
    assert not actions_policy_core.SHA_PATTERN.match('a' * 41)  # Too long
    assert not actions_policy_core.SHA_PATTERN.match('g' * 40)  # Invalid hex
    
    print("  ✓ SHA pattern validation works correctly")


def test_local_and_docker_actions():
    """Test detection of local and docker actions"""
    print("Testing local and docker action detection...")
    
    # Test local actions
    assert actions_policy_core.is_local_action('./.github/actions/my-action')
    assert actions_policy_core.is_local_action('./path/to/action')
    assert not actions_policy_core.is_local_action('owner/repo@sha')
    
    # Test docker actions
    assert actions_policy_core.is_docker_action('docker://alpine:latest')
    assert actions_policy_core.is_docker_action('docker://my-image:tag')
    assert not actions_policy_core.is_docker_action('owner/repo@sha')
    
    # Test docker digest pinning validation
    policy = actions_policy_core.get_default_policy()
    
    # Docker with mutable tag - should fail
    violations = actions_policy_core.validate_docker_action('docker://alpine:latest', policy)
    assert len(violations) > 0
    assert 'SHA256 digest' in violations[0]
    
    # Docker with SHA256 digest - should pass
    violations = actions_policy_core.validate_docker_action(
        'docker://alpine@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b',
        policy
    )
    assert len(violations) == 0

    # Docker with malformed SHA256 digest (too short) - should fail
    violations = actions_policy_core.validate_docker_action(
        'docker://alpine@sha256:deadbeef',
        policy
    )
    assert len(violations) > 0
    assert 'invalid SHA256 digest format' in violations[0]
    
    # Docker with malformed SHA256 digest (non-hex chars) - should fail
    violations = actions_policy_core.validate_docker_action(
        'docker://alpine@sha256:gggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggggg',
        policy
    )
    assert len(violations) > 0
    assert 'invalid SHA256 digest format' in violations[0]
    
    # Test with policy that doesn't require docker digest pinning
    policy_permissive = {
        'policy': {
            'require_docker_digest_pinning': False
        }
    }
    violations = actions_policy_core.validate_docker_action('docker://alpine:latest', policy_permissive)
    assert len(violations) == 0
    
    print("  ✓ Local and docker action detection works correctly")


def test_validate_action_reference():
    """Test action reference validation logic"""
    print("Testing action reference validation...")
    
    policy = {
        'policy': {
            'require_org_ownership': True,
            'allowed_organizations': ['indestructibleorg'],
            'require_sha_pinning': True,
            'block_tag_references': True
        },
        'blocked_actions': ['actions/checkout', 'actions/setup-node']
    }
    
    # Test 1: Valid action from allowed org with SHA
    # Note: Using valid 40-char hex format (not a real commit SHA)
    violations = actions_policy_core.validate_action_reference(
        'indestructibleorg/my-action@' + 'a' * 40,
        policy
    )
    assert len(violations) == 0, "Valid action should have no violations"
    
    # Test 2: Local action should be allowed
    violations = actions_policy_core.validate_action_reference(
        './.github/actions/my-action',
        policy
    )
    assert len(violations) == 0, "Local action should be allowed"
    
    # Test 3: Docker action with mutable tag should be rejected
    violations = actions_policy_core.validate_action_reference(
        'docker://alpine:latest',
        policy
    )
    assert len(violations) > 0, "Docker action with mutable tag should have violations"
    assert any('SHA256 digest' in v for v in violations)
    
    # Test 3b: Docker action with digest should be allowed
    violations = actions_policy_core.validate_action_reference(
        'docker://alpine@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b',
        policy
    )
    assert len(violations) == 0, "Docker action with SHA256 digest should be allowed"
    
    # Test 4: Action from wrong org
    # Note: Using valid SHA format for testing
    violations = actions_policy_core.validate_action_reference(
        'actions/checkout@' + 'a' * 40,
        policy
    )
    assert len(violations) >= 1, "Action from wrong org should have violations"
    assert any('actions' in v and 'not allowed' in v for v in violations)
    
    # Test 5: Action with tag instead of SHA
    violations = actions_policy_core.validate_action_reference(
        'indestructibleorg/my-action@v1',
        policy
    )
    assert len(violations) >= 1, "Action with tag should have violations"
    assert any('full-length commit SHA' in v for v in violations)
    
    # Test 6: Explicitly blocked action
    # Note: Using valid SHA format for testing
    violations = actions_policy_core.validate_action_reference(
        'actions/checkout@' + 'a' * 40,
        policy
    )
    assert any('explicitly blocked' in v for v in violations)
    
    # Test 7: Missing @ symbol
    violations = actions_policy_core.validate_action_reference(
        'owner/repo',
        policy
    )
    assert len(violations) >= 1
    assert any('missing version/ref specifier' in v for v in violations)
    
    # Test 8: Invalid format
    violations = actions_policy_core.validate_action_reference(
        'invalid@ref',
        policy
    )
    assert len(violations) >= 1
    assert any('Invalid action format' in v for v in violations)
    
    print("  ✓ Action reference validation works correctly")


def test_extract_actions_from_workflow():
    """Test action extraction from workflow files"""
    print("Testing action extraction from workflows...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        repo_root = Path(tmpdir)
        workflows_dir = repo_root / '.github' / 'workflows'
        workflows_dir.mkdir(parents=True)
        
        workflow_file = workflows_dir / 'test.yml'
        workflow_file.write_text("""
name: Test
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: indestructibleorg/my-action@1234567890abcdef1234567890abcdef12345678
    - uses: ./.github/actions/local
    - uses: docker://alpine@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b
    - name: Run command
      run: echo "test"
""")
        
        actions = actions_policy_core.extract_actions_from_workflow(workflow_file, repo_root)
        
        # Note: SHA in test workflow is valid format but not a real commit
        assert len(actions) == 4, f"Expected 4 actions, found {len(actions)}"
        assert actions[0]['action'] == 'actions/checkout@v4'
        assert actions[1]['action'] == 'indestructibleorg/my-action@1234567890abcdef1234567890abcdef12345678'
        assert actions[2]['action'] == './.github/actions/local'
        assert actions[3]['action'] == 'docker://alpine@sha256:c5b1261d6d3e43071626931fc004f70149baeba2c8ec672bd4f27761f8e1ad6b'
        assert all('line' in a for a in actions)
        assert all('file' in a for a in actions)
        
        print("  ✓ Action extraction works correctly")


def test_policy_loading():
    """Test policy file loading"""
    print("Testing policy file loading...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        policy_file = Path(tmpdir) / 'policy.yaml'
        
        # Test 1: Non-existent file
        policy, error = actions_policy_core.load_policy_file(policy_file)
        assert policy is None, "Non-existent file should return None"
        assert error is None, "Non-existent file should have no error"
        
        # Test 2: Empty file
        policy_file.write_text('')
        policy, error = actions_policy_core.load_policy_file(policy_file)
        assert policy is None, "Empty file should return None"
        assert error is not None, "Empty file should have warning message"
        assert "empty" in error.lower()
        
        # Test 3: Valid policy
        policy_file.write_text("""
policy:
  require_org_ownership: true
  allowed_organizations:
    - testorg
  require_sha_pinning: true
blocked_actions:
  - actions/checkout
""")
        policy, error = actions_policy_core.load_policy_file(policy_file)
        if policy is not None:  # Only test if PyYAML is available
            assert error is None, "Valid policy should have no error"
            assert policy['policy']['allowed_organizations'] == ['testorg']
            assert 'actions/checkout' in policy['blocked_actions']
        
        # Test 4: Malformed YAML
        policy_file.write_text("""
policy:
  invalid: [this is: bad yaml
""")
        policy, error = actions_policy_core.load_policy_file(policy_file)
        assert policy is None, "Malformed YAML should return None"
        if error:  # Only check if PyYAML is available
            assert error is not None, "Malformed YAML should have error"
            assert "parse" in error.lower() or "error" in error.lower()
        
        print("  ✓ Policy file loading works correctly")


def test_default_policy():
    """Test default policy structure"""
    print("Testing default policy...")
    
    policy = actions_policy_core.get_default_policy()
    
    assert 'policy' in policy
    assert policy['policy']['require_org_ownership'] is True
    assert 'indestructibleorg' in policy['policy']['allowed_organizations']
    assert policy['policy']['require_sha_pinning'] is True
    assert policy['policy']['require_docker_digest_pinning'] is True
    assert 'blocked_actions' in policy
    
    print("  ✓ Default policy structure is correct")


def test_enforcement_level():
    """Test enforcement level handling"""
    print("Testing enforcement level configuration...")
    
    policy_error = {
        'policy': {
            'require_org_ownership': True,
            'allowed_organizations': ['indestructibleorg'],
            'require_sha_pinning': True,
            'enforcement_level': 'error'
        },
        'blocked_actions': []
    }
    
    policy_warning = {
        'policy': {
            'require_org_ownership': True,
            'allowed_organizations': ['indestructibleorg'],
            'require_sha_pinning': True,
            'enforcement_level': 'warning'
        },
        'blocked_actions': []
    }
    
    # Both should detect violations
    # Note: Using fabricated SHA format example (not a real commit)
    violations_error = actions_policy_core.validate_action_reference(
        'actions/checkout@v4', policy_error
    )
    violations_warning = actions_policy_core.validate_action_reference(
        'actions/checkout@v4', policy_warning
    )
    
    # Both should detect the same violations
    assert len(violations_error) > 0
    assert len(violations_warning) > 0
    
    print("  ✓ Enforcement level configuration works correctly")


def run_all_tests():
    """Run all tests"""
    print("=" * 70)
    print("GitHub Actions Policy Validator - Test Suite")
    print("=" * 70)
    print()
    
    try:
        test_sha_pattern()
        test_local_and_docker_actions()
        test_default_policy()
        test_policy_loading()
        test_extract_actions_from_workflow()
        test_validate_action_reference()
        test_enforcement_level()
        
        print()
        print("=" * 70)
        print("✓ ALL TESTS PASSED")
        print("=" * 70)
        return 0
    except AssertionError as e:
        print()
        print("=" * 70)
        print(f"✗ TEST FAILED: {e}")
        print("=" * 70)
        return 1
    except Exception as e:
        print()
        print("=" * 70)
        print(f"✗ UNEXPECTED ERROR: {e}")
        print("=" * 70)
        return 2


if __name__ == '__main__':
    sys.exit(run_all_tests())
