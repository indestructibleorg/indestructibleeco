#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: pipeline_validator
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
ETL Pipeline Structure Validator
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
from datetime import datetime, timezone
import hashlib
logger = logging.getLogger(__name__)
class PipelineValidator:
    """
    Validates ETL pipeline structure against gl-platform.gl-platform.governance standards.
    Implements zero-tolerance validation for directory and file compliance.
    """
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.root_label = self.root_path.name
        self.validation_results = {
            'timestamp': self._current_timestamp(),
            'root_path': self.root_label,
            'passed': True,
            'errors': [],
            'warnings': [],
            'valid_files': [],
            'invalid_files': []
        }
        self.evidence_chain = []
    def _current_timestamp(self) -> str:
        env_timestamp = os.getenv('PIPELINE_VALIDATION_TIMESTAMP')
        if env_timestamp:
            return env_timestamp
        source_date_epoch = os.getenv('SOURCE_DATE_EPOCH')
        if source_date_epoch:
            try:
                epoch_value = int(source_date_epoch)
            except ValueError:
                epoch_value = None
            if epoch_value is not None:
                return datetime.fromtimestamp(epoch_value, timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
    def _format_path(self, path: Path) -> str:
        try:
            relative = path.relative_to(self.root_path)
        except ValueError:
            return str(path)
        relative_value = relative.as_posix()
        if relative_value == '.':
            return self.root_label
        return f"{self.root_label}/{relative_value}"
    def generate_evidence(self, operation: str, details: Dict[str, Any]) -> str:
        """Generate evidence entry for validation operation."""
        evidence = {
            'timestamp': self._current_timestamp(),
            'validator': 'pipeline-structure-validator',
            'operation': operation,
            'details': details
        }
        evidence_hash = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        evidence['hash'] = evidence_hash
        self.evidence_chain.append(evidence)
        return evidence_hash
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        logger.info("Starting pipeline structure validation")
        self.generate_evidence('validation_start', {'root_path': self.root_label})
        self._validate_directory_structure()
        self._validate_naming_conventions()
        self._validate_closure_signals()
        self._validate_forbidden_files()
        self.validation_results['passed'] = len(self.validation_results['errors']) == 0
        self.generate_evidence('validation_complete', {
            'passed': self.validation_results['passed'],
            'errors': len(self.validation_results['errors']),
            'warnings': len(self.validation_results['warnings'])
        })
        self.validation_results['evidence_chain_length'] = len(self.evidence_chain)
        logger.info(f"Validation complete: {self.validation_results['passed']}")
        return self.validation_results
    def _validate_directory_structure(self):
        """Validate required directory structure."""
        required_dirs = [
            'controlplane',
            'controlplane/gl-platform.gl-platform.governance',
            'controlplane/baseline',
            'workspace',
            'workspace/projects',
            'var/evidence',
            'root-policy',
            'root-policy/naming-convention',
            'root-contracts',
            'root-evidence',
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
                self.validation_results['valid_files'].append(self._format_path(full_path))
        self.generate_evidence('directory_structure_validated', {
            'required_dirs': required_dirs,
            'errors': len([e for e in self.validation_results['errors'] if 'directory' in e.lower()])
        })
    def _validate_naming_conventions(self):
        """Validate naming conventions."""
        kebab_pattern = re.compile(r'^[a-z0-9\-]+$')
        snake_pattern = re.compile(r'^[a-z0-9\_\.]+$')
        for root, dirs, files in os.walk(self.root_path):
            for dir_name in dirs:
                if not kebab_pattern.match(dir_name):
                    error = f"Invalid directory name (not kebab-case): {self._format_path(Path(root) / dir_name)}"
                    self.validation_results['errors'].append(error)
                    logger.error(error)
            for file_name in files:
                file_stem = Path(file_name).stem
                if not (kebab_pattern.match(file_stem) or snake_pattern.match(file_stem)):
                    warning = f"File name suggestion (not kebab/snake_case): {self._format_path(Path(root) / file_name)}"
                    self.validation_results['warnings'].append(warning)
                    logger.warning(warning)
        self.generate_evidence('naming_conventions_validated', {
            'errors': len([e for e in self.validation_results['errors'] if 'name' in e.lower()]),
            'warnings': len([w for w in self.validation_results['warnings'] if 'name' in w.lower()])
        })
    def _validate_closure_signals(self):
        """Validate required closure signal files."""
        closure_signal_files = [
            'policy.yaml',
            'manifest.yaml',
            'evidence-chain.json'
        ]
        for root, dirs, files in os.walk(self.root_path):
            if any(root.endswith(d) for d in ['controlplane', 'workspace', 'root-policy']):
                missing_signals = [f for f in closure_signal_files if f not in files]
                if missing_signals:
                    warning = f"Missing closure signals in {self._format_path(Path(root))}: {missing_signals}"
                    self.validation_results['warnings'].append(warning)
                    logger.warning(warning)
        self.generate_evidence('closure_signals_validated', {
            'warnings': len([w for w in self.validation_results['warnings'] if 'closure' in w.lower()])
        })
    def _validate_forbidden_files(self):
        """Validate no forbidden files exist."""
        forbidden_extensions = [
            '.tmp', '.bak', '.swp', '.swo', '.log',
            '.DS_Store', 'Thumbs.db', '.old', '.legacy'
        ]
        forbidden_dirs = [
            'tmp', 'temp', 'backup', 'old', 'legacy', 'misc'
        ]
        for root, dirs, files in os.walk(self.root_path):
            for dir_name in dirs:
                if dir_name.lower() in forbidden_dirs:
                    error = f"Forbidden directory found: {self._format_path(Path(root) / dir_name)}"
                    self.validation_results['errors'].append(error)
                    logger.error(error)
            for file_name in files:
                file_ext = Path(file_name).suffix
                if file_ext in forbidden_extensions:
                    error = f"Forbidden file type: {self._format_path(Path(root) / file_name)}"
                    self.validation_results['errors'].append(error)
                    logger.error(error)
        self.generate_evidence('forbidden_files_validated', {
            'errors': len([e for e in self.validation_results['errors'] if 'forbidden' in e.lower()])
        })
    def save_report(self, output_path: str):
        """Save validation report to file."""
        report = {
            'validation_results': self.validation_results,
            'evidence_chain': self.evidence_chain
        }
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {output_path}")
def main():
    """Main validation entry point."""
    root_path = Path(__file__).resolve().parents[2]
    validator = PipelineValidator(str(root_path))
    results = validator.validate_all()
    print(f"\n{'='*60}")
    print("ETL Pipeline Structure Validation Results")
    print(f"{'='*60}")
    print(f"Status: {'PASSED' if results['passed'] else 'FAILED'}")
    print(f"Errors: {len(results['errors'])}")
    print(f"Warnings: {len(results['warnings'])}")
    print(f"Valid Files: {len(results['valid_files'])}")
    print(f"Evidence Chain Entries: {results['evidence_chain_length']}")
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
