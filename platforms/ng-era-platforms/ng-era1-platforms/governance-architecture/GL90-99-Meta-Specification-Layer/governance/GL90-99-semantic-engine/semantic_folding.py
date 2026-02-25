# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Folding Engine
Transforms YAML semantic specifications into computable semantic nodes
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import yaml
from typing import Dict, Any, List, Optional
import numpy as np
from dataclasses import dataclass

from .semantic_models import (
    SemanticNode, SemanticNodeType, SemanticEdge, SemanticGraph, 
    SemanticIndex
)


class SemanticFoldingEngine:
    """
    Engine for folding YAML semantic specifications into semantic nodes
    Implements Phase 2: Semantic Folding (語意折疊)
    """
    
    def __init__(self, embedding_dim: int = 128):
        """
        Initialize the semantic folding engine
        
        Args:
            embedding_dim: Dimension for semantic vectors
        """
        self.embedding_dim = embedding_dim
        self.feature_mapping: Dict[str, int] = {}
        self.feature_counter = 0
    
    def _map_feature_to_index(self, feature: str) -> int:
        """Map semantic feature to numerical index"""
        if feature not in self.feature_mapping:
            self.feature_mapping[feature] = self.feature_counter
            self.feature_counter += 1
        return self.feature_mapping[feature]
    
    def _create_semantic_vector(self, features: List[str]) -> np.ndarray:
        """
        Create semantic vector from features using one-hot encoding
        This implements semantic compression (bit vectors)
        """
        vector = np.zeros(self.embedding_dim, dtype=np.float32)
        for feature in features:
            idx = self._map_feature_to_index(feature)
            if idx < self.embedding_dim:
                vector[idx] = 1.0
        return vector
    
    def fold_domain(self, domain_spec: Dict[str, Any]) -> SemanticNode:
        """
        Fold a domain specification into a semantic node
        
        Args:
            domain_spec: Domain specification from YAML
            
        Returns:
            SemanticNode representing the domain
        """
        domain_id = domain_spec['domain_id']
        abbr = domain_spec.get('abbr', domain_id[:3])
        description = domain_spec.get('description', '')
        semantics = domain_spec.get('semantics', [])
        
        # Create semantic node
        node = SemanticNode(
            id=f"domain.{domain_id}",
            type=SemanticNodeType.DOMAIN,
            features=semantics,
            metadata={
                'abbr': abbr,
                'description': description,
                'domain_id': domain_id
            }
        )
        
        # Generate semantic vector
        node.vector = self._create_semantic_vector(semantics)
        
        return node
    
    def fold_capability(self, capability_spec: Dict[str, Any]) -> SemanticNode:
        """
        Fold a capability specification into a semantic node
        
        Args:
            capability_spec: Capability specification from YAML
            
        Returns:
            SemanticNode representing the capability
        """
        capability_id = capability_spec['capability_id']
        domain = capability_spec.get('domain')
        abbr = capability_spec.get('abbr', capability_id[:3])
        description = capability_spec.get('description', '')
        semantics = capability_spec.get('semantics', [])
        
        # Create semantic node
        node = SemanticNode(
            id=f"capability.{capability_id}",
            type=SemanticNodeType.CAPABILITY,
            features=semantics,
            relations=[{
                'relation': 'belongs-to',
                'domain': f"domain.{domain}" if domain else None
            }] if domain else [],
            metadata={
                'abbr': abbr,
                'description': description,
                'capability_id': capability_id,
                'domain': domain
            }
        )
        
        # Generate semantic vector
        node.vector = self._create_semantic_vector(semantics + [domain] if domain else semantics)
        
        return node
    
    def fold_resource(self, resource_spec: Dict[str, Any]) -> SemanticNode:
        """
        Fold a resource specification into a semantic node
        
        Args:
            resource_spec: Resource specification from YAML
            
        Returns:
            SemanticNode representing the resource
        """
        resource_id = resource_spec['resource_id']
        description = resource_spec.get('description', '')
        semantics = resource_spec.get('semantics', [])
        
        # Create semantic node
        node = SemanticNode(
            id=f"resource.{resource_id}",
            type=SemanticNodeType.RESOURCE,
            features=semantics,
            metadata={
                'description': description,
                'resource_id': resource_id
            }
        )
        
        # Generate semantic vector
        node.vector = self._create_semantic_vector(semantics)
        
        return node
    
    def fold_label(self, label_spec: Dict[str, Any]) -> SemanticNode:
        """
        Fold a label specification into a semantic node
        
        Args:
            label_spec: Label specification from YAML
            
        Returns:
            SemanticNode representing the label
        """
        label_id = label_spec['label_id']
        description = label_spec.get('description', '')
        semantics = label_spec.get('semantics', [])
        
        # Create semantic node
        node = SemanticNode(
            id=f"label.{label_id}",
            type=SemanticNodeType.LABEL,
            features=semantics,
            metadata={
                'description': description,
                'label_id': label_id
            }
        )
        
        # Generate semantic vector
        node.vector = self._create_semantic_vector(semantics)
        
        return node
    
    def fold_specification(self, spec_yaml: str) -> SemanticGraph:
        """
        Fold a complete YAML specification into a semantic graph
        
        Args:
            spec_yaml: YAML string containing the semantic specification
            
        Returns:
            SemanticGraph containing all folded semantic nodes
        """
        # Parse YAML
        spec_data = yaml.safe_load(spec_yaml)
        
        # Create semantic graph
        graph = SemanticGraph()
        
        # Get semantic taxonomy from spec
        taxonomy = spec_data.get('spec', {}).get('semantic-taxonomy', {})
        
        # Fold domains
        domains = taxonomy.get('domains', [])
        domain_nodes = {}
        for domain_spec in domains:
            node = self.fold_domain(domain_spec)
            graph.add_node(node)
            domain_nodes[domain_spec['domain_id']] = node
        
        # Fold capabilities and create domain-capability edges
        capabilities = taxonomy.get('capabilities', [])
        capability_nodes = {}
        for capability_spec in capabilities:
            node = self.fold_capability(capability_spec)
            graph.add_node(node)
            capability_nodes[capability_spec['capability_id']] = node
            
            # Create edge to domain
            domain_id = capability_spec.get('domain')
            if domain_id and f"domain.{domain_id}" in graph.nodes:
                edge = SemanticEdge(
                    source_id=f"domain.{domain_id}",
                    target_id=node.id,
                    relation_type="belongs-to",
                    properties={'domain': domain_id, 'capability': capability_spec['capability_id']}
                )
                graph.add_edge(edge)
        
        # Fold resources
        resources = taxonomy.get('resources', [])
        for resource_spec in resources:
            node = self.fold_resource(resource_spec)
            graph.add_node(node)
        
        # Fold labels
        labels = taxonomy.get('labels', [])
        for label_spec in labels:
            node = self.fold_label(label_spec)
            graph.add_node(node)
        
        return graph
    
    def compute_semantic_overlap(self, node_a: SemanticNode, node_b: SemanticNode) -> float:
        """
        Compute semantic overlap between two nodes
        Uses bitwise AND on compressed vectors
        """
        if node_a.vector is None or node_b.vector is None:
            return 0.0
        
        # Bitwise AND for overlap detection
        overlap = np.bitwise_and(
            node_a.vector.astype(np.int32),
            node_b.vector.astype(np.int32)
        )
        
        # Count overlapping features
        overlap_count = np.sum(overlap)
        min_count = min(np.sum(node_a.vector), np.sum(node_b.vector))
        
        return overlap_count / min_count if min_count > 0 else 0.0
    
    def detect_semantic_conflict(self, node_a: SemanticNode, node_b: SemanticNode) -> bool:
        """
        Detect semantic conflict between two nodes
        Uses bitwise operations on compressed vectors
        """
        if node_a.type == node_b.type:
            # Same type nodes should not have identical features
            if node_a.vector is not None and node_b.vector is not None:
                return np.array_equal(node_a.vector, node_b.vector)
        return False