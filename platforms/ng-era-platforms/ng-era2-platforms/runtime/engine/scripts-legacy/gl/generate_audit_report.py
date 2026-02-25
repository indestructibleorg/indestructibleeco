#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: generate-audit-report
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL Audit Report Generator
Generates audit reports for GL layers
"""
# MNGA-002: Import organization needs review
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
class AuditReportGenerator:
    """Generate audit reports for GL layers"""
    def __init__(self, layer: str, output_dir: str):
        self.layer = layer
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = datetime.now()
    def analyze_layer_structure(self, layer_path: Path) -> Dict[str, Any]:
        """Analyze layer structure"""
        structure_analysis = {
            'total_files': 0,
            'total_directories': 0,
            'file_types': {},
            'modules': [],
            'has_semantic_index': False,
            'has_tests': False
        }
        if not layer_path.exists():
            return structure_analysis
        for item in layer_path.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                structure_analysis['total_files'] += 1
                # Track file types
                ext = item.suffix.lower()
                if ext:
                    structure_analysis['file_types'][ext] = structure_analysis['file_types'].get(ext, 0) + 1
                # Check for semantic index
                if item.name == 'ECO-SEMANTIC-INDEX.json':
                    structure_analysis['has_semantic_index'] = True
                # Check for tests
                if 'test' in item.name.lower() or 'tests' in str(item):
                    structure_analysis['has_tests'] = True
            elif item.is_dir():
                structure_analysis['total_directories'] += 1
        # Identify modules
        if layer_path.is_dir():
            for item in layer_path.iterdir():
                if item.is_dir() and not item.name.startswith('.'):
                    structure_analysis['modules'].append({
                        'name': item.name,
                        'path': str(item),
                        'file_count': len(list(item.rglob('*')))
                    })
        return structure_analysis
    def check_compliance(self, layer_path: Path) -> Dict[str, Any]:
        """Check layer compliance with GL standards"""
        compliance_check = {
            'status': 'COMPLIANT',
            'violations': [],
            'warnings': []
        }
        if not layer_path.exists():
            compliance_check['status'] = 'NON_COMPLIANT'
            compliance_check['violations'].append(f"Layer path does not exist: {layer_path}")
            return compliance_check
        # Check for semantic index
        semantic_index = layer_path / "ECO-SEMANTIC-INDEX.json"
        if not semantic_index.exists():
            compliance_check['status'] = 'NON_COMPLIANT'
            compliance_check['violations'].append("Missing ECO-SEMANTIC-INDEX.json")
        # Check for module initialization files
        for item in layer_path.iterdir():
            if item.is_dir():
                init_file = item / "__init__.py"
                if not init_file.exists():
                    compliance_check['warnings'].append(f"Module {item.name} missing __init__.py")
        # Check for test directories
        test_dirs = list(layer_path.glob('*/tests'))
        if not test_dirs:
            compliance_check['warnings'].append("No test directories found")
        return compliance_check
    def generate_audit_findings(self, layer_path: Path) -> List[Dict[str, Any]]:
        """Generate audit findings"""
        findings = []
        if not layer_path.exists():
            findings.append({
                'severity': 'CRITICAL',
                'category': 'STRUCTURE',
                'finding': f"Layer directory does not exist: {layer_path}",
                'recommendation': 'Create layer directory structure'
            })
            return findings
        # Check semantic index
        semantic_index = layer_path / "ECO-SEMANTIC-INDEX.json"
        if semantic_index.exists():
            try:
                with open(semantic_index, 'r') as f:
                    index_data = json.load(f)
                if index_data.get('layer') != self.layer:
                    findings.append({
                        'severity': 'HIGH',
                        'category': 'SEMANTIC_INDEX',
                        'finding': f"Semantic index layer mismatch: expected {self.layer}, got {index_data.get('layer')}",
                        'recommendation': 'Update semantic index layer field'
                    })
            except Exception as e:
                findings.append({
                    'severity': 'HIGH',
                    'category': 'SEMANTIC_INDEX',
                    'finding': f"Invalid semantic index: {e}",
                    'recommendation': 'Fix semantic index JSON structure'
                })
        else:
            findings.append({
                'severity': 'HIGH',
                'category': 'SEMANTIC_INDEX',
                'finding': 'Missing ECO-SEMANTIC-INDEX.json',
                'recommendation': 'Generate semantic index for the layer'
            })
        # Check module completeness
        for item in layer_path.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                init_file = item / "__init__.py"
                if not init_file.exists():
                    findings.append({
                        'severity': 'MEDIUM',
                        'category': 'MODULE_STRUCTURE',
                        'finding': f"Module {item.name} missing __init__.py",
                        'recommendation': f'Create __init__.py for {item.name} module'
                    })
                # Check test directory
                test_dir = item / "tests"
                if not test_dir.exists():
                    findings.append({
                        'severity': 'LOW',
                        'category': 'TEST_COVERAGE',
                        'finding': f"Module {item.name} missing tests directory",
                        'recommendation': f'Create tests directory for {item.name}'
                    })
        return findings
    def generate_audit_report(self) -> Dict[str, Any]:
        """Generate comprehensive audit report"""
        layer_path = Path(f"workspace/src/{self.layer.split('-')[0].lower()}")
        report_id = f"ECO-AUDIT-{self.layer}-{self.timestamp.strftime('%Y%m%d%H%M%S')}"
        report = {
            'report_id': report_id,
            'layer': self.layer,
            'timestamp': self.timestamp.isoformat(),
            'layer_path': str(layer_path),
            'structure_analysis': self.analyze_layer_structure(layer_path),
            'compliance_check': self.check_compliance(layer_path),
            'audit_findings': self.generate_audit_findings(layer_path),
            'summary': {
                'total_findings': 0,
                'critical': 0,
                'high': 0,
                'medium': 0,
                'low': 0
            }
        }
        # Generate summary
        for finding in report['audit_findings']:
            report['summary']['total_findings'] += 1
            severity = finding.get('severity', 'UNKNOWN').upper()
            if severity in report['summary']:
                report['summary'][severity] += 1
        # Set overall compliance status
        if report['summary']['critical'] > 0 or report['summary']['high'] > 0:
            report['overall_compliance_status'] = 'NON_COMPLIANT'
        elif report['summary']['medium'] > 0:
            report['overall_compliance_status'] = 'PARTIALLY_COMPLIANT'
        else:
            report['overall_compliance_status'] = 'COMPLIANT'
        return report
    def save_report(self, report: Dict[str, Any]) -> Path:
        """Save audit report to file"""
        filename = f"audit-{self.layer}-{self.timestamp.strftime('%Y%m%d%H%M%S')}.json"
        filepath = self.output_dir / filename
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2)
        return filepath
def main():
    parser = argparse.ArgumentParser(
        description='Generate GL audit report',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python generate-audit-report.py --layer GL20-29 --output var/audit
  python generate-audit-report.py --layer GL40-49 --output var/audit
  python generate-audit-report.py --layer GL50-59 --output var/audit
        """
    )
    parser.add_argument('--layer', required=True, help='GL layer (e.g., GL20-29)')
    parser.add_argument('--output', required=True, help='Output directory')
    args = parser.parse_args()
    print(f"\\n{'='*60}")
    print("GL Audit Report Generator")
    print(f"{'='*60}")
    print(f"Layer: {args.layer}")
    print(f"Output: {args.output}")
    print(f"{'='*60}\\n")
    # Generate audit report
    generator = AuditReportGenerator(args.layer, args.output)
    report = generator.generate_audit_report()
    # Save report
    filepath = generator.save_report(report)
    # Display results
    print(f"Report ID: {report['report_id']}")
    print("\\nStructure Analysis:")
    print(f"  Total Files: {report['structure_analysis']['total_files']}")
    print(f"  Total Directories: {report['structure_analysis']['total_directories']}")
    print(f"  Modules: {len(report['structure_analysis']['modules'])}")
    print(f"  Has Semantic Index: {report['structure_analysis']['has_semantic_index']}")
    print(f"  Has Tests: {report['structure_analysis']['has_tests']}")
    print(f"\\nCompliance Status: {report['compliance_check']['status']}")
    if report['compliance_check'].get('violations'):
        print("  Violations:")
        for violation in report['compliance_check']['violations']:
            print(f"    - {violation}")
    print("\\nAudit Findings:")
    summary = report['summary']
    print(f"  Total: {summary['total_findings']}")
    print(f"  Critical: {summary['critical']}")
    print(f"  High: {summary['high']}")
    print(f"  Medium: {summary['medium']}")
    print(f"  Low: {summary['low']}")
    print(f"\\nOverall Compliance: {report['overall_compliance_status']}")
    print(f"\\n{'='*60}")
    print(f"✅ Audit report saved to: {filepath}")
    print(f"{'='*60}\\n")
if __name__ == "__main__":
    main()