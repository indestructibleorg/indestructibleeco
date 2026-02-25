#!/usr/bin/env python3
"""
GL Boundary Checker Tool
Enforces directory boundary rules across the project
"""

# MNGA-002: Import organization needs review
import os
import sys
import re
import json
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum


class EnforcementLevel(Enum):
    E0 = "CRITICAL"
    E1 = "HIGH"
    E2 = "MEDIUM"
    E3 = "LOW"


class Action(Enum):
    BLOCK = "BLOCK"
    REJECT = "REJECT"
    VALIDATE = "VALIDATE"
    WARNING = "WARNING"


@dataclass
class Violation:
    rule: str
    level: EnforcementLevel
    action: Action
    message: str
    file_path: Optional[str] = None
    details: Optional[Dict] = None
    
    def to_dict(self):
        return {
            'rule': self.rule,
            'level': self.level.value,
            'action': self.action.value,
            'message': self.message,
            'file_path': self.file_path,
            'details': self.details
        }


class DependencyMatrix:
    """Dependency matrix defining allowed dependencies between layers"""
    
    LAYERS = [
        'GL00-09',  # gl-enterprise-architecture
        'GL10-29',  # gl-platform-services
        'GL20-29',  # gl-data-processing
        'GL30-49',  # gl-execution-runtime
        'GL50-59',  # gl-observability
        'GL60-80',  # gl-governance-compliance
        'GL81-83',  # gl-extension-services
        'GL90-99',  # gl-meta-specifications
    ]
    
    # Dependency matrix: matrix[from_layer][to_layer]
    # ✓ = ALLOWED, ✗ = FORBIDDEN, - = Self-reference
    MATRIX = {
        'GL00-09': {'GL00-09': '-', 'GL10-29': '✗', 'GL20-29': '✗', 'GL30-49': '✗', 
                   'GL50-59': '✗', 'GL60-80': '✗', 'GL81-83': '✗', 'GL90-99': '✗'},
        'GL10-29': {'GL00-09': '✓', 'GL10-29': '-', 'GL20-29': '✗', 'GL30-49': '✗', 
                   'GL50-59': '✓', 'GL60-80': '✓', 'GL81-83': '✓', 'GL90-99': '✓'},
        'GL20-29': {'GL00-09': '✓', 'GL10-29': '✓', 'GL20-29': '-', 'GL30-49': '✗', 
                   'GL50-59': '✓', 'GL60-80': '✓', 'GL81-83': '✓', 'GL90-99': '✓'},
        'GL30-49': {'GL00-09': '✓', 'GL10-29': '✓', 'GL20-29': '✓', 'GL30-49': '-', 
                   'GL50-59': '✓', 'GL60-80': '✓', 'GL81-83': '✓', 'GL90-99': '✓'},
        'GL50-59': {'GL00-09': '✓', 'GL10-29': '✓', 'GL20-29': '✓', 'GL30-49': '✓', 
                   'GL50-59': '-', 'GL60-80': '✓', 'GL81-83': '✓', 'GL90-99': '✓'},
        'GL60-80': {'GL00-09': '✓', 'GL10-29': '✗', 'GL20-29': '✗', 'GL30-49': '✗', 
                   'GL50-59': '✓', 'GL60-80': '-', 'GL81-83': '✗', 'GL90-99': '✗'},
        'GL81-83': {'GL00-09': '✓', 'GL10-29': '✓', 'GL20-29': '✓', 'GL30-49': '✓', 
                   'GL50-59': '✓', 'GL60-80': '✓', 'GL81-83': '-', 'GL90-99': '✓'},
        'GL90-99': {'GL00-09': '✗', 'GL10-29': '✗', 'GL20-29': '✗', 'GL30-49': '✗', 
                   'GL50-59': '✗', 'GL60-80': '✗', 'GL81-83': '✗', 'GL90-99': '-'},
    }
    
    @classmethod
    def is_allowed(cls, layer_from: str, layer_to: str) -> bool:
        """Check if dependency from layer_from to layer_to is allowed"""
        if layer_from not in cls.MATRIX or layer_to not in cls.MATRIX[layer_from]:
            return False
        return cls.MATRIX[layer_from][layer_to] == '✓'
    
    @classmethod
    def is_forbidden(cls, layer_from: str, layer_to: str) -> bool:
        """Check if dependency from layer_from to layer_to is forbidden"""
        if layer_from not in cls.MATRIX or layer_to not in cls.MATRIX[layer_from]:
            return True
        return cls.MATRIX[layer_from][layer_to] == '✗'
    
    @classmethod
    def get_allowed_dependencies(cls, layer: str) -> List[str]:
        """Get list of layers that 'layer' can depend on"""
        allowed = []
        if layer not in cls.MATRIX:
            return allowed
        for target_layer, status in cls.MATRIX[layer].items():
            if status == '✓':
                allowed.append(target_layer)
        return allowed


