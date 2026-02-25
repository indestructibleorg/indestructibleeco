#!/usr/bin/env python3
"""
GL Runtime Platform - Naming Violations Scanner
Scans the entire repository for naming convention violations

@ECO-governed
@ECO-layer: GL10-29 Operational
@ECO-semantic: naming-violations-scanner
@ECO-charter-version: 1.0.0
"""

# MNGA-002: Import organization needs review
import os
import re
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

class NamingViolationScanner:
    """Scan repository for naming convention violations"""
    
    def __init__(self, root_path="/workspace/machine-native-ops"):
        self.root_path = Path(root_path)
        self.violations = defaultdict(list)
        self.stats = {
            'total_files': 0,
            'scanned_files': 0,
            'total_violations': 0,
            'violation_types': defaultdict(int)
        }
        
        # Define naming patterns to check
        self.patterns = {
            # File/Directory naming violations
            'file_uppercase': {
                'description': 'Files with uppercase letters (should be lowercase)',
                'pattern': r'^[A-Z]',
                'severity': 'low',
                'apply_to': ['files', 'directories']
            },
            'file_spaces': {
                'description': 'Files/directories with spaces',
                'pattern': r' ',
                'severity': 'high',
                'apply_to': ['files', 'directories']
            },
            'file_special_chars': {
                'description': 'Files/directories with special characters',
                'pattern': r'[^a-zA-Z0-9._-]',
                'severity': 'medium',
                'apply_to': ['files', 'directories']
            },
            
            # Legacy naming patterns
            'axiom_references': {
                'description': 'AXIOM namespace references (should be gl-runtime)',
                'pattern': r'\baxiom\b',
                'severity': 'high',
                'apply_to': ['content']
            },
            'legacy_apis': {
                'description': 'Legacy API version references',
                'pattern': r'apiVersion:\s*v\d+beta',
                'severity': 'medium',
                'apply_to': ['content']
            },
            
            # Code naming violations
            'kebab_case_in_code': {
                'description': 'Kebab-case identifiers in code (should be snake_case)',
                'pattern': r'\b[a-z]+-[a-z]+\b',
                'severity': 'low',
                'apply_to': ['content'],
                'extensions': ['.py', '.js', '.ts']
            },
            'camelCase_variables': {
                'description': 'camelCase variable names (should be snake_case in Python)',
                'pattern': r'\b[a-z][a-z0-9]*[A-Z]',
                'severity': 'low',
                'apply_to': ['content'],
                'extensions': ['.py']
            }
        }
        
        # Files/directories to skip
        self.skip_patterns = [
            '.git/',
            'node_modules/',
            '__pycache__/',
            '.pytest_cache/',
            '.axiom-refactor-backup/',
            'dist/',
            'build/',
            '.next/',
            'coverage/',
            '*.pyc',
            '*.log',
            'package-lock.json',
            'yarn.lock',
            '.DS_Store'
        ]
    
    def should_skip(self, path):
        """Check if path should be skipped"""
        path_str = str(path)
        for pattern in self.skip_patterns:
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(path_str, pattern):
                    return True
            elif pattern in path_str:
                return True
        return False
    
    def scan_file_naming(self, file_path):
        """Scan file/directory name for violations"""
        if self.should_skip(file_path):
            return
        
        name = file_path.name
        file_type = 'directories' if file_path.is_dir() else 'files'
        
        for pattern_name, pattern_info in self.patterns.items():
            if file_type not in pattern_info['apply_to']:
                continue
            
            if re.search(pattern_info['pattern'], name):
                self.violations[pattern_name].append({
                    'type': 'naming',
                    'path': str(file_path),
                    'name': name,
                    'severity': pattern_info['severity'],
                    'description': pattern_info['description']
                })
                self.stats['violation_types'][pattern_name] += 1
                self.stats['total_violations'] += 1
    
    def scan_content(self, file_path):
        """Scan file content for violations"""
        if self.should_skip(file_path):
            return
        
        # Check if file should be scanned for content
        content_extensions = ['.py', '.js', '.ts', '.yaml', '.yml', '.sh', '.json', '.md']
        if file_path.suffix.lower() not in content_extensions:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return
        
        for pattern_name, pattern_info in self.patterns.items():
            if 'content' not in pattern_info['apply_to']:
                continue
            
            # Check file extension restrictions
            if 'extensions' in pattern_info:
                if file_path.suffix.lower() not in pattern_info['extensions']:
                    continue
            
            for line_num, line in enumerate(lines, 1):
                matches = re.finditer(pattern_info['pattern'], line)
                for match in matches:
                    self.violations[pattern_name].append({
                        'type': 'content',
                        'path': str(file_path),
                        'line': line_num,
                        'match': match.group(),
                        'severity': pattern_info['severity'],
                        'description': pattern_info['description']
                    })
                    self.stats['violation_types'][pattern_name] += 1
                    self.stats['total_violations'] += 1
    
    def scan_repository(self):
        """Scan entire repository"""
        print("=" * 80)
        print("GL Runtime Platform - Naming Violations Scanner")
        print("=" * 80)
        print(f"Root Path: {self.root_path}")
        print(f"Scan Time: {datetime.now().isoformat()}")
        print("=" * 80)
        
        # Get all files and directories
        all_items = []
        for item in self.root_path.rglob('*'):
            if not self.should_skip(item):
                all_items.append(item)
        
        self.stats['total_files'] = len(all_items)
        print(f"Total items found: {self.stats['total_files']}")
        print("Scanning...")
        
        # Scan file/directory names
        for item in all_items:
            self.scan_file_naming(item)
            self.stats['scanned_files'] += 1
        
        # Scan file content
        files_to_scan = [item for item in all_items if item.is_file()]
        for file_path in files_to_scan:
            self.scan_content(file_path)
        
        print(f"Scan complete. Scanned {self.stats['scanned_files']} items.")
        print("=" * 80)
    
    def generate_report(self):
        """Generate detailed report"""
        report = {
            'scan_info': {
                'timestamp': datetime.now().isoformat(),
                'root_path': str(self.root_path),
                'total_items': self.stats['total_files'],
                'scanned_items': self.stats['scanned_files'],
                'total_violations': self.stats['total_violations']
            },
            'violation_summary': dict(self.stats['violation_types']),
            'violation_details': dict(self.violations),
            'patterns_checked': len(self.patterns)
        }
        
        return report
    
    def print_summary(self):
        """Print summary of violations"""
        print("\n" + "=" * 80)
        print("NAMING VIOLATIONS SUMMARY")
        print("=" * 80)
        print(f"Total Items Scanned: {self.stats['scanned_files']}")
        print(f"Total Violations Found: {self.stats['total_violations']}")
        print(f"Violation Types Detected: {len(self.stats['violation_types'])}")
        print("=" * 80)
        
        if self.stats['total_violations'] > 0:
            print("\nViolations by Type:")
            print("-" * 80)
            
            # Sort by count (descending)
            sorted_violations = sorted(
                self.stats['violation_types'].items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            for violation_type, count in sorted_violations:
                pattern_info = self.patterns.get(violation_type, {})
                severity = pattern_info.get('severity', 'unknown')
                description = pattern_info.get('description', 'No description')
                print(f"\n{violation_type}:")
                print(f"  Count: {count}")
                print(f"  Severity: {severity}")
                print(f"  Description: {description}")
            
            print("\n" + "=" * 80)
            print("Severity Breakdown:")
            print("-" * 80)
            severity_count = defaultdict(int)
            for violation_type, count in self.stats['violation_types'].items():
                pattern_info = self.patterns.get(violation_type, {})
                severity = pattern_info.get('severity', 'unknown')
                severity_count[severity] += count
            
            for severity in ['critical', 'high', 'medium', 'low']:
                if severity in severity_count:
                    print(f"{severity.upper()}: {severity_count[severity]} violations")
            
            print("=" * 80)
        else:
            print("\n✅ No naming violations found!")
            print("=" * 80)

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='GL Runtime Platform Naming Violations Scanner')
    parser.add_argument('--path', default='/workspace/machine-native-ops',
                        help='Root path to scan')
    parser.add_argument('--output', help='Output JSON file for detailed report')
    
    args = parser.parse_args()
    
    scanner = NamingViolationScanner(root_path=args.path)
    scanner.scan_repository()
    scanner.print_summary()
    
    # Generate and save detailed report
    report = scanner.generate_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {args.output}")
    else:
        # Default output location
        output_path = scanner.root_path / "logs" / f"naming-violations-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nDetailed report saved to: {output_path}")

if __name__ == "__main__":
    main()