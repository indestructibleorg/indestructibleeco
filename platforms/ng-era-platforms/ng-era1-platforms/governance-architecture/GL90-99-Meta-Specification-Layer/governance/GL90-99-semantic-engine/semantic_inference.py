# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Inference Engine
Implements reasoning capabilities over semantic graph
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import numpy as np
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

from .semantic_models import (
    SemanticNode, SemanticNodeType, SemanticGraph
)
from .semantic_folding import SemanticFoldingEngine
from .semantic_parameterization import SemanticParameterizationEngine


class SemanticInferenceEngine:
    """
    Engine for semantic inference
    Implements reasoning capabilities over the semantic graph
    """
    
    def __init__(self, graph: SemanticGraph, parameterization: SemanticParameterizationEngine):
        """
        Initialize the inference engine
        
        Args:
            graph: Semantic graph
            parameterization: Parameterization engine for semantic access
        """
        self.graph = graph
        self.param = parameterization
        self.folding = SemanticFoldingEngine()
        
        # Precompute inference cache
        self._precompute_inferences()
    
    def _precompute_inferences(self):
        """
        Precompute commonly used inferences
        Implements Phase 5: Semantic Precomputation
        """
        self.inference_cache = {}
        
        # Precompute capability-domain mappings
        self._compute_capability_domain_mappings()
        
        # Precompute feature co-occurrence
        self._compute_feature_cooccurrence()
    
    def _compute_capability_domain_mappings(self):
        """Precompute which capabilities belong to which domains"""
        self.capability_domain_map = {}
        
        for node_id, node in self.graph.nodes.items():
            if node.type == SemanticNodeType.CAPABILITY:
                for rel in node.relations:
                    if rel.get('relation') == 'belongs-to' and 'domain' in rel:
                        domain_id = rel['domain']
                        capability_id = node_id.replace('capability.', '')
                        self.capability_domain_map[capability_id] = domain_id
    
    def _compute_feature_cooccurrence(self):
        """Precompute feature co-occurrence statistics"""
        self.feature_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        for node_id, node in self.graph.nodes.items():
            for i, feat_i in enumerate(node.features):
                for feat_j in node.features[i+1:]:
                    self.feature_cooccurrence[feat_i][feat_j] += 1
                    self.feature_cooccurrence[feat_j][feat_i] += 1
    
    def infer_capabilities_for_domain(self, domain_id: str) -> List[Dict[str, Any]]:
        """
        Infer all capabilities belonging to a domain
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            List of capability definitions
        """
        capabilities = []
        domain_node_id = f"domain.{domain_id}"
        
        for node_id, node in self.graph.nodes.items():
            if node.type == SemanticNodeType.CAPABILITY:
                # Check if capability belongs to this domain
                for rel in node.relations:
                    if rel.get('relation') == 'belongs-to' and rel.get('domain') == domain_node_id:
                        capabilities.append({
                            'id': node_id,
                            'capability_id': node_id.replace('capability.', ''),
                            'metadata': node.metadata,
                            'features': node.features
                        })
                        break
        
        return capabilities
    
    def infer_resources_for_capability(self, capability_id: str) -> List[Dict[str, Any]]:
        """
        Infer all resources implementing a capability
        
        Args:
            capability_id: Capability identifier
            
        Returns:
            List of resource definitions
        """
        resources = []
        capability_node_id = f"capability.{capability_id}"
        
        # Find edges from capability to resources
        for edge in self.graph.edges:
            if edge.source_id == capability_node_id and edge.relation_type == 'implements':
                resource_node = self.graph.get_node(edge.target_id)
                if resource_node:
                    resources.append({
                        'id': resource_node.id,
                        'resource_id': resource_node.id.replace('resource.', ''),
                        'metadata': resource_node.metadata,
                        'features': resource_node.features
                    })
        
        return resources
    
    def infer_labels_for_resource(self, resource_id: str) -> List[Dict[str, Any]]:
        """
        Infer all labels applied to a resource
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            List of label definitions
        """
        labels = []
        resource_node_id = f"resource.{resource_id}"
        
        # Find edges from resource to labels
        for edge in self.graph.edges:
            if edge.source_id == resource_node_id and edge.relation_type == 'labeled-with':
                label_node = self.graph.get_node(edge.target_id)
                if label_node:
                    labels.append({
                        'id': label_node.id,
                        'label_id': label_node.id.replace('label.', ''),
                        'metadata': label_node.metadata,
                        'features': label_node.features
                    })
        
        return labels
    
    def infer_semantic_type(self, id: str) -> Optional[str]:
        """
        Infer the semantic type of an identifier
        
        Args:
            id: Identifier string
            
        Returns:
            Semantic type or None
        """
        # Check if it's a known node
        node = self.graph.get_node(id)
        if node:
            return node.type.value
        
        # Try to infer from naming convention
        if id.startswith('domain.'):
            return 'domain'
        elif id.startswith('capability.'):
            return 'capability'
        elif id.startswith('resource.'):
            return 'resource'
        elif id.startswith('label.'):
            return 'label'
        
        return None
    
    def infer_missing_semantics(
        self, 
        partial_features: List[str], 
        node_type: SemanticNodeType
    ) -> List[str]:
        """
        Infer missing semantic features based on partial information
        
        Args:
            partial_features: Known semantic features
            node_type: Type of node
            
        Returns:
            List of suggested additional features
        """
        suggestions = []
        
        # Find nodes of the same type
        for node_id, node in self.graph.nodes.items():
            if node.type == node_type:
                # Calculate feature overlap
                overlap = len(set(partial_features) & set(node.features))
                
                # If there's overlap, suggest missing features
                if overlap > 0 and overlap < len(node.features):
                    for feature in node.features:
                        if feature not in partial_features:
                            suggestions.append((feature, overlap))
        
        # Sort by overlap count and return unique suggestions
        suggestions = sorted(suggestions, key=lambda x: x[1], reverse=True)
        unique_suggestions = list({s[0] for s in suggestions})
        
        return unique_suggestions[:10]  # Return top 10
    
    def infer_capability_hierarchy(
        self, 
        domain_id: str
    ) -> List[Dict[str, Any]]:
        """
        Infer the capability hierarchy within a domain
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            List of capabilities with their hierarchy information
        """
        capabilities = self.infer_capabilities_for_domain(domain_id)
        
        # Build hierarchy based on feature relationships
        hierarchy = []
        
        for cap in capabilities:
            node = self.graph.get_node(cap['id'])
            if node:
                # Find related capabilities
                related = []
                for other in capabilities:
                    if other['id'] != cap['id']:
                        other_node = self.graph.get_node(other['id'])
                        if other_node:
                            similarity = node.semantic_similarity(other_node)
                            if similarity > 0.3:  # Threshold for related capabilities
                                related.append({
                                    'id': other['capability_id'],
                                    'similarity': similarity
                                })
                
                hierarchy.append({
                    'capability': cap,
                    'related_capabilities': related
                })
        
        return hierarchy
    
    def validate_semantic_conflict(
        self, 
        node_a_id: str, 
        node_b_id: str
    ) -> Dict[str, Any]:
        """
        Validate if two semantic nodes conflict
        
        Args:
            node_a_id: First node ID
            node_b_id: Second node ID
            
        Returns:
            Dictionary with conflict validation results
        """
        node_a = self.graph.get_node(node_a_id)
        node_b = self.graph.get_node(node_b_id)
        
        if not node_a or not node_b:
            return {'valid': False, 'reason': 'One or both nodes not found'}
        
        # Check for type conflict
        type_conflict = node_a.type == node_b.type and node_a.id != node_b.id
        
        # Check for feature conflict
        features_a = set(node_a.features)
        features_b = set(node_b.features)
        feature_overlap = features_a.intersection(features_b)
        
        # If same type and high feature overlap, potential conflict
        conflict_detected = (
            type_conflict and 
            len(feature_overlap) > 0 and 
            len(feature_overlap) >= min(len(features_a), len(features_b)) * 0.8
        )
        
        return {
            'valid': not conflict_detected,
            'conflict_detected': conflict_detected,
            'type_conflict': type_conflict,
            'feature_overlap': list(feature_overlap),
            'overlap_ratio': len(feature_overlap) / max(len(features_a), len(features_b)) if features_a or features_b else 0.0
        }
    
    def validate_semantic_completeness(
        self, 
        node_id: str
    ) -> Dict[str, Any]:
        """
        Validate if a semantic node has complete definitions
        
        Args:
            node_id: Node ID to validate
            
        Returns:
            Dictionary with completeness validation results
        """
        node = self.graph.get_node(node_id)
        
        if not node:
            return {'valid': False, 'reason': 'Node not found'}
        
        # Check required fields
        has_features = len(node.features) > 0
        has_metadata = len(node.metadata) > 0
        has_description = 'description' in node.metadata
        
        # Type-specific checks
        type_specific_valid = True
        if node.type == SemanticNodeType.CAPABILITY:
            # Capabilities should belong to a domain
            has_domain = any(
                rel.get('relation') == 'belongs-to' and 'domain' in rel
                for rel in node.relations
            )
            type_specific_valid = has_domain
        
        completeness_score = 0.0
        checks = [has_features, has_metadata, has_description, type_specific_valid]
        completeness_score = sum(checks) / len(checks) if checks else 0.0
        
        return {
            'valid': completeness_score >= 0.75,
            'completeness_score': completeness_score,
            'has_features': has_features,
            'has_metadata': has_metadata,
            'has_description': has_description,
            'type_specific_valid': type_specific_valid,
            'checks': {
                'features': has_features,
                'metadata': has_metadata,
                'description': has_description,
                'type_specific': type_specific_valid
            }
        }
    
    def validate_semantic_consistency(
        self, 
        node_id: str
    ) -> Dict[str, Any]:
        """
        Validate semantic consistency of a node
        
        Args:
            node_id: Node ID to validate
            
        Returns:
            Dictionary with consistency validation results
        """
        node = self.graph.get_node(node_id)
        
        if not node:
            return {'valid': False, 'reason': 'Node not found'}
        
        # Check feature consistency
        features = node.features
        feature_count = len(features)
        
        # Check for contradictory features
        contradictions = []
        
        # Example: execution vs read-only
        if 'execution' in features and 'read-only' in features:
            contradictions.append(('execution', 'read-only'))
        
        # Check for redundant features
        feature_set = set(features)
        has_duplicates = len(features) != len(feature_set)
        
        return {
            'valid': len(contradictions) == 0 and not has_duplicates,
            'contradictions': contradictions,
            'has_duplicates': has_duplicates,
            'feature_count': feature_count,
            'unique_features': len(feature_set)
        }
    
    def infer_semantic_chain(
        self, 
        start_node_id: str, 
        end_node_id: str
    ) -> Optional[List[str]]:
        """
        Infer semantic chain/path between two nodes
        
        Args:
            start_node_id: Starting node ID
            end_node_id: Ending node ID
            
        Returns:
            List of node IDs forming the chain, or None if no chain
        """
        return self.graph.find_shortest_path(start_node_id, end_node_id)
    
    def get_inference_stats(self) -> Dict[str, Any]:
        """Get statistics about the inference engine"""
        return {
            'capability_domain_mappings': len(self.capability_domain_map),
            'feature_cooccurrence_entries': len(self.feature_cooccurrence),
            'cache_size': len(self.inference_cache)
        }