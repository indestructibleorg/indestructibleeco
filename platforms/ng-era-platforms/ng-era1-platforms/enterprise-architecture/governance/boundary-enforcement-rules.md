# GL Directory Boundary Enforcement Rules v1.0.0

## Document Control

| Field | Value |
|-------|-------|
| **Version** | 1.0.0 |
| **Cost** | MANDATORY |
| **Last Updated** | 2026-01-31 |
| **Governance Level** | GL60-80 |
| **Enforcement** | MANDATORY |

## 1. Enforcement Overview

### 1.1 Enforcement Philosophy

**Principle**: Prevent boundary violations through automated enforcement, not just detection.

**Strategy**:
- Prevention over cure
- Automation over manual review
- Clear rules over ambiguous guidelines
- Hard stops over warnings

### 1.2 Enforcement Levels

| Level | Name | Enforcement Method | Severity |
|-------|------|-------------------|----------|
| E0 | Constitutional | Automated blocking | CRITICAL |
| E1 | Regulatory | Automated rejection | HIGH |
| E2 | Operational | Automated validation | MEDIUM |
| E3 | Advisory | Warning messages | LOW |

### 1.3 Enforcement Scope

All boundary rules are enforced at:
- **Development Time**: IDE integration, pre-commit hooks
- **Integration Time**: CI/CD pipeline, automated tests
- **Runtime Time**: Permission checks, access control
- **Audit Time**: Continuous monitoring, compliance verification

## 2. Rule Definitions

### 2.1 Constitutional Rules (E0 - CRITICAL)

#### Rule E0-001: No Circular Dependencies
```
NAME: circular-dependency-forbidden
LEVEL: E0 - CRITICAL
ACTION: BLOCK (reject commit)
DESCRIPTION: Circular dependencies are never permitted
```

**Implementation**:
```python
def check_circular_dependencies(dependency_graph):
    # Build dependency matrix
    graph = build_dependency_matrix(dependency_graph)
    
    # Detect cycles
    if has_cycle(graph):
        return {
            'status': 'VIOLATION',
            'rule': 'E0-001',
            'severity': 'CRITICAL',
            'action': 'BLOCK',
            'message': 'Circular dependency detected',
            'details': list_cycle(graph)
        }
    
    return {'status': 'PASS'}
```

**Examples**:
```
VIOLATION: gl-execution-runtime depends on gl-platform-services,
           gl-platform-services depends on gl-execution-runtime

ALLOWED: gl-execution-runtime depends on gl-platform-services
ALLOWED: gl-platform-services depends on gl-enterprise-architecture
```

#### Rule E0-002: Dependency Matrix Compliance
```
NAME: dependency-matrix-compliance
LEVEL: E0 - CRITICAL
ACTION: BLOCK (reject commit)
DESCRIPTION: All dependencies must comply with the dependency matrix
```

**Implementation**:
```python
def check_dependency_matrix_compliance(layer_from, layer_to):
    matrix = load_dependency_matrix()
    
    if matrix[layer_from][layer_to] == 'FORBIDDEN':
        return {
            'status': 'VIOLATION',
            'rule': 'E0-002',
            'severity': 'CRITICAL',
            'action': 'BLOCK',
            'message': f'{layer_from} cannot depend on {layer_to}',
            'allowed_dependencies': get_allowed_dependencies(layer_from)
        }
    
    return {'status': 'PASS'}
```

**Reference Matrix**:
| From | GL00-09 | GL10-29 | GL20-29 | GL30-49 | GL50-59 | GL60-80 | GL81-83 | GL90-99 |
|------|---------|---------|---------|---------|---------|---------|---------|---------|
| GL00-09 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| GL10-29 | ✓ | - | ✗ | ✗ | ✓ | ✓ | ✓ | ✓ |
| GL20-29 | ✓ | ✓ | - | ✗ | ✓ | ✓ | ✓ | ✓ |
| GL30-49 | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ |
| GL50-59 | ✓ | ✓ | ✓ | ✓ | - | ✓ | ✓ | ✓ |
| GL60-80 | ✓ | ✗ | ✗ | ✗ | ✓ | - | ✗ | ✗ |
| GL81-83 | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | - | ✓ |
| GL90-99 | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | - |

#### Rule E0-003: No Execution in GL00-09
```
NAME: no-execution-in-governance
LEVEL: E0 - CRITICAL
ACTION: BLOCK (reject commit)
DESCRIPTION: GL00-09 cannot contain executable code
```

