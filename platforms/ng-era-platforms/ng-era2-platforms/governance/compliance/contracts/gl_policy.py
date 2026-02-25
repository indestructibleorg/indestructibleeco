# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Policy Implementation

This module provides the GLPolicy class for defining and evaluating
GL governance policies with conditions, actions, and priority support.
"""

from typing import Dict, Any, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass, field


class PolicySeverity(Enum):
    """Policy severity levels"""
    CRITICAL = 100
    HIGH = 80
    MEDIUM = 60
    LOW = 40
    INFO = 20


@dataclass
class PolicyCondition:
    """Policy condition"""
    field: str
    operator: str
    value: Any
    description: str = ""


@dataclass
class PolicyAction:
    """Policy action"""
    type: str
    severity: str
    message: str
    parameters: Dict[str, Any] = field(default_factory=dict)


class GLPolicy:
    """
    GL Policy - Governance policy definition and evaluation
    
    Attributes:
        name: Policy name (format: gl.policy.{domain}.{policy_name})
        priority: Policy priority (higher = more important)
        description: Policy description
        conditions: List of policy conditions
        actions: List of policy actions
        enabled: Whether the policy is enabled
    """
    
    OPERATORS = {
        'equals': lambda a, b: a == b,
        'not_equals': lambda a, b: a != b,
        'greater_than': lambda a, b: a > b,
        'less_than': lambda a, b: a < b,
        'greater_than_or_equal': lambda a, b: a >= b,
        'less_than_or_equal': lambda a, b: a <= b,
        'starts_with': lambda a, b: str(a).startswith(str(b)),
        'ends_with': lambda a, b: str(a).endswith(str(b)),
        'contains': lambda a, b: str(b) in str(a),
        'not_contains': lambda a, b: str(b) not in str(a),
        'matches_regex': lambda a, b: __import__('re').search(b, str(a)) is not None,
        'in_list': lambda a, b: a in b,
        'not_in_list': lambda a, b: a not in b
    }
    
    def __init__(
        self,
        name: str,
        priority: int = 80,
        description: str = "",
        enabled: bool = True
    ):
        self.name = name
        self.priority = priority
        self.description = description
        self.conditions: List[PolicyCondition] = []
        self.actions: List[PolicyAction] = []
        self.enabled = enabled
    
    def add_condition(
        self,
        field: str,
        operator: str,
        value: Any,
        description: str = ""
    ) -> 'GLPolicy':
        """Add policy condition"""
        if operator not in self.OPERATORS:
            raise ValueError(f"Invalid operator: {operator}")
        
        self.conditions.append(PolicyCondition(
            field=field,
            operator=operator,
            value=value,
            description=description
        ))
        return self
    
    def add_action(
        self,
        type: str,
        severity: str,
        message: str,
        **parameters
    ) -> 'GLPolicy':
        """Add policy action"""
        self.actions.append(PolicyAction(
            type=type,
            severity=severity,
            message=message,
            parameters=parameters
        ))
        return self
    
    def evaluate(self, data: Dict[str, Any]) -> bool:
        """Evaluate policy against data"""
        if not self.enabled:
            return True
        
        for condition in self.conditions:
            field_value = self._get_field_value(data, condition.field)
            
            if field_value is None:
                # Field not found, condition fails
                return False
            
            operator_func = self.OPERATORS[condition.operator]
            
            try:
                result = operator_func(field_value, condition.value)
                if not result:
                    return False
            except Exception as e:
                # Evaluation error, condition fails
                return False
        
        return True
    
    def _get_field_value(self, data: Dict[str, Any], field: str) -> Any:
        """Get field value from nested dictionary"""
        keys = field.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def get_violations(self, data: Dict[str, Any]) -> List[str]:
        """Get policy violations"""
        violations = []
        
        for condition in self.conditions:
            field_value = self._get_field_value(data, condition.field)
            
            if field_value is None:
                violations.append(
                    f"Field '{condition.field}' not found in data"
                )
                continue
            
            operator_func = self.OPERATORS[condition.operator]
            
            try:
                result = operator_func(field_value, condition.value)
                if not result:
                    violations.append(
                        f"Condition failed: {condition.field} {condition.operator} {condition.value}"
                    )
            except Exception as e:
                violations.append(
                    f"Evaluation error for {condition.field}: {str(e)}"
                )
        
        return violations
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'priority': self.priority,
            'description': self.description,
            'enabled': self.enabled,
            'conditions': [
                {
                    'field': c.field,
                    'operator': c.operator,
                    'value': c.value,
                    'description': c.description
                }
                for c in self.conditions
            ],
            'actions': [
                {
                    'type': a.type,
                    'severity': a.severity,
                    'message': a.message,
                    'parameters': a.parameters
                }
                for a in self.actions
            ]
        }
    
    def to_yaml(self) -> str:
        """Convert to YAML"""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Convert to JSON"""
        import json
        return json.dumps(self.to_dict(), indent=2)


