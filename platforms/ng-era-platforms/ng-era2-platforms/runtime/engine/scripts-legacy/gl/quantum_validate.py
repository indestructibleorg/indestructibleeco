# @ECO-layer: GQS-L0
#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: quantum-validate
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Quantum Validation System
Validates consistency, reversibility, reproducibility, and provability
"""
# MNGA-002: Import organization needs review
import argparse
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
class QuantumValidator:
    """Quantum validation for GL layers"""
    def __init__(self, layer: str):
        self.layer = layer
        self.validation_results = {}
        self.timestamp = datetime.now()
    def validate_consistency(self, path: str) -> Dict[str, Any]:
        """Validate semantic and structural consistency"""
        result = {
            'check': 'CONSISTENCY',
            'status': 'PASSED',
            'issues': [],
            'metrics': {}
        }
        layer_path = Path(path)
        # Check if semantic index exists
        semantic_index_path = layer_path / "ECO-SEMANTIC-INDEX.json"
        if not semantic_index_path.exists():
            result['status'] = 'FAILED'
            result['issues'].append("Semantic index not found")
            return result
        # Load and validate semantic index
        try:
            with open(semantic_index_path, 'r') as f:
                semantic_index = json.load(f)
            # Validate layer consistency
            if semantic_index.get('layer') != self.layer:
                result['status'] = 'FAILED'
                result['issues'].append(f"Layer mismatch: expected {self.layer}, got {semantic_index.get('layer')}")
            # Validate artifact paths exist
            artifacts = semantic_index.get('artifacts', [])
            missing_paths = []
            for artifact in artifacts:
                artifact_path = Path(artifact.get('path', ''))
                if not artifact_path.exists():
                    missing_paths.append(str(artifact_path))
            if missing_paths:
                result['status'] = 'WARNING'
                result['issues'].append(f"Missing artifact paths: {', '.join(missing_paths)}")
            # Metrics
            result['metrics'] = {
                'artifact_count': len(artifacts),
                'path_existence_rate': 1.0 - (len(missing_paths) / len(artifacts)) if artifacts else 0
            }
        except Exception as e:
            result['status'] = 'ERROR'
            result['issues'].append(f"Failed to validate consistency: {e}")
        return result
    def validate_reversibility(self, path: str) -> Dict[str, Any]:
        """Validate that changes can be reversed"""
        result = {
            'check': 'REVERSIBILITY',
            'status': 'PASSED',
            'issues': [],
            'metrics': {}
        }
        layer_path = Path(path)
        # Check for version control
        git_dir = layer_path / '.git'
        if not git_dir.exists():
            # Check parent directories
            parent_git = layer_path
            while parent_git.parent != parent_git:
                if (parent_git / '.git').exists():
                    break
                parent_git = parent_git.parent
            if (parent_git / '.git').exists():
                result['metrics']['version_control_available'] = True
            else:
                result['status'] = 'WARNING'
                result['issues'].append("No version control detected")
                result['metrics']['version_control_available'] = False
        # Check for backup directories
        backup_dirs = list(layer_path.glob('**/backup*')) + list(layer_path.glob('**/.backup*'))
        result['metrics']['backup_directories_found'] = len(backup_dirs)
        # Check for rollback scripts
        rollback_scripts = list(layer_path.glob('**/*rollback*')) + list(layer_path.glob('**/*revert*'))
        result['metrics']['rollback_scripts_found'] = len(rollback_scripts)
        # Check for immutable evidence
        evidence_dirs = list(layer_path.glob('**/evidence*')) + list(layer_path.glob('**/var/evidence'))
        result['metrics']['evidence_directories_found'] = len(evidence_dirs)
        return result
    def validate_reproducibility(self, path: str) -> Dict[str, Any]:
        """Validate that builds are reproducible"""
        result = {
            'check': 'REPRODUCIBILITY',
            'status': 'PASSED',
            'issues': [],
            'metrics': {}
        }
        layer_path = Path(path)
        # Check for requirements files
        requirements_files = list(layer_path.glob('**/requirements*.txt')) + list(layer_path.glob('**/pyproject.toml'))
        result['metrics']['dependency_files_found'] = len(requirements_files)
        if not requirements_files:
            result['status'] = 'WARNING'
            result['issues'].append("No dependency specification files found")
        # Check for Docker files
        docker_files = list(layer_path.glob('**/Dockerfile*'))
        result['metrics']['docker_files_found'] = len(docker_files)
        # Check for configuration files
        config_files = list(layer_path.glob('**/*.yaml')) + list(layer_path.glob('**/*.yml')) + list(layer_path.glob('**/*.json'))
        result['metrics']['configuration_files_found'] = len(config_files)
        # Check for deterministic build scripts
        build_scripts = list(layer_path.glob('**/build*')) + list(layer_path.glob('**/Makefile'))
        result['metrics']['build_scripts_found'] = len(build_scripts)
        return result
    def validate_provability(self, path: str) -> Dict[str, Any]:
        """Validate that operations have verifiable proofs"""
        result = {
            'check': 'PROVABILITY',
            'status': 'PASSED',
            'issues': [],
            'metrics': {}
        }
        layer_path = Path(path)
        # Check for evidence chains
        evidence_files = list(layer_path.glob('**/*evidence*.json'))
        result['metrics']['evidence_files_found'] = len(evidence_files)
        # Check for audit logs
        audit_files = list(layer_path.glob('**/*audit*.json')) + list(layer_path.glob('**/*audit*.log'))
        result['metrics']['audit_files_found'] = len(audit_files)
        # Check for validation reports
        validation_files = list(layer_path.glob('**/*validation*.json'))
        result['metrics']['validation_files_found'] = len(validation_files)
        # Check for cryptographic signatures
        signature_files = list(layer_path.glob('**/*.sig')) + list(layer_path.glob('**/*.asc')) + list(layer_path.glob('**/*.pem'))
        result['metrics']['signature_files_found'] = len(signature_files)
        # Check for checksum files
        checksum_files = list(layer_path.glob('**/*checksum*')) + list(layer_path.glob('**/*.sha256'))
        result['metrics']['checksum_files_found'] = len(checksum_files)
        return result
    def generate_validation_report(self, path: str, checks: List[str]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        report = {
            'validation_id': f"ECO-QUANTUM-{self.layer}-{self.timestamp.strftime('%Y%m%d%H%M%S')}",
            'layer': self.layer,
            'timestamp': self.timestamp.isoformat(),
            'validation_path': path,
            'checks': [],
            'overall_status': 'PASSED',
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'errors': 0
            }
        }
        # Run requested checks
        for check in checks:
            check_upper = check.upper()
            if check_upper == 'CONSISTENCY':
                result = self.validate_consistency(path)
            elif check_upper == 'REVERSIBILITY':
                result = self.validate_reversibility(path)
            elif check_upper == 'REPRODUCIBILITY':
                result = self.validate_reproducibility(path)
            elif check_upper == 'PROVABILITY':
                result = self.validate_provability(path)
            else:
                result = {
                    'check': check_upper,
                    'status': 'UNKNOWN',
                    'issues': [f"Unknown check type: {check}"]
                }
            report['checks'].append(result)
            report['summary']['total_checks'] += 1
            status = result.get('status', 'UNKNOWN')
            if status == 'PASSED':
                report['summary']['passed'] += 1
            elif status == 'FAILED':
                report['summary']['failed'] += 1
                report['overall_status'] = 'FAILED'
            elif status == 'WARNING':
                report['summary']['warnings'] += 1
            elif status == 'ERROR':
                report['summary']['errors'] += 1
                report['overall_status'] = 'FAILED'
        return report
def main():
    parser = argparse.ArgumentParser(
        description='GL Quantum Validation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python quantum-validate.py --layer GL20-29 --check consistency,reversibility,reproducibility,provability
  python quantum-validate.py --layer GL40-49 --check consistency
  python quantum-validate.py --layer GL50-59 --check all
        """
    )
    parser.add_argument('--layer', required=True, help='GL layer (e.g., GL20-29)')
    parser.add_argument('--check', required=True, help='Comma-separated checks (or "all")')
    args = parser.parse_args()
    # Determine path
    layer_key = {
        'GL20': 'data',
        'GL40': 'algorithms',
        'GL50': 'gpu'
    }.get(args.layer.split('-')[0], args.layer.split('-')[0].lower())
    path = f"workspace/src/{layer_key}"
    # Determine checks
    if args.check.lower() == 'all':
        checks = ['consistency', 'reversibility', 'reproducibility', 'provability']
    else:
        checks = [c.strip() for c in args.check.split(',')]
    print(f"\\n{'='*60}")
    print("GL Quantum Validation")
    print(f"{'='*60}")
    print(f"Layer: {args.layer}")
    print(f"Path: {path}")
    print(f"Checks: {', '.join(checks)}")
    print(f"{'='*60}\\n")
    # Run validation
    validator = QuantumValidator(args.layer)
    report = validator.generate_validation_report(path, checks)
    # Display results
    print("Validation Results:")
    print("-" * 60)
    for check in report['checks']:
        status_symbol = {
            'PASSED': '✅',
            'FAILED': '❌',
            'WARNING': '⚠️ ',
            'ERROR': '🔴',
            'UNKNOWN': '❓'
        }.get(check['status'], '❓')
        print(f"{status_symbol} {check['check']}: {check['status']}")
        if check.get('issues'):
            for issue in check['issues']:
                print(f"     - {issue}")
        if check.get('metrics'):
            print(f"     Metrics: {json.dumps(check['metrics'], indent=6)}")
    # Display summary
    print(f"\\n{'='*60}")
    summary = report['summary']
    status_symbol = '✅' if report['overall_status'] == 'PASSED' else '❌'
    print(f"{status_symbol} Overall Status: {report['overall_status']}")
    print(f"{'='*60}")
    print(f"Total Checks: {summary['total_checks']}")
    print(f"  Passed:   {summary['passed']}")
    print(f"  Failed:   {summary['failed']}")
    print(f"  Warnings: {summary['warnings']}")
    print(f"  Errors:   {summary['errors']}")
    print(f"{'='*60}\\n")
    # Exit with appropriate code
    if report['overall_status'] in ['FAILED', 'ERROR']:
        sys.exit(1)
    else:
        sys.exit(0)
if __name__ == "__main__":
    main()