**Implementation**:
```python
def check_no_execution_in_governance(file_path):
    if not file_path.startswith('gl-enterprise-architecture/'):
        return {'status': 'PASS'}
    
    # Check for executable patterns
    executable_patterns = [
        r'def\s+\w+\s*\(',  # Function definitions
        r'class\s+\w+\s*:',  # Class definitions
        r'if\s+.*:',  # Conditional statements
        r'for\s+.*:',  # Loop statements
        r'while\s+.*:',  # While loops
        r'import\s+',  # Import statements (except for data structures)
    ]
    
    content = read_file(file_path)
    
    for pattern in executable_patterns:
        if re.search(pattern, content):
            return {
                'status': 'VIOLATION',
                'rule': 'E0-003',
                'severity': 'CRITICAL',
                'action': 'BLOCK',
                'message': 'GL00-09 cannot contain executable code',
                'details': f'Found pattern: {pattern}'
            }
    
    return {'status': 'PASS'}
```

**Exception**: Data structure definitions (YAML, JSON, TOML) are allowed.

#### Rule E0-004: No External Dependencies
```
NAME: no-external-dependencies
LEVEL: E0 - CRITICAL
ACTION: BLOCK (reject commit)
DESCRIPTION: Zero external dependency policy enforcement
```

**Implementation**:
```python
def check_no_external_dependencies(file_path):
    external_patterns = [
        r'https?://',  # External URLs
        r'npmjs\.org',  # NPM registry
        r'pypi\.org',  # PyPI registry
        r'github\.com.*action',  # GitHub Actions
        r'hub\.docker\.com',  # Docker Hub
    ]
    
    content = read_file(file_path)
    
    for pattern in external_patterns:
        if re.search(pattern, content):
            return {
                'status': 'VIOLATION',
                'rule': 'E0-004',
                'severity': 'CRITICAL',
                'action': 'BLOCK',
                'message': 'External dependencies are forbidden',
                'details': f'Found external reference: {pattern}'
            }
    
    return {'status': 'PASS'}
```

### 2.2 Regulatory Rules (E1 - HIGH)

#### Rule E1-001: Interface Contract Required
```
NAME: interface-contract-required
LEVEL: E1 - HIGH
ACTION: REJECT (require fix before merge)
DESCRIPTION: All cross-boundary interactions must have defined contracts
```

**Implementation**:
```python
def check_interface_contract_required(layer_from, layer_to):
    # If this is a cross-boundary interaction
    if is_cross_boundary(layer_from, layer_to):
        # Check if contract exists
        contract_path = get_contract_path(layer_from, layer_to)
        
        if not file_exists(contract_path):
            return {
                'status': 'VIOLATION',
                'rule': 'E1-001',
                'severity': 'HIGH',
                'action': 'REJECT',
                'message': f'Interface contract required: {contract_path}',
                'template': get_contract_template(layer_from, layer_to)
            }
    
    return {'status': 'PASS'}
```

**Contract Template**:
```yaml
# Interface Contract Template
apiVersion: gl-runtime.io/v1.0.0
kind: InterfaceContract
metadata:
  name: {from-layer}-{to-layer}-contract
  version: "1.0.0"
spec:
  layers:
    from: {from-layer}
    to: {to-layer}
  
  interfaces:
    - name: operation-name
      method: POST
      path: /api/v1/operation
      request:
        type: object
        properties:
          param1: {type: string}
          param2: {type: integer}
      response:
        type: object
        properties:
          result: {type: string}
      errors:
        - code: ERR001
          message: "Error description"
  
  non_functional:
    performance:
      max_latency: 100ms
      throughput: 1000 req/s
    availability:
      sla: 99.9%
    security:
      authentication: required
      authorization: required
```

#### Rule E1-002: Leaky Abstraction Prevention
```
NAME: leaky-abstraction-prevention
LEVEL: E1 - HIGH
ACTION: REJECT (require fix before merge)
DESCRIPTION: Internal implementation must not be exposed across boundaries
```

**Implementation**:
```python
def check_leaky_abstraction(layer_from, layer_to):
    # Check for internal implementation exposure
    public_api = get_public_api(layer_to)
    exposed_internals = find_exposed_internals(layer_to)
    
    if exposed_internals:
        return {
            'status': 'VIOLATION',
            'rule': 'E1-002',
            'severity': 'HIGH',
            'action': 'REJECT',
            'message': 'Internal implementation exposed across boundary',
            'details': exposed_internals,
            'remediation': 'Create proper interface abstraction'
        }
    
    return {'status': 'PASS'}
```

