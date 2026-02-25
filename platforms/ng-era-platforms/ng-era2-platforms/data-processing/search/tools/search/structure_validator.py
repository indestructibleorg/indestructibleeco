# 
#  @ECO-governed
#  @ECO-layer: search
#  @ECO-semantic: structure_validator
#  @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
# 
#  GL Unified Architecture Governance Framework Activated
# /
"""
Search System Structure Validator
ECO-Layer: GL90-99 (Meta - Validation)
Closure-Signal: validation, evidence
"""
# MNGA-002: Import organization needs review
import os
import re
import json
from typing import Dict, Any
from pathlib import Path
import logging
from datetime import datetime
import hashlib
logger = logging.getLogger(__name__)
class SearchStructureValidator:
    """Validates search system structure against gl-platform.governance standards."""
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.validation_results = {
            'timestamp': datetime.utcnow().isoformat(),
            'root_path': str(self.root_path),
            'passed': True,
            'errors': [],
            'warnings': [],
            'valid_files': []
        }
        self.evidence_chain = []
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        evidence = {
            'timestamp': datetime.utcnow().isoformat(),
            'validator': 'search-structure-validator',
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("Starting search system structure validation")
        self.generate_evidence('validation_start', {'root_path': str(self.root_path)})
        self._validate_directory_structure()
        self._validate_naming_conventions()
        self._validate_closure_signals()
        self._validate_forbidden_files()
        self.validation_results['passed'] = len(self.validation_results['errors']) == 0
        self.validation_results['evidence_chain_length'] = len(self.evidence_chain)
        self.generate_evidence('validation_complete', {
            'passed': self.validation_results['passed'],
            'errors': len(self.validation_results['errors']),
            'warnings': len(self.validation_results['warnings'])
        })
        logger.info(f"Validation complete: {self.validation_results['passed']}")
        return self.validation_results
    def _validate_directory_structure(self):
        required_dirs = [
            'workspace/projects',
            'var/evidence',
            'controlplane',
            'root-policy',
            'tools'
        ]
        for dir_path in required_dirs:
            full_path = self.root_path / dir_path
            if not full_path.exists():
                error = f"Required directory missing: {dir_path}"
                self.validation_results['errors'].append(error)
                self.validation_results['passed'] = False
                logger.error(error)
            else:
                self.validation_results['valid_files'].append(str(full_path))
    def _validate_naming_conventions(self):
        kebab_pattern = re.compile(r'^[a-z0-9\-]+$')
        snake_pattern = re.compile(r'^[a-z0-9\_\.]+$')
        for root, dirs, files in os.walk(self.root_path):
            for dir_name in dirs:
                if not kebab_pattern.match(dir_name):
                    error = f"Invalid directory name: {root}/{dir_name}"
                    self.validation_results['errors'].append(error)
                    logger.error(error)
            for file_name in files:
                if not (kebab_pattern.match(file_name) or snake_pattern.match(file_name)):
                    warning = f"File name suggestion: {root}/{file_name}"
                    self.validation_results['warnings'].append(warning)
                    logger.warning(warning)
    def _validate_closure_signals(self):
        closure_signal_files = ['policy.yaml', 'manifest.yaml']
        for root, dirs, files in os.walk(self.root_path):
            if any(root.endswith(d) for d in ['controlplane', 'workspace', 'root-policy']):
                missing_signals = [f for f in closure_signal_files if f not in files]
                if missing_signals:
                    warning = f"Missing closure signals in {root}: {missing_signals}"
                    self.validation_results['warnings'].append(warning)
    def _validate_forbidden_files(self):
        forbidden_extensions = ['.tmp', '.bak', '.swp', '.swo', '.log', '.DS_Store', 'Thumbs.db']
        for root, dirs, files in os.walk(self.root_path):
            for file_name in files:
                file_ext = Path(file_name).suffix
                if file_ext in forbidden_extensions:
                    error = f"Forbidden file: {root}/{file_name}"
                    self.validation_results['errors'].append(error)
                    logger.error(error)
    def save_report(self, output_path: str):
        report = {
            'validation_results': self.validation_results,
            'evidence_chain': self.evidence_chain
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {output_path}")
def main():
    root_path = Path(__file__).resolve().parents[2]
    validator = SearchStructureValidator(str(root_path))
    results = validator.validate_all()
    print(f"\n{'='*60}")
    print("Search System Structure Validation Results")
    print(f"{'='*60}")
    print(f"Status: {'PASSED' if results['passed'] else 'FAILED'}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Valid Files: {len(results['valid_files'])}")
    print(f"{'='*60}\n")
    if results['errors']:
        print("ERRORS:")
        for error in results['errors']:
            print(f"  - {error}")
        print()
    if results['warnings']:
        print("WARNINGS:")
        for warning in results['warnings']:
            print(f"  - {warning}")
        print()
    validator.save_report(str(root_path / 'var/evidence/validation-report.json'))
    return 0 if results['passed'] else 1
if __name__ == '__main__':
    import sys
    sys.exit(main())
