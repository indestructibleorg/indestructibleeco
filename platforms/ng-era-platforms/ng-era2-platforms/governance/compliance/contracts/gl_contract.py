# @ECO-layer: GL60-80
# @ECO-governed
"""
GL Contract Implementation

This module provides the GLContract class for managing GL contracts
with support for validation, serialization, and metadata management.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field


class GLContractException(Exception):
    """GL Contract Exception"""
    
    def __init__(self, code: str, message: str, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.details = details or {}
        self.category = code.split('-')[1] if '-' in code else 'UNKNOWN'
        self.severity = self._extract_severity()
        super().__init__(self.message)
    
    def _extract_severity(self) -> str:
        """Extract severity from error code"""
        severity_map = {
            '001': 'CRITICAL',
            '002': 'HIGH',
            '003': 'MEDIUM',
            '004': 'LOW'
        }
        number = self.code.split('-')[-1]
        return severity_map.get(number, 'MEDIUM')
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'code': self.code,
            'category': self.category,
            'severity': self.severity,
            'message': self.message,
            'details': self.details
        }
    
    def __str__(self) -> str:
        return f"[{self.code}] {self.message}"


@dataclass
class GLContractMetadata:
    """GL Contract Metadata"""
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat() + 'Z')
    author: str = "GL Governance Team"
    license: str = "MIT"
    tags: List[str] = field(default_factory=list)
    references: List[Dict[str, str]] = field(default_factory=list)


class GLContract:
    """
    GL Contract - Base class for all GL contracts
    
    Attributes:
        id: Contract unique identifier (format: gl.contract.{name})
        version: Contract version (format: v{major}.{minor}.{patch})
        contract_type: Contract type (core, platform, validation, governance, etc.)
        status: Contract status (active, deprecated, archived)
        spec: Contract specification
        metadata: Contract metadata
        dependencies: List of contract dependencies
        validation_rules: List of validation rules
        governance: List of governance frameworks
    """
    
    REQUIRED_FIELDS = ['id', 'version', 'type', 'status']
    FIELD_TYPES = {
        'id': str,
        'version': str,
        'type': str,
        'status': str,
        'spec': dict,
        'metadata': dict
    }
    
    CONTRACT_CATEGORIES = [
        'core',      # Core contracts (naming ontology, governance layers)
        'platform',  # Platform contracts (platform definition, index)
        'validation',  # Validation contracts (validation rules, validators)
        'governance',  # Governance contracts (governance layers, placement rules)
        'extension',  # Extension contracts (extension points)
        'generator',  # Generator contracts (generator specs)
        'reasoning'   # Reasoning contracts (reasoning rules)
    ]
    
    def __init__(
        self,
        contract_id: str,
        version: str,
        contract_type: str,
        status: str = 'active',
        spec: Dict[str, Any] = None,
        metadata: GLContractMetadata = None
    ):
        self.id = contract_id
        self.version = version
        self.type = contract_type
        self.status = status
        self.spec = spec or {}
        self.metadata = metadata or GLContractMetadata()
        self.dependencies: List[str] = []
        self.validation_rules: List[str] = []
        self.governance: List[str] = []
    
    def validate_id(self) -> bool:
        """Validate contract ID format"""
        return self.id.startswith('gl.contract.')
    
    def validate_version(self) -> bool:
        """Validate contract version format"""
        import re
        return bool(re.match(r'^v\d+\.\d+\.\d+$', self.version))
    
    def validate_category(self) -> bool:
        """Validate contract category"""
        return self.type in self.CONTRACT_CATEGORIES
    
    def add_dependency(self, contract_id: str):
        """Add contract dependency"""
        if contract_id not in self.dependencies:
            self.dependencies.append(contract_id)
    
    def add_validation_rule(self, rule_id: str):
        """Add validation rule"""
        if rule_id not in self.validation_rules:
            self.validation_rules.append(rule_id)
    
    def add_governance(self, governance_id: str):
        """Add governance framework"""
        if governance_id not in self.governance:
            self.governance.append(governance_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'version': self.version,
            'type': self.type,
            'status': self.status,
            'spec': self.spec,
            'metadata': {
                'created_at': self.metadata.created_at,
                'updated_at': self.metadata.updated_at,
                'author': self.metadata.author,
                'license': self.metadata.license,
                'tags': self.metadata.tags,
                'references': self.metadata.references
            },
            'dependencies': self.dependencies,
            'validation_rules': self.validation_rules,
            'governance': self.governance
        }
    
    def to_yaml(self) -> str:
        """Convert to YAML"""
        import yaml
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)
    
    def to_json(self) -> str:
        """Convert to JSON"""
        import json
        return json.dumps(self.to_dict(), indent=2)
    
    def save_yaml(self, filepath: str):
        """Save contract to YAML file"""
        with open(filepath, 'w') as f:
            f.write(self.to_yaml())
    
    def save_json(self, filepath: str):
        """Save contract to JSON file"""
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'GLContract':
        """Create contract from dictionary"""
        contract = cls(
            contract_id=data['id'],
            version=data['version'],
            contract_type=data['type'],
            status=data.get('status', 'active')
        )
        
        contract.spec = data.get('spec', {})
        contract.dependencies = data.get('dependencies', [])
        contract.validation_rules = data.get('validation_rules', [])
        contract.governance = data.get('governance', [])
        
        if 'metadata' in data:
            meta = data['metadata']
            contract.metadata = GLContractMetadata(
                created_at=meta.get('created_at'),
                updated_at=meta.get('updated_at'),
                author=meta.get('author'),
                license=meta.get('license', 'MIT'),
                tags=meta.get('tags', []),
                references=meta.get('references', [])
            )
        
        return contract
    
    @classmethod
    def from_yaml(cls, filepath: str) -> 'GLContract':
        """Load contract from YAML file"""
        import yaml
        with open(filepath, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)
    
    @classmethod
    def from_json(cls, filepath: str) -> 'GLContract':
        """Load contract from JSON file"""
        import json
        with open(filepath, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)


def create_naming_ontology_contract() -> GLContract:
    """Create naming ontology contract"""
    contract = GLContract(
        contract_id='gl.contract.naming_ontology',
        version='1.0.0',
        contract_type='core',
        status='active'
    )
    
    contract.spec = {
        'layers': [
            'semantic', 'contract', 'platform', 'format',
            'language', 'deployment', 'supply-chain', 'user-facing',
            'metadata', 'interface', 'dependency', 'versioning',
            'testing', 'build', 'ci-cd', 'documentation',
            'permission', 'observability', 'security', 'packaging',
            'indexing', 'extensibility', 'validation', 'governance'
        ],
        'rules': {
            'prefix_required': True,
            'format_validation': True
        },
        'metadata': {
            'total_layers': 24,
            'total_entities': 100
        }
    }
    
    contract.metadata.tags = ['naming', 'ontology', 'governance']
    contract.metadata.references = [
        {
            'type': 'documentation',
            'url': 'https://docs.gl.com/naming'
        }
    ]
    
    return contract


# Example usage
if __name__ == '__main__':
    # Create a contract
    contract = create_naming_ontology_contract()
    
    # Validate contract
    print(f"Contract ID: {contract.id}")
    print(f"Valid ID: {contract.validate_id()}")
    print(f"Valid Version: {contract.validate_version()}")
    print(f"Valid Category: {contract.validate_category()}")
    
    # Add dependencies
    contract.add_dependency('gl.contract.platform_definition')
    contract.add_dependency('gl.contract.validation_rules')
    
    # Add validation rules
    contract.add_validation_rule('ECO-NO-001')
    contract.add_validation_rule('ECO-NO-002')
    
    # Add governance
    contract.add_governance('gl-enterprise-architecture')
    contract.add_governance('gl-boundary-enforcement')
    
    # Convert to different formats
    print("\n--- YAML Output ---")
    print(contract.to_yaml()[:200] + "...")
    
    print("\n--- JSON Output ---")
    print(contract.to_json()[:200] + "...")
    
    # Save to file
    contract.save_yaml('/tmp/naming_ontology_contract.yaml')
    print("\n✅ Contract saved to YAML file")