def create_naming_prefix_policy() -> GLPolicy:
    """Create naming prefix required policy"""
    policy = GLPolicy(
        name='gl.policy.naming.prefix_required',
        priority=100,
        description='All entities must have gl. prefix',
        enabled=True
    )
    
    policy.add_condition(
        field='name',
        operator='starts_with',
        value='gl.',
        description='Entity name must start with gl.'
    )
    
    policy.add_action(
        type='validate',
        severity='critical',
        message='All entities must have gl. prefix'
    )
    
    return policy


def create_circular_dependency_policy() -> GLPolicy:
    """Create no circular dependency policy"""
    policy = GLPolicy(
        name='gl.policy.governance.no_circular_deps',
        priority=100,
        description='No circular dependencies allowed',
        enabled=True
    )
    
    # This would require custom evaluation logic
    # For demonstration, we add a simple condition
    policy.add_condition(
        field='has_circular_deps',
        operator='equals',
        value=False,
        description='No circular dependencies allowed'
    )
    
    policy.add_action(
        type='block_commit',
        severity='critical',
        message='Circular dependencies detected, commit blocked'
    )
    
    return policy


def create_api_auth_policy() -> GLPolicy:
    """Create API authentication required policy"""
    policy = GLPolicy(
        name='gl.policy.security.api_authentication',
        priority=100,
        description='All API endpoints must require authentication',
        enabled=True
    )
    
    policy.add_condition(
        field='authentication_required',
        operator='equals',
        value=True,
        description='API endpoints must require authentication'
    )
    
    policy.add_action(
        type='validate',
        severity='critical',
        message='API authentication is required'
    )
    
    policy.add_action(
        type='create_issue',
        severity='high',
        message='Missing API authentication',
        parameters={
            'repository': 'MachineNativeOps/machine-native-ops',
            'labels': ['security', 'authentication']
        }
    )
    
    return policy


# Example usage
if __name__ == '__main__':
    # Create policies
    naming_policy = create_naming_prefix_policy()
    circular_dep_policy = create_circular_dependency_policy()
    auth_policy = create_api_auth_policy()
    
    # Test data
    test_data_valid = {'name': 'gl.semantic.entity.user'}
    test_data_invalid = {'name': 'user'}
    
    # Evaluate policies
    print("=== Naming Prefix Policy ===")
    print(f"Valid data: {naming_policy.evaluate(test_data_valid)}")
    print(f"Invalid data: {naming_policy.evaluate(test_data_invalid)}")
    
    if not naming_policy.evaluate(test_data_invalid):
        violations = naming_policy.get_violations(test_data_invalid)
        print(f"Violations: {violations}")
    
    print("\n=== Policy Dictionary ===")
    print(naming_policy.to_dict())
    
    print("\n=== Policy YAML ===")
    print(naming_policy.to_yaml()[:300] + "...")