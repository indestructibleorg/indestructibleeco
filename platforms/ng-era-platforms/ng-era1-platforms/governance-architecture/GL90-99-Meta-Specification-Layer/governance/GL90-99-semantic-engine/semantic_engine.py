# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Core Engine
Main engine integrating folding, parameterization, indexing, and inference
Phase 6: Semantic Engine Integration (語意引擎化)
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
from typing import Dict, Any, List, Optional
import yaml

from .semantic_models import SemanticNode, SemanticGraph, SemanticNodeType
from .semantic_folding import SemanticFoldingEngine
from .semantic_parameterization import SemanticParameterizationEngine
from .semantic_indexing import SemanticIndexingEngine
from .semantic_inference import SemanticInferenceEngine


class SemanticEngine:
    """
    Main Semantic Core Engine
    Integrates all semantic processing capabilities into a unified API
    """
    
    def __init__(self, embedding_dim: int = 128):
        """
        Initialize the semantic engine
        
        Args:
            embedding_dim: Dimension for semantic vectors
        """
        self.embedding_dim = embedding_dim
        
        # Initialize sub-engines
        self.folding = SemanticFoldingEngine(embedding_dim=embedding_dim)
        self.graph: Optional[SemanticGraph] = None
        self.parameterization: Optional[SemanticParameterizationEngine] = None
        self.indexing: Optional[SemanticIndexingEngine] = None
        self.inference: Optional[SemanticInferenceEngine] = None
    
    def load_specification(self, spec_yaml: str) -> SemanticGraph:
        """
        Load and fold a YAML specification
        
        Args:
            spec_yaml: YAML string containing semantic specification
            
        Returns:
            SemanticGraph containing folded semantic nodes
        """
        # Fold specification into semantic graph
        self.graph = self.folding.fold_specification(spec_yaml)
        
        # Initialize parameterization engine
        self.parameterization = SemanticParameterizationEngine(self.graph)
        
        # Initialize indexing engine
        self.indexing = SemanticIndexingEngine(self.graph)
        
        # Initialize inference engine
        self.inference = SemanticInferenceEngine(self.graph, self.parameterization)
        
        return self.graph
    
    def load_specification_from_file(self, file_path: str) -> SemanticGraph:
        """
        Load specification from YAML file
        
        Args:
            file_path: Path to YAML file
            
        Returns:
            SemanticGraph containing folded semantic nodes
        """
        with open(file_path, 'r') as f:
            spec_yaml = f.read()
        return self.load_specification(spec_yaml)
    
    # ==================== Semantic Query API ====================
    
    def get_domain(self, domain_id: str) -> Optional[Dict[str, Any]]:
        """
        Get domain semantic definition
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            Domain definition or None
        """
        if not self.parameterization:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.parameterization.get_domain(domain_id)
    
    def get_capability(self, capability_id: str) -> Optional[Dict[str, Any]]:
        """
        Get capability semantic definition
        
        Args:
            capability_id: Capability identifier
            
        Returns:
            Capability definition or None
        """
        if not self.parameterization:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.parameterization.get_capability(capability_id)
    
    def get_resource(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Get resource semantic definition
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            Resource definition or None
        """
        if not self.parameterization:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.parameterization.get_resource(resource_id)
    
    def get_label(self, label_id: str) -> Optional[Dict[str, Any]]:
        """
        Get label semantic definition
        
        Args:
            label_id: Label identifier
            
        Returns:
            Label definition or None
        """
        if not self.parameterization:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.parameterization.get_label(label_id)
    
    def query(self, id: str) -> Optional[Dict[str, Any]]:
        """
        Query semantic node by ID
        
        Args:
            id: Node ID
            
        Returns:
            Node definition or None
        """
        if not self.parameterization:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.parameterization.get_semantics(id)
    
    def query_by_feature(self, feature: str) -> List[Dict[str, Any]]:
        """
        Query semantic nodes by feature
        
        Args:
            feature: Semantic feature
            
        Returns:
            List of node definitions
        """
        if not self.indexing:
            raise RuntimeError("Engine not initialized. Load specification first.")
        nodes = self.indexing.query_by_feature(feature)
        return [{'id': n.id, 'type': n.type.value, 'metadata': n.metadata} for n in nodes]
    
    def query_related(self, id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Query nodes related to a given node
        
        Args:
            id: Node ID
            relation_type: Optional relation type filter
            
        Returns:
            List of related node definitions
        """
        if not self.parameterization:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.parameterization.get_relations(id, relation_type)
    
    def semantic_search(
        self, 
        query: str, 
        top_k: int = 10, 
        threshold: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Semantic search over all nodes
        
        Args:
            query: Query text or node ID
            top_k: Number of results
            threshold: Minimum similarity threshold
            
        Returns:
            List of (node_id, similarity_score) tuples
        """
        if not self.indexing:
            raise RuntimeError("Engine not initialized. Load specification first.")
        
        # Check if query is a node ID
        node = self.graph.get_node(query)
        if node and node.vector is not None:
            results = self.indexing.semantic_search(
                node.vector, 
                top_k=top_k, 
                threshold=threshold
            )
        else:
            # Treat as text search
            results = self.indexing.semantic_search_by_text(
                query, 
                top_k=top_k, 
                threshold=threshold
            )
        
        return [{'node_id': nid, 'similarity': sim} for nid, sim in results]
    
    # ==================== Semantic Inference API ====================
    
    def infer_capabilities(self, domain_id: str) -> List[Dict[str, Any]]:
        """
        Infer capabilities for a domain
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            List of capability definitions
        """
        if not self.inference:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.inference.infer_capabilities_for_domain(domain_id)
    
    def infer_resources(self, capability_id: str) -> List[Dict[str, Any]]:
        """
        Infer resources for a capability
        
        Args:
            capability_id: Capability identifier
            
        Returns:
            List of resource definitions
        """
        if not self.inference:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.inference.infer_resources_for_capability(capability_id)
    
    def infer_labels(self, resource_id: str) -> List[Dict[str, Any]]:
        """
        Infer labels for a resource
        
        Args:
            resource_id: Resource identifier
            
        Returns:
            List of label definitions
        """
        if not self.inference:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.inference.infer_labels_for_resource(resource_id)
    
    # ==================== Semantic Validation API ====================
    
    def validate_conflict(self, node_a_id: str, node_b_id: str) -> Dict[str, Any]:
        """
        Validate semantic conflict between two nodes
        
        Args:
            node_a_id: First node ID
            node_b_id: Second node ID
            
        Returns:
            Validation results
        """
        if not self.inference:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.inference.validate_semantic_conflict(node_a_id, node_b_id)
    
    def validate_duplicate(self, node_id: str) -> Dict[str, Any]:
        """
        Validate if a node has duplicates
        
        Args:
            node_id: Node ID to check
            
        Returns:
            Validation results
        """
        if not self.indexing:
            raise RuntimeError("Engine not initialized. Load specification first.")
        
        node = self.graph.get_node(node_id)
        if not node:
            return {'valid': True, 'duplicates': []}
        
        duplicates = []
        for nid, other_node in self.graph.nodes.items():
            if nid != node_id and other_node.type == node.type:
                similarity = node.semantic_similarity(other_node)
                if similarity > 0.9:  # High similarity threshold
                    duplicates.append({
                        'id': nid,
                        'similarity': similarity,
                        'features': other_node.features
                    })
        
        return {
            'valid': len(duplicates) == 0,
            'duplicates': duplicates
        }
    
    def validate_consistency(self, node_id: str) -> Dict[str, Any]:
        """
        Validate semantic consistency of a node
        
        Args:
            node_id: Node ID
            
        Returns:
            Validation results
        """
        if not self.inference:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.inference.validate_semantic_consistency(node_id)
    
    def validate_completeness(self, node_id: str) -> Dict[str, Any]:
        """
        Validate semantic completeness of a node
        
        Args:
            node_id: Node ID
            
        Returns:
            Validation results
        """
        if not self.inference:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.inference.validate_semantic_completeness(node_id)
    
    # ==================== Semantic Mapping API ====================
    
    def map_internal_to_ui(self, internal_id: str) -> Optional[Dict[str, Any]]:
        """
        Map internal ID to UI representation
        
        Args:
            internal_id: Internal node ID
            
        Returns:
            UI mapping information
        """
        if not self.graph:
            raise RuntimeError("Engine not initialized. Load specification first.")
        
        node = self.graph.get_node(internal_id)
        if not node:
            return None
        
        return {
            'internal_id': internal_id,
            'ui_name': node.metadata.get('description', internal_id),
            'ui_display': node.metadata.get('abbr', internal_id.split('.')[-1].upper()),
            'type': node.type.value,
            'features': node.features
        }
    
    def map_platform_to_api(self, platform_id: str) -> Optional[Dict[str, Any]]:
        """
        Map platform identifier to API endpoint
        
        Args:
            platform_id: Platform identifier
            
        Returns:
            API endpoint information
        """
        # This would use semantic-mapping from the specification
        # For now, return a basic mapping
        return {
            'platform_id': platform_id,
            'api_endpoint': f'/api/{platform_id.replace("-", "/")}',
            'version': 'v1.0.0'
        }
    
    def map_component_to_functional(self, component_id: str) -> Optional[Dict[str, Any]]:
        """
        Map component ID to functional description
        
        Args:
            component_id: Component identifier
            
        Returns:
            Functional mapping information
        """
        node = self.graph.get_node(component_id) if self.graph else None
        if not node:
            return None
        
        return {
            'component_id': component_id,
            'functional_description': node.metadata.get('description', ''),
            'capabilities': node.features,
            'type': node.type.value
        }
    
    # ==================== Utility Methods ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get engine statistics"""
        return {
            'graph_nodes': len(self.graph.nodes) if self.graph else 0,
            'graph_edges': len(self.graph.edges) if self.graph else 0,
            'indexed_features': len(self.indexing.index.by_feature) if self.indexing else 0,
            'indexed_vectors': len(self.indexing.vector_index) if self.indexing else 0,
            'folding_cache_size': len(self.folding.feature_mapping),
            'inference_cache_size': len(self.inference.inference_cache) if self.inference else 0
        }
    
    def export_graph(self) -> Dict[str, Any]:
        """Export the semantic graph to dictionary"""
        if not self.graph:
            raise RuntimeError("Engine not initialized. Load specification first.")
        return self.graph.to_dict()
    
    def export_graph_json(self) -> str:
        """Export the semantic graph to JSON string"""
        import json
        return json.dumps(self.export_graph(), indent=2)