#### Rule E1-003: No Direct File Access
```
NAME: no-direct-file-access
LEVEL: E1 - HIGH
ACTION: REJECT (require fix before merge)
DESCRIPTION: Cross-boundary file access must use defined APIs
```

**Implementation**:
```python
def check_no_direct_file_access(layer_from, layer_to):
    # Check for direct file system access patterns
    direct_access_patterns = [
        r'open\(.+\)',  # Direct file open
        r'pathlib\.Path\(.+\)',  # Direct path manipulation
        r'shutil\.',  # Direct file operations
    ]
    
    if has_cross_layer_calls(layer_from, layer_to):
        for pattern in direct_access_patterns:
            if pattern_found_in_code(layer_from, pattern):
                return {
                    'status': 'VIOLATION',
                    'rule': 'E1-003',
                    'severity': 'HIGH',
                    'action': 'REJECT',
                    'message': 'Direct file access across boundary forbidden',
                    'remediation': 'Use defined APIs instead'
                }
    
    return {'status': 'PASS'}
```

#### Rule E1-004: Observability Read-Only
```
NAME: observability-read-only
LEVEL: E1 - HIGH
ACTION: REJECT (require fix before merge)
DESCRIPTION: GL50-59 must be read-only
```

**Implementation**:
```python
def check_observability_read_only():
    if not is_observability_layer():
        return {'status': 'PASS'}
    
    # Check for modification patterns
    modification_patterns = [
        r'\.write\(',  # File writes
        r'\.set\(',  # Value setting
        r'\.update\(',  # Updates
        r'\.delete\(',  # Deletions
    ]
    
    for pattern in modification_patterns:
        if pattern_found(pattern):
            return {
                'status': 'VIOLATION',
                'rule': 'E1-004',
                'severity': 'HIGH',
                'action': 'REJECT',
                'message': 'GL50-59 must be read-only',
                'details': f'Found modification pattern: {pattern}'
            }
    
    return {'status': 'PASS'}
```

### 2.3 Operational Rules (E2 - MEDIUM)

#### Rule E2-001: Directory Naming Convention
```
NAME: directory-naming-convention
LEVEL: E2 - MEDIUM
ACTION: VALIDATE (require fix)
DESCRIPTION: Directories must follow naming conventions
```

**Implementation**:
```python
def check_directory_naming_convention(directory_name):
    # Standard naming pattern
    pattern = r'^gl-([a-z0-9-]+)(?:-(platform|service|module))?/$'
    
    if not re.match(pattern, directory_name):
        return {
            'status': 'VIOLATION',
            'rule': 'E2-001',
            'severity': 'MEDIUM',
            'action': 'VALIDATE',
            'message': 'Directory naming convention violation',
            'expected': 'gl-{layer}-{capability}-{type}/',
            'actual': directory_name
        }
    
    return {'status': 'PASS'}
```

**Naming Conventions**:
```
gl-{layer}-{capability}-{type}/

Layers:
- enterprise-architecture
- platform-services
- data-processing
- execution-runtime
- observability
- governance-compliance
- extension-services
- meta-specifications

Types:
- platform
- service
- module

Examples:
- gl-runtime-dag-platform/
- gl-quantum-compute-service/
- gl-authentication-module/
```

#### Rule E2-002: Standard Subdirectory Structure
```
NAME: standard-subdirectory-structure
LEVEL: E2 - MEDIUM
ACTION: VALIDATE (require fix)
DESCRIPTION: Directories must have standard subdirectory structure
```

**Implementation**:
```python
def check_standard_subdirectory_structure(directory_path):
    required_subdirs = ['src/', 'configs/', 'docs/', 'tests/', 'deployments/']
    missing = []
    
    for subdir in required_subdirs:
        if not directory_exists(directory_path + subdir):
            missing.append(subdir)
    
    if missing:
        return {
            'status': 'VIOLATION',
            'rule': 'E2-002',
            'severity': 'MEDIUM',
            'action': 'VALIDATE',
            'message': 'Missing required subdirectories',
            'missing': missing,
            'required': required_subdirs
        }
    
    return {'status': 'PASS'}
```

**Required Subdirectories**:
- `src/` - Source code
- `configs/` - Configuration files
- `docs/` - Documentation
- `tests/` - Tests
- `deployments/` - Deployment configurations

