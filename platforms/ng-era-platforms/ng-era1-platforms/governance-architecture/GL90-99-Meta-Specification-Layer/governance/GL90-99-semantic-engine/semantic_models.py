# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Core Models
Defines the fundamental data structures for the Semantic Core Engine
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
from enum import Enum
import numpy as np
from datetime import datetime


class SemanticNodeType(Enum):
    """Types of semantic nodes"""
    DOMAIN = "domain"
    CAPABILITY = "capability"
    RESOURCE = "resource"
    LABEL = "label"


@dataclass
class SemanticNode:
    """
    Core semantic node representation
    Represents any semantic entity (domain, capability, resource, label)
    """
    id: str
    type: SemanticNodeType
    features: List[str] = field(default_factory=list)
    relations: List[Dict[str, str]] = field(default_factory=list)
    vector: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize timestamp and ensure proper data types"""
        if 'created_at' not in self.metadata:
            self.metadata['created_at'] = datetime.utcnow().isoformat()
        if not isinstance(self.features, list):
            self.features = list(self.features)
        if not isinstance(self.relations, list):
            self.relations = list(self.relations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'type': self.type.value,
            'features': self.features,
            'relations': self.relations,
            'vector': self.vector.tolist() if self.vector is not None else None,
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SemanticNode':
        """Create from dictionary representation"""
        vector = np.array(data['vector']) if data.get('vector') else None
        return cls(
            id=data['id'],
            type=SemanticNodeType(data['type']),
            features=data.get('features', []),
            relations=data.get('relations', []),
            vector=vector,
            metadata=data.get('metadata', {})
        )
    
    def semantic_similarity(self, other: 'SemanticNode') -> float:
        """Calculate semantic similarity using cosine similarity"""
        if self.vector is None or other.vector is None:
            return 0.0
        dot_product = np.dot(self.vector, other.vector)
        norm_a = np.linalg.norm(self.vector)
        norm_b = np.linalg.norm(other.vector)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot_product / (norm_a * norm_b)
    
    def feature_overlap(self, other: 'SemanticNode') -> float:
        """Calculate feature overlap (Jaccard similarity)"""
        set_a = set(self.features)
        set_b = set(other.features)
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0


@dataclass
class SemanticEdge:
    """
    Represents a semantic relationship between two nodes
    """
    source_id: str
    target_id: str
    relation_type: str
    properties: Dict[str, Any] = field(default_factory=dict)
    weight: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'relation_type': self.relation_type,
            'properties': self.properties,
            'weight': self.weight
        }


@dataclass
class SemanticIndex:
    """
    Multi-dimensional index for fast semantic queries
    """
    by_id: Dict[str, SemanticNode] = field(default_factory=dict)
    by_feature: Dict[str, List[str]] = field(default_factory=dict)
    by_domain: Dict[str, List[str]] = field(default_factory=dict)
    by_capability: Dict[str, List[str]] = field(default_factory=dict)
    by_label: Dict[str, List[str]] = field(default_factory=dict)
    by_type: Dict[SemanticNodeType, List[str]] = field(default_factory=dict)
    
    def add_node(self, node: SemanticNode):
        """Add a node to all indices"""
        # ID index
        self.by_id[node.id] = node
        
        # Feature index
        for feature in node.features:
            if feature not in self.by_feature:
                self.by_feature[feature] = []
            if node.id not in self.by_feature[feature]:
                self.by_feature[feature].append(node.id)
        
        # Type index
        if node.type not in self.by_type:
            self.by_type[node.type] = []
        if node.id not in self.by_type[node.type]:
            self.by_type[node.type].append(node.id)
        
        # Domain/Capability/Label indices
        for rel in node.relations:
            if rel.get('relation') == 'belongs-to' and 'domain' in rel:
                domain_id = rel['domain']
                if domain_id not in self.by_domain:
                    self.by_domain[domain_id] = []
                if node.id not in self.by_domain[domain_id]:
                    self.by_domain[domain_id].append(node.id)
            
            if rel.get('relation') == 'implements' and 'capability' in rel:
                capability_id = rel['capability']
                if capability_id not in self.by_capability:
                    self.by_capability[capability_id] = []
                if node.id not in self.by_capability[capability_id]:
                    self.by_capability[capability_id].append(node.id)
            
            if rel.get('relation') == 'labeled-with' and 'label' in rel:
                label_id = rel['label']
                if label_id not in self.by_label:
                    self.by_label[label_id] = []
                if node.id not in self.by_label[label_id]:
                    self.by_label[label_id].append(node.id)
    
    def get_by_feature(self, feature: str) -> List[SemanticNode]:
        """Get all nodes with a specific feature"""
        node_ids = self.by_feature.get(feature, [])
        return [self.by_id[nid] for nid in node_ids if nid in self.by_id]
    
    def get_by_domain(self, domain_id: str) -> List[SemanticNode]:
        """Get all nodes belonging to a domain"""
        node_ids = self.by_domain.get(domain_id, [])
        return [self.by_id[nid] for nid in node_ids if nid in self.by_id]
    
    def get_by_capability(self, capability_id: str) -> List[SemanticNode]:
        """Get all nodes implementing a capability"""
        node_ids = self.by_capability.get(capability_id, [])
        return [self.by_id[nid] for nid in node_ids if nid in self.by_id]
    
    def get_by_type(self, node_type: SemanticNodeType) -> List[SemanticNode]:
        """Get all nodes of a specific type"""
        node_ids = self.by_type.get(node_type, [])
        return [self.by_id[nid] for nid in node_ids if nid in self.by_id]


@dataclass
class SemanticGraph:
    """
    Semantic graph structure holding nodes and edges
    """
    nodes: Dict[str, SemanticNode] = field(default_factory=dict)
    edges: List[SemanticEdge] = field(default_factory=list)
    index: SemanticIndex = field(default_factory=SemanticIndex)
    
    def add_node(self, node: SemanticNode):
        """Add a node to the graph"""
        self.nodes[node.id] = node
        self.index.add_node(node)
    
    def add_edge(self, edge: SemanticEdge):
        """Add an edge to the graph"""
        self.edges.append(edge)
        # Update node relations
        if edge.source_id in self.nodes:
            self.nodes[edge.source_id].relations.append({
                'relation': edge.relation_type,
                'target': edge.target_id,
                **edge.properties
            })
    
    def get_node(self, node_id: str) -> Optional[SemanticNode]:
        """Get a node by ID"""
        return self.nodes.get(node_id)
    
    def get_related_nodes(self, node_id: str, relation_type: Optional[str] = None) -> List[SemanticNode]:
        """Get nodes related to a given node"""
        related = []
        node = self.nodes.get(node_id)
        if not node:
            return related
        
        for rel in node.relations:
            if relation_type is None or rel.get('relation') == relation_type:
                target_id = rel.get('target')
                if target_id in self.nodes:
                    related.append(self.nodes[target_id])
        return related
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[List[str]]:
        """Find shortest path between two nodes using BFS"""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None
        
        from collections import deque
        queue = deque([(source_id, [source_id])])
        visited = {source_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == target_id:
                return path
            
            node = self.nodes.get(current_id)
            if node:
                for rel in node.relations:
                    next_id = rel.get('target')
                    if next_id and next_id not in visited:
                        visited.add(next_id)
                        queue.append((next_id, path + [next_id]))
        
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entire graph to dictionary"""
        return {
            'nodes': {nid: node.to_dict() for nid, node in self.nodes.items()},
            'edges': [edge.to_dict() for edge in self.edges],
            'index': {
                'by_id': {nid: node.id for nid, node in self.index.by_id.items()},
                'by_feature': self.index.by_feature,
                'by_domain': self.index.by_domain,
                'by_capability': self.index.by_capability,
                'by_label': self.index.by_label
            }
        }