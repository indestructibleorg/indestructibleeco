# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Parameterization Engine
Implements queryable, referencable, composable semantic API
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass

from .semantic_models import (
    SemanticNode, SemanticNodeType, SemanticGraph, SemanticIndex
)
from .semantic_folding import SemanticFoldingEngine


class SemanticParameterizationEngine:
    """
    Engine for semantic parameterization
    Implements Phase 3: Semantic Parameterization (語意參數化)
    Makes semantic specifications queryable, referencable, composable
    """
    
    def __init__(self, graph: SemanticGraph):
        """
        Initialize the parameterization engine
        
        Args:
            graph: Semantic graph from folding engine
        """
        self.graph = graph
        self.cache: Dict[str, Any] = {}
    
    def get_semantics(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Get semantic definition by ID
        
        Args:
            id: Node ID (e.g., "domain.runtime", "capability.dag")
            
        Returns:
            Dictionary with semantic information or None
        """
        node = self.graph.get_node(id)
        if not node:
            return None
        
        return {
            'id': node.id,
            'type': node.type.value,
            'features': node.features,
            'metadata': node.metadata,
            'relations': node.relations
        }
    
    def get_domain(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """
        Get domain semantic definition
        
        Args:
            domain_id: Domain identifier (e.g., "runtime", "quantum")
            
        Returns:
            Dictionary with domain semantics or None
        """
        node_id = f"domain.{domain_id}"
        return self.get_semantics(node_id)
    
    def get_capability(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """
        Get capability semantic definition
        
        Args:
            capability_id: Capability identifier (e.g., "dag", "schema")
            
        Returns:
            Dictionary with capability semantics or None
        """
        node_id = f"capability.{capability_id}"
        return self.get_semantics(node_id)
    
    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resource semantic definition
        
        Args:
            resource_id: Resource identifier (e.g., "executor", "generator")
            
        Returns:
            Dictionary with resource semantics or None
        """
        node_id = f"resource.{resource_id}"
        return self.get_semantics(node_id)
    
    def get_label(self, label_id: str) -> Optional[Dict[str, Any]]:
        """
        Get label semantic definition
        
        Args:
            label_id: Label identifier (e.g., "baseline.component", "policy.level")
            
        Returns:
            Dictionary with label semantics or None
        """
        node_id = f"label.{label_id}"
        return self.get_semantics(node_id)
    
    def get_relations(self, id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get relations for a semantic node
        
        Args:
            id: Node ID
            relation_type: Optional filter for relation type
            
        Returns:
            List of related nodes with relation information
        """
        related_nodes = self.graph.get_related_nodes(id, relation_type)
        results = []
        
        for node in related_nodes:
            results.append({
                'id': node.id,
                'type': node.type.value,
                'features': node.features,
                'metadata': node.metadata
            })
        
        return results
    
    def compose_semantics(self, ids: List[str]) -> Dict[str, Any]:
        """
        Compose multiple semantic definitions
        
        Args:
            ids: List of node IDs to compose
            
        Returns:
            Composed semantic definition
        """
        composed = {
            'features': set(),
            'types': set(),
            'nodes': []
        }
        
        for node_id in ids:
            semantics = self.get_semantics(node_id)
            if semantics:
                composed['features'].update(semantics['features'])
                composed['types'].add(semantics['type'])
                composed['nodes'].append(semantics)
        
        # Convert sets to lists
        composed['features'] = list(composed['features'])
        composed['types'] = list(composed['types'])
        
        # Compute composed vector (union of features)
        composed['vector'] = self._compose_vectors(ids)
        
        return composed
    
    def _compose_vectors(self, ids: List[str]) -> Optional[List[float]]:
        """Compose semantic vectors by taking union"""
        import numpy as np
        
        vectors = []
        for node_id in ids:
            node = self.graph.get_node(node_id)
            if node and node.vector is not None:
                vectors.append(node.vector)
        
        if not vectors:
            return None
        
        # Union: use element-wise maximum
        composed = np.maximum.reduce(vectors)
        return composed.tolist()
    
    def resolve_reference(self, reference: str) -> Optional[Dict[str, Any]]:
        """
        Resolve a semantic reference (e.g., "gl:runtime:dag")
        
        Args:
            reference: Semantic reference in format "gl:<domain>:<capability>"
            
        Returns:
            Resolved semantic definition or None
        """
        parts = reference.split(':')
        if len(parts) < 3 or parts[0] != 'gl':
            return None
        
        # Parse reference
        # Format: gl:<domain>:<capability>[:<resource>]
        domain = parts[1]
        capability = parts[2]
        resource = parts[3] if len(parts) > 3 else None
        
        if resource:
            return self.get_resource(resource)
        else:
            # Return capability with domain context
            capability_semantics = self.get_capability(capability)
            if capability_semantics:
                capability_semantics['domain_context'] = self.get_domain(domain)
            return capability_semantics
    
    def validate_semantic_reference(self, reference: str) -> bool:
        """
        Validate if a semantic reference exists
        
        Args:
            reference: Semantic reference string
            
        Returns:
            True if valid, False otherwise
        """
        return self.resolve_reference(reference) is not None
    
    def get_semantic_hierarchy(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get semantic hierarchy for a node (parent relationships)
        
        Args:
            node_id: Node ID
            
        Returns:
            List of parent nodes in hierarchy
        """
        node = self.graph.get_node(node_id)
        if not node:
            return []
        
        hierarchy = []
        
        # Find parents based on relations
        for edge in self.graph.edges:
            if edge.target_id == node_id:
                parent = self.graph.get_node(edge.source_id)
                if parent:
                    hierarchy.append({
                        'id': parent.id,
                        'type': parent.type.value,
                        'relation': edge.relation_type,
                        'metadata': parent.metadata
                    })
        
        return hierarchy
    
    def get_semantic_children(self, node_id: str) -> List[Dict[str, Any]]:
        """
        Get semantic children for a node (child relationships)
        
        Args:
            node_id: Node ID
            
        Returns:
            List of child nodes
        """
        node = self.graph.get_node(node_id)
        if not node:
            return []
        
        children = []
        
        # Find children based on relations
        for edge in self.graph.edges:
            if edge.source_id == node_id:
                child = self.graph.get_node(edge.target_id)
                if child:
                    children.append({
                        'id': child.id,
                        'type': child.type.value,
                        'relation': edge.relation_type,
                        'metadata': child.metadata
                    })
        
        return children
    
    def get_all_domains(self) -> List[Dict[str, Any]]:
        """Get all domain semantic definitions"""
        domains = self.graph.index.get_by_type(SemanticNodeType.DOMAIN)
        return [{'id': d.id, 'metadata': d.metadata, 'features': d.features} for d in domains]
    
    def get_all_capabilities(self, domain_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all capability semantic definitions
        
        Args:
            domain_id: Optional filter by domain
        """
        capabilities = self.graph.index.get_by_type(SemanticNodeType.CAPABILITY)
        
        if domain_id:
            # Filter by domain
            filtered = []
            for cap in capabilities:
                if f"domain.{domain_id}" in [rel.get('domain') for rel in cap.relations]:
                    filtered.append(cap)
            capabilities = filtered
        
        return [{'id': c.id, 'metadata': c.metadata, 'features': c.features} for c in capabilities]
    
    def get_all_resources(self, capability_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all resource semantic definitions
        
        Args:
            capability_id: Optional filter by capability
        """
        resources = self.graph.index.get_by_type(SemanticNodeType.RESOURCE)
        return [{'id': r.id, 'metadata': r.metadata, 'features': r.features} for r in resources]
    
    def get_all_labels(self) -> List[Dict[str, Any]]:
        """Get all label semantic definitions"""
        labels = self.graph.index.get_by_type(SemanticNodeType.LABEL)
        return [{'id': l.id, 'metadata': l.metadata, 'features': l.features} for l in labels]
    
    def clear_cache(self):
        """Clear the parameterization cache"""
        self.cache.clear()