#### Rule E2-003: Documentation Completeness
```
NAME: documentation-completeness
LEVEL: E2 - MEDIUM
ACTION: VALIDATE (require fix)
DESCRIPTION: Each layer must have required documentation
```

**Implementation**:
```python
def check_documentation_completeness(layer_path):
    required_docs = {
        'README.md': 'Layer overview',
        'ARCHITECTURE.md': 'Architecture description',
        'RESPONSIBILITIES.md': 'Responsibility definition',
        'API.md': 'API documentation (if applicable)'
    }
    
    missing = []
    for doc_file, description in required_docs.items():
        if not file_exists(layer_path + doc_file):
            missing.append(f'{doc_file}: {description}')
    
    if missing:
        return {
            'status': 'VIOLATION',
            'rule': 'E2-003',
            'severity': 'MEDIUM',
            'action': 'VALIDATE',
            'message': 'Missing required documentation',
            'missing': missing
        }
    
    return {'status': 'PASS'}
```

### 2.4 Advisory Rules (E3 - LOW)

#### Rule E3-001: Directory Size Recommendation
```
NAME: directory-size-recommendation
LEVEL: E3 - LOW
ACTION: WARNING (advisory only)
DESCRIPTION: Directories should be manageable in size
```

**Implementation**:
```python
def check_directory_size_recommendation(directory_path):
    max_files = 1000
    file_count = count_files(directory_path)
    
    if file_count > max_files:
        return {
            'status': 'WARNING',
            'rule': 'E3-001',
            'severity': 'LOW',
            'action': 'WARNING',
            'message': 'Directory exceeds recommended size',
            'file_count': file_count,
            'recommendation': f'Maximum {max_files} files recommended',
            'suggestion': 'Consider splitting into subdirectories'
        }
    
    return {'status': 'PASS'}
```

#### Rule E3-002: Module Cohesion Check
```
NAME: module-cohesion-check
LEVEL: E3 - LOW
ACTION: WARNING (advisory only)
DESCRIPTION: Modules should have high cohesion
```

**Implementation**:
```python
def check_module_cohesion(module_path):
    # Calculate cohesion metric
    cohesion = calculate_cohesion(module_path)
    
    if cohesion < 0.7:  # 70% threshold
        return {
            'status': 'WARNING',
            'rule': 'E3-002',
            'severity': 'LOW',
            'action': 'WARNING',
            'message': 'Module has low cohesion',
            'cohesion_score': cohesion,
            'recommendation': 'Consider refactoring for better cohesion'
        }
    
    return {'status': 'PASS'}
```

#### Rule E3-003: Circular Import Detection (Early Warning)
```
NAME: circular-import-detection
LEVEL: E3 - LOW
ACTION: WARNING (advisory only)
DESCRIPTION: Warn about potential circular imports
```

**Implementation**:
```python
def check_circular_imports(file_path):
    imports = extract_imports(file_path)
    
    # Build import graph
    graph = build_import_graph(imports)
    
    # Detect potential cycles
    potential_cycles = find_potential_cycles(graph)
    
    if potential_cycles:
        return {
            'status': 'WARNING',
            'rule': 'E3-003',
            'severity': 'LOW',
            'action': 'WARNING',
            'message': 'Potential circular imports detected',
            'potential_cycles': potential_cycles,
            'suggestion': 'Review and restructure imports'
        }
    
    return {'status': 'PASS'}
```

## 3. Enforcement Implementation

### 3.1 Pre-Commit Enforcement

```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running boundary enforcement checks..."

# Run all critical checks
python3 /tools/boundary_checker.py --level E0

if [ $? -ne 0 ]; then
    echo "❌ CRITICAL violation detected. Commit blocked."
    exit 1
fi

# Run all high priority checks
python3 /tools/boundary_checker.py --level E1

if [ $? -ne 0 ]; then
    echo "❌ HIGH priority violation detected. Fix required."
    exit 1
fi

# Run validation checks
python3 /tools/boundary_checker.py --level E2

if [ $? -ne 0 ]; then
    echo "⚠️  Validation issues found. Review warnings."
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "✅ All checks passed. Proceeding with commit."
```

### 3.2 CI/CD Enforcement