class LayerMapper:
    """Map directory paths to GL layers"""
    
    DIRECTORY_TO_LAYER = {
        'gl-enterprise-architecture': 'GL00-09',
        'gl-platform-services': 'GL10-29',
        'gl-data-processing': 'GL20-29',
        'gl-execution-runtime': 'GL30-49',
        'gl-observability': 'GL50-59',
        'gl-governance-compliance': 'GL60-80',
        'gl-extension-services': 'GL81-83',
        'gl-meta-specifications': 'GL90-99',
    }
    
    @classmethod
    def get_layer_from_path(cls, file_path: str) -> Optional[str]:
        """Get GL layer from file path"""
        path_parts = Path(file_path).parts
        for part in path_parts:
            if part in cls.DIRECTORY_TO_LAYER:
                return cls.DIRECTORY_TO_LAYER[part]
        return None
    
    @classmethod
    def is_in_layer(cls, file_path: str, layer: str) -> bool:
        """Check if file is in specified layer"""
        file_layer = cls.get_layer_from_path(file_path)
        return file_layer == layer


class BoundaryChecker:
    """Main boundary checker class"""
    
    def __init__(self, project_root: str = '.'):
        self.project_root = Path(project_root).absolute()
        self.violations: List[Violation] = []
        self.dependency_graph: Dict[str, List[str]] = {}
        
    def check_file(self, file_path: str) -> List[Violation]:
        """Check a single file for boundary violations"""
        violations = []
        
        # Get layer information
        layer = LayerMapper.get_layer_from_path(file_path)
        if not layer:
            return violations  # Skip files not in GL layers
        
        # Check for circular dependencies
        circular_violation = self._check_circular_dependencies(file_path)
        if circular_violation:
            violations.append(circular_violation)
        
        # Check dependency matrix compliance
        dep_violations = self._check_dependency_matrix(file_path)
        violations.extend(dep_violations)
        
        # Check for external dependencies
        external_violation = self._check_external_dependencies(file_path)
        if external_violation:
            violations.append(external_violation)
        
        # Check for execution in governance layer
        execution_violation = self._check_governance_execution(file_path)
        if execution_violation:
            violations.append(execution_violation)
        
        # Check observability read-only
        observability_violation = self._check_observability_readonly(file_path)
        if observability_violation:
            violations.append(observability_violation)
        
        return violations
    
    def check_directory(self, dir_path: str) -> List[Violation]:
        """Check all files in a directory"""
        violations = []
        dir_path = Path(dir_path)
        
        # Only check Python, JavaScript, TypeScript, YAML files
        extensions = ['.py', '.js', '.ts', '.yaml', '.yml']
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                file_violations = self.check_file(str(file_path))
                violations.extend(file_violations)
        
        return violations
    
    def check_level(self, level: EnforcementLevel) -> List[Violation]:
        """Check for violations at specified enforcement level"""
        all_violations = []
        
        # Check all GL layer directories
        for directory in LayerMapper.DIRECTORY_TO_LAYER.keys():
            dir_path = self.project_root / directory
            if dir_path.exists():
                violations = self.check_directory(str(dir_path))
                all_violations.extend(violations)
        
        # Filter by level
        return [v for v in all_violations if v.level == level]
    
    def _check_circular_dependencies(self, file_path: str) -> Optional[Violation]:
        """Check for circular dependencies"""
        layer = LayerMapper.get_layer_from_path(file_path)
        if not layer:
            return None
        
        # Extract import statements
        imports = self._extract_imports(file_path)
        
        # Build local dependency graph
        for imp in imports:
            target_layer = LayerMapper.get_layer_from_path(imp)
            if target_layer and target_layer != layer:
                if file_path not in self.dependency_graph:
                    self.dependency_graph[file_path] = []
                self.dependency_graph[file_path].append(imp)
        
        # Check for cycles
        if self._has_cycle(file_path):
            return Violation(
                rule='E0-001',
                level=EnforcementLevel.E0,
                action=Action.BLOCK,
                message='Circular dependency detected',
                file_path=file_path,
                details={'cycle': self._find_cycle(file_path)}
            )
        
        return None
    
    def _check_dependency_matrix(self, file_path: str) -> List[Violation]:
        """Check compliance with dependency matrix"""
        violations = []
        layer_from = LayerMapper.get_layer_from_path(file_path)
        
        if not layer_from:
            return violations
        
        # Get imports from file
        imports = self._extract_imports(file_path)
        
        for imp in imports:
            layer_to = LayerMapper.get_layer_from_path(imp)
            if layer_to and layer_to != layer_from:
                # Check if dependency is allowed
                if DependencyMatrix.is_forbidden(layer_from, layer_to):
                    violations.append(Violation(
                        rule='E0-002',
                        level=EnforcementLevel.E0,
                        action=Action.BLOCK,
                        message=f'{layer_from} cannot depend on {layer_to}',
                        file_path=file_path,
                        details={
                            'forbidden_dependency': f'{layer_from} → {layer_to}',
                            'import_path': imp,
                            'allowed_dependencies': DependencyMatrix.get_allowed_dependencies(layer_from)
                        }
                    ))
        
        return violations
    
    def _check_external_dependencies(self, file_path: str) -> Optional[Violation]:
        """Check for external dependencies (zero-dependency policy)"""
        external_patterns = [
            r'https?://',  # External URLs
            r'npmjs\.org',  # NPM registry
            r'pypi\.org',  # PyPI registry
            r'github\.com.*action',  # GitHub Actions
            r'hub\.docker\.com',  # Docker Hub
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
        
        for pattern in external_patterns:
            if re.search(pattern, content):
                return Violation(
                    rule='E0-004',
                    level=EnforcementLevel.E0,
                    action=Action.BLOCK,
                    message='External dependencies are forbidden',
                    file_path=file_path,
                    details={
                        'external_reference': pattern,
                        'found_in_content': True
                    }
                )
        
        return None
    
    def _check_governance_execution(self, file_path: str) -> Optional[Violation]:
        """Check for executable code in governance layer"""
        if not LayerMapper.is_in_layer(file_path, 'GL00-09'):
            return None
        
        executable_patterns = [
            r'def\s+\w+\s*\(',  # Function definitions
            r'class\s+\w+\s*:',  # Class definitions
            r'if\s+.*:',  # Conditional statements (in code context)
            r'for\s+.*:',  # Loop statements
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
        
        # Skip YAML/JSON files (data structures are allowed)
        if file_path.endswith(('.yaml', '.yml', '.json')):
            return None
        
        for pattern in executable_patterns:
            if re.search(pattern, content):
                return Violation(
                    rule='E0-003',
                    level=EnforcementLevel.E0,
                    action=Action.BLOCK,
                    message='GL00-09 cannot contain executable code',
                    file_path=file_path,
                    details={
                        'pattern': pattern,
                        'remediation': 'Move executable code to appropriate layer'
                    }
                )
        
        return None
    
    def _check_observability_readonly(self, file_path: str) -> Optional[Violation]:
        """Check if observability layer is read-only"""
        if not LayerMapper.is_in_layer(file_path, 'GL50-59'):
            return None
        
        modification_patterns = [
            r'\.write\(',  # File writes
            r'\.set\(',  # Value setting
            r'\.update\(',  # Updates (in modification context)
            r'\.delete\(',  # Deletions
        ]
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return None
        
        for pattern in modification_patterns:
            # More context-aware checking
            if re.search(pattern, content):
                # Check if it's just a method name vs actual modification
                if re.search(rf'{pattern}\s*#.*modification|writes.*data', content, re.IGNORECASE):
                    return Violation(
                        rule='E1-004',
                        level=EnforcementLevel.E1,
                        action=Action.REJECT,
                        message='GL50-59 must be read-only',
                        file_path=file_path,
                        details={
                            'pattern': pattern,
                            'remediation': 'Use read-only access patterns'
                        }
                    )
        
        return None
    
    def _extract_imports(self, file_path: str) -> List[str]:
        """Extract import statements from file"""
        imports = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return imports
        
        # Python imports
        python_imports = re.findall(r'^import\s+(.+)$|^from\s+(\S+)\s+import', 
                                    content, re.MULTILINE)
        for match in python_imports:
            if isinstance(match, tuple):
                imports.extend([m for m in match if m])
            else:
                imports.append(match)
        
        # JavaScript/TypeScript imports
        js_imports = re.findall(r'import.*from\s+["\'](.+?)["\']', content)
        imports.extend(js_imports)
        
        return imports
    
    def _has_cycle(self, node: str, visited=None, recursion_stack=None) -> bool:
        """Check if dependency graph has cycle starting from node"""
        if visited is None:
            visited = set()
        if recursion_stack is None:
            recursion_stack = set()
        
        visited.add(node)
        recursion_stack.add(node)
        
        neighbors = self.dependency_graph.get(node, [])
        for neighbor in neighbors:
            if neighbor not in visited:
                if self._has_cycle(neighbor, visited, recursion_stack):
                    return True
            elif neighbor in recursion_stack:
                return True
        
        recursion_stack.remove(node)
        return False
    
    def _find_cycle(self, start_node: str) -> List[str]:
        """Find cycle in dependency graph"""
        def dfs(node, path):
            if node in path:
                return path[path.index(node):] + [node]
            if node in visited:
                return None
            
            visited.add(node)
            path.append(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                cycle = dfs(neighbor, path.copy())
                if cycle:
                    return cycle
            
            path.pop()
            return None
        
        visited = set()
        return dfs(start_node, [])
    
    def generate_report(self) -> Dict:
        """Generate compliance report"""
        total_violations = len(self.violations)
        
        # Count by severity
        by_severity = {}
        for v in self.violations:
            by_severity[v.level.value] = by_severity.get(v.level.value, 0) + 1
        
        # Count by rule
        by_rule = {}
        for v in self.violations:
            by_rule[v.rule] = by_rule.get(v.rule, 0) + 1
        
        # Count by layer
        by_layer = {}
        for v in self.violations:
            layer = LayerMapper.get_layer_from_path(v.file_path or '')
            by_layer[layer] = by_layer.get(layer, 0) + 1
        
        # Calculate compliance rate
        total_files = sum(1 for _ in self.project_root.rglob('*.py'))
        if total_files > 0:
            compliance_rate = ((total_files - total_violations) / total_files) * 100
        else:
            compliance_rate = 100.0
        
        return {
            'total_violations': total_violations,
            'by_severity': by_severity,
            'by_rule': by_rule,
            'by_layer': by_layer,
            'compliance_rate': round(compliance_rate, 2),
            'violations': [v.to_dict() for v in self.violations]
        }
    
    def auto_fix(self) -> int:
        """Attempt to auto-fix simple violations"""
        fixed = 0
        
        # Currently, most violations require manual intervention
        # This method can be extended for auto-fixable issues
        
        return fixed


def main():
    parser = argparse.ArgumentParser(
        description='GL Boundary Checker - Enforce directory boundary rules',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check critical violations
  python boundary_checker.py --level E0
  
  # Check all levels
  python boundary_checker.py --check
  
  # Generate compliance report
  python boundary_checker.py --report
  
  # Check specific file
  python boundary_checker.py --file path/to/file.py
  
  # Check specific directory
  python boundary_checker.py --directory gl-execution-runtime
  
  # Generate JSON report
  python boundary_checker.py --report --format json
        """
    )
    
    parser.add_argument(
        '--level',
        choices=['E0', 'E1', 'E2', 'E3'],
        help='Enforcement level to check (E0=CRITICAL, E1=HIGH, E2=MEDIUM, E3=LOW)'
    )
    
    parser.add_argument(
        '--file',
        help='Check specific file'
    )
    
    parser.add_argument(
        '--directory',
        help='Check specific directory'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Run all checks'
    )
    
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate compliance report'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Report format'
    )
    
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to auto-fix issues (where possible)'
    )
    
    parser.add_argument(
        '--project-root',
        default='.',
        help='Project root directory (default: current directory)'
    )
    
    args = parser.parse_args()
    
    # Initialize checker
    checker = BoundaryChecker(project_root=args.project_root)
    
    # Execute checks based on arguments
    violations = []
    
    if args.level:
        level = EnforcementLevel[args.level]
        violations = checker.check_level(level)
        
        if violations:
            print(f"❌ {len(violations)} {level.value} violations found:\n")
            for v in violations:
                print(f"  {v.rule}: {v.message}")
                if v.file_path:
                    print(f"    File: {v.file_path}")
                if v.details:
                    print(f"    Details: {json.dumps(v.details, indent=6)}")
                print()
            sys.exit(1)
        else:
            print(f"✅ No {level.value} violations found")
    
    elif args.file:
        violations = checker.check_file(args.file)
        
        if violations:
            print(f"❌ {len(violations)} violations found in {args.file}:\n")
            for v in violations:
                print(f"  {v.rule} [{v.level.value}]: {v.message}")
                if v.details:
                    print(f"    Details: {json.dumps(v.details, indent=6)}")
                print()
            sys.exit(1)
        else:
            print(f"✅ No violations found in {args.file}")
    
    elif args.directory:
        violations = checker.check_directory(args.directory)
        
        if violations:
            print(f"❌ {len(violations)} violations found in {args.directory}:\n")
            for v in violations:
                print(f"  {v.rule} [{v.level.value}]: {v.message}")
                if v.file_path:
                    print(f"    File: {v.file_path}")
                print()
            sys.exit(1)
        else:
            print(f"✅ No violations found in {args.directory}")
    
    elif args.check:
        # Run all checks
        for level_name in ['E0', 'E1', 'E2', 'E3']:
            level = EnforcementLevel[level_name]
            level_violations = checker.check_level(level)
            violations.extend(level_violations)
        
        if violations:
            print(f"❌ {len(violations)} total violations found:\n")
            
            # Group by level
            for level_name in ['E0', 'E1', 'E2', 'E3']:
                level = EnforcementLevel[level_name]
                level_violations = [v for v in violations if v.level == level]
                if level_violations:
                    print(f"{level.value} violations ({len(level_violations)}):")
                    for v in level_violations:
                        print(f"  {v.rule}: {v.message}")
                    print()
            sys.exit(1)
        else:
            print("✅ No violations found")
    
    elif args.report:
        # Generate report
        report = checker.generate_report()
        
        if args.format == 'json':
            print(json.dumps(report, indent=2))
        else:
            print("=== GL Boundary Compliance Report ===\n")
            print(f"Total violations: {report['total_violations']}")
            print(f"Compliance rate: {report['compliance_rate']}%")
            print("\nBy severity:")
            for severity, count in report['by_severity'].items():
                print(f"  {severity}: {count}")
            print("\nBy rule:")
            for rule, count in report['by_rule'].items():
                print(f"  {rule}: {count}")
            print("\nBy layer:")
            for layer, count in report['by_layer'].items():
                print(f"  {layer}: {count}")
    
    elif args.fix:
        fixed = checker.auto_fix()
        print(f"Auto-fixed {fixed} violations")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()