```yaml
# .github/workflows/boundary-enforcement.yml (if GitHub Actions were allowed)
name: Boundary Enforcement

on: [push, pull_request]

jobs:
  boundary-check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      
      - name: Run critical checks
        run: |
          python3 /tools/boundary_checker.py --level E0
          if [ $? -ne 0 ]; then
            echo "CRITICAL violation detected"
            exit 1
          fi
      
      - name: Run high-priority checks
        run: |
          python3 /tools/boundary_checker.py --level E1
          if [ $? -ne 0 ]; then
            echo "HIGH priority violation detected"
            exit 1
          fi
      
      - name: Generate report
        run: |
          python3 /tools/boundary_checker.py --report
```

### 3.3 Runtime Enforcement

```python
# Runtime boundary checker
class RuntimeBoundaryChecker:
    def __init__(self):
        self.dependency_matrix = self._load_dependency_matrix()
        self.interface_contracts = self._load_interface_contracts()
    
    def validate_cross_layer_call(self, layer_from, layer_to, operation):
        """Validate a cross-layer call at runtime"""
        
        # Check dependency matrix
        if not self._is_dependency_allowed(layer_from, layer_to):
            raise BoundaryViolationException(
                f"{layer_from} cannot call {layer_to}"
            )
        
        # Check interface contract
        contract = self._get_interface_contract(layer_from, layer_to)
        if not contract:
            raise BoundaryViolationException(
                f"No interface contract for {layer_from} → {layer_to}"
            )
        
        # Validate operation against contract
        if not self._validate_operation(contract, operation):
            raise BoundaryViolationException(
                f"Operation violates interface contract"
            )
        
        return True
    
    def _is_dependency_allowed(self, layer_from, layer_to):
        return self.dependency_matrix[layer_from][layer_to] != 'FORBIDDEN'
```

## 4. Violation Handling

### 4.1 Violation Classification

| Severity | Action | Notification | Escalation |
|----------|--------|--------------|------------|
| CRITICAL | BLOCK | Immediate email to team | Architectural review |
| HIGH | REJECT | Pull request comment | Security review |
| MEDIUM | VALIDATE | Warning comment | Team lead review |
| LOW | WARNING | Log entry only | No escalation |

### 4.2 Violation Response

#### CRITICAL Violations
1. **Immediate Action**: Block operation
2. **Notification**: Email to architectural board
3. **Documentation**: Create violation ticket
4. **Remediation**: Required before proceeding
5. **Escalation**: Architectural review meeting

#### HIGH Violations
1. **Immediate Action**: Reject merge
2. **Notification**: Pull request comment
3. **Documentation**: Comment on PR
4. **Remediation**: Fix before approval
5. **Escalation**: Security review if needed

#### MEDIUM Violations
1. **Immediate Action**: Flag for review
2. **Notification**: Warning comment
3. **Documentation**: Issue created
4. **Remediation**: Schedule fix
5. **Escalation**: Team lead review

#### LOW Violations
1. **Immediate Action**: Log warning
2. **Notification**: Developer notification
3. **Documentation**: Warning in logs
4. **Remediation**: Optional improvement
5. **Escalation**: None

### 4.3 Violation Tracking

```python
class ViolationTracker:
    def __init__(self):
        self.violations = []
    
    def record_violation(self, violation):
        """Record a boundary violation"""
        self.violations.append({
            'timestamp': datetime.utcnow(),
            'rule': violation['rule'],
            'severity': violation['severity'],
            'layer_from': violation.get('layer_from'),
            'layer_to': violation.get('layer_to'),
            'message': violation['message'],
            'action': violation['action'],
            'status': 'OPEN'
        })
        
        # Send notification based on severity
        self._notify(violation)
    
    def generate_report(self):
        """Generate violation report"""
        return {
            'total_violations': len(self.violations),
            'by_severity': self._count_by_severity(),
            'by_rule': self._count_by_rule(),
            'by_layer': self._count_by_layer(),
            'trends': self._analyze_trends()
        }
```

## 5. Compliance Monitoring

### 5.1 Continuous Monitoring

```python
class ComplianceMonitor:
    def __init__(self):
        self.boundary_checker = BoundaryChecker()
        self.violation_tracker = ViolationTracker()
    
    def continuous_monitor(self):
        """Run continuous compliance monitoring"""
        while True:
            # Scan for violations
            violations = self.boundary_checker.scan()
            
            # Track violations
            for violation in violations:
                self.violation_tracker.record_violation(violation)
            
            # Generate reports
            report = self.violation_tracker.generate_report()
            
            # Send alerts for critical violations
            critical_violations = [v for v in violations 
                                   if v['severity'] == 'CRITICAL']
            if critical_violations:
                self.send_alert(critical_violations)
            
            # Sleep for next scan
            time.sleep(3600)  # Scan every hour
```

### 5.2 Dashboard Metrics

```yaml
compliance_dashboard:
  metrics:
    - name: total_violations
      type: counter
      description: Total boundary violations detected
    
    - name: violation_severity_distribution
      type: histogram
      description: Distribution of violations by severity
    
    - name: layer_violation_count
      type: gauge
      description: Violations per layer
    
    - name: compliance_rate
      type: percentage
      description: Overall compliance rate
    
    - name: critical_violation_count
      type: counter
      description: Number of critical violations
    
    - name: open_violations
      type: gauge
      description: Number of open violations
```

## 6. Remediation Guidelines

### 6.1 Common Violation Remediations

#### Circular Dependency
```
Problem: A depends on B, B depends on A
Solution:
1. Identify shared responsibilities
2. Create abstraction layer C
3. Both A and B depend on C
4. A and B no longer depend on each other
```

#### Dependency Matrix Violation
```
Problem: Layer depends on forbidden layer
Solution:
1. Review layer responsibilities
2. Move functionality to correct layer
3. Update dependencies accordingly
4. Verify no other violations introduced
```

#### Leaky Abstraction
```
Problem: Internal implementation exposed
Solution:
1. Identify exposed internals
2. Create proper interface
3. Hide implementation behind interface
4. Update all consumers to use interface
```

#### Missing Contract
```
Problem: Cross-boundary interaction without contract
Solution:
1. Document interface requirements
2. Create interface contract
3. Validate against specification
4. Register contract in governance
```

### 6.2 Remediation Workflow

```
1. DETECT
   - Automated scanning identifies violation
   - Violation recorded in tracker
   - Severity assessed

2. NOTIFY
   - Appropriate notifications sent
   - Developer alerted
   - Escalation if critical

3. ANALYZE
   - Root cause investigation
   - Impact assessment
   - Solution planning

4. REMEDIATE
   - Implement fix
   - Verify no new violations
   - Update documentation

5. VERIFY
   - Re-scan for violations
   - Confirm resolution
   - Close violation ticket

6. LEARN
   - Document lessons learned
   - Update training materials
   - Improve prevention
```

## 7. Tooling and Automation

### 7.1 Boundary Checker Tool

```python
#!/usr/bin/env python3
"""
GL Boundary Checker Tool
Enforces directory boundary rules across the project
"""

import sys
import argparse
from boundary_checker import BoundaryChecker

def main():
    parser = argparse.ArgumentParser(
        description='GL Boundary Checker'
    )
    parser.add_argument(
        '--level',
        choices=['E0', 'E1', 'E2', 'E3'],
        help='Enforcement level to check'
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate compliance report'
    )
    parser.add_argument(
        '--fix',
        action='store_true',
        help='Attempt to auto-fix issues'
    )
    
    args = parser.parse_args()
    
    checker = BoundaryChecker()
    
    if args.level:
        violations = checker.check_level(args.level)
        if violations:
            print(f"❌ {len(violations)} violations found")
            for v in violations:
                print(f"  {v['rule']}: {v['message']}")
            sys.exit(1)
        else:
            print("✅ No violations found")
    
    if args.report:
        report = checker.generate_report()
        print(json.dumps(report, indent=2))
    
    if args.fix:
        checker.auto_fix()

if __name__ == '__main__':
    main()
```

### 7.2 Integration Hooks

#### IDE Integration
```python
# VS Code extension for boundary checking
class GLBoundaryCheckerExtension:
    def on_file_save(self, file_path):
        """Run boundary checks on file save"""
        violations = check_file_boundaries(file_path)
        
        if violations:
            self.show_errors(violations)
        
        return violations
    
    def on_code_completion(self, context):
        """Filter code completion suggestions"""
        suggestions = get_suggestions(context)
        
        # Filter out boundary violations
        filtered = [
            s for s in suggestions
            if not would_cause_violation(s)
        ]
        
        return filtered
```

#### Pre-Commit Hook
```bash
#!/bin/bash
# .git/hooks/pre-commit
python3 /tools/boundary_checker.py --level E0
if [ $? -ne 0 ]; then
    echo "❌ CRITICAL violation. Commit blocked."
    exit 1
fi
```

---

**Document Status**: MANDATORY - These rules must be enforced across the entire project.