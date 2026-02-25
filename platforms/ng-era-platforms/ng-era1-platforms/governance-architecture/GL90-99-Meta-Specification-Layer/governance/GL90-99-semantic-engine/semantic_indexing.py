# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: python-module
# @ECO-audit-trail: ../../engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
#
# GL Unified Architecture Governance Framework Activated
# GL Root Semantic Anchor: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/semantic/ECO-ROOT-SEMANTIC-ANCHOR.yaml
# GL Unified Naming Charter: gl-enterprise-architecture/governance/engine/governance/gl-artifacts/meta/naming-charter/gl-unified-naming-charter.yaml

"""
Semantic Indexing Engine
Implements millisecond-level semantic queries with multiple index types
"""

"""
Module docstring
================

This module is part of the GL governance framework.
Please add specific module documentation here.
"""
# MNGA-002: Import organization needs review
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict
import bisect

from .semantic_models import (
    SemanticNode, SemanticNodeType, SemanticGraph, SemanticIndex
)


class SemanticIndexingEngine:
    """
    Engine for semantic indexing
    Implements Phase 4: Semantic Indexing (語意索引)
    Provides millisecond-level semantic queries
    """
    
    def __init__(self, graph: SemanticGraph):
        """
        Initialize the indexing engine
        
        Args:
            graph: Semantic graph to index
        """
        self.graph = graph
        self.index = graph.index
        
        # Build additional indices
        self._build_feature_bitmap_index()
        self._build_vector_index()
        self._build_similarity_cache()
    
    def _build_feature_bitmap_index(self):
        """
        Build bitmap index for feature-based queries
        Enables O(1) feature existence checks
        """
        self.feature_bitmap = {}
        
        for node_id, node in self.graph.nodes.items():
            # Create bitmap for each node's features
            bitmap = set(node.features)
            self.feature_bitmap[node_id] = bitmap
    
    def _build_vector_index(self):
        """
        Build spatial index for vector similarity queries
        Uses simple FAISS-like structure (can be replaced with actual FAISS)
        """
        self.vector_index = {}
        
        for node_id, node in self.graph.nodes.items():
            if node.vector is not None:
                # Store vector with node ID
                self.vector_index[node_id] = node.vector
    
    def _build_similarity_cache(self):
        """
        Build cache for frequently used similarity computations
        Implements Phase 5: Semantic Cache (語意快取)
        """
        self.similarity_cache: Dict[Tuple[str, str], float] = {}
    
    def query_by_id(self, id: str) -> Optional[SemanticNode]:
        """
        Query semantic node by ID - O(1)
        
        Args:
            id: Node ID
            
        Returns:
            SemanticNode or None
        """
        return self.index.by_id.get(id)
    
    def query_by_feature(self, feature: str) -> List[SemanticNode]:
        """
        Query semantic nodes by feature - O(1)
        
        Args:
            feature: Semantic feature to search for
            
        Returns:
            List of semantic nodes with the feature
        """
        return self.index.get_by_feature(feature)
    
    def query_by_features(self, features: List[str], match_all: bool = False, partial_match: bool = True) -> List[SemanticNode]:
        """
        Query semantic nodes by multiple features
        
        Args:
            features: List of semantic features
            match_all: If True, require all features; if False, require any feature
            partial_match: If True, also do partial string matching
            
        Returns:
            List of matching semantic nodes
        """
        # First try exact matches
        exact_matches = []
        if match_all:
            # Find nodes that have ALL features
            candidates = None
            for feature in features:
                nodes = set(self.query_by_feature(feature))
                if candidates is None:
                    candidates = nodes
                else:
                    candidates = candidates.intersection(nodes)
            
            exact_matches = [self.graph.nodes[nid] for nid in candidates] if candidates else []
        else:
            # Find nodes that have ANY feature
            node_set = set()
            for feature in features:
                nodes = self.query_by_feature(feature)
                node_set.update([node.id for node in nodes])
            
            exact_matches = [self.graph.nodes[nid] for nid in node_set]
        
        # If partial matching is enabled and no exact matches found, try partial matching
        if partial_match and not exact_matches:
            partial_matches = []
            for node_id, node in self.graph.nodes.items():
                for feature in features:
                    for node_feature in node.features:
                        if feature.lower() in node_feature.lower() or node_feature.lower() in feature.lower():
                            partial_matches.append(node)
                            break
                    if node in partial_matches:
                        break
            
            return list(set(partial_matches))  # Remove duplicates
        
        return exact_matches
    
    def query_by_domain(self, domain_id: str) -> List[SemanticNode]:
        """
        Query semantic nodes by domain - O(1)
        
        Args:
            domain_id: Domain identifier
            
        Returns:
            List of nodes in the domain
        """
        domain_node_id = f"domain.{domain_id}"
        return self.index.get_by_domain(domain_node_id)
    
    def query_by_capability(self, capability_id: str) -> List[SemanticNode]:
        """
        Query semantic nodes by capability - O(1)
        
        Args:
            capability_id: Capability identifier
            
        Returns:
            List of nodes implementing the capability
        """
        capability_node_id = f"capability.{capability_id}"
        return self.index.get_by_capability(capability_node_id)
    
    def query_by_label(self, label_id: str) -> List[SemanticNode]:
        """
        Query semantic nodes by label - O(1)
        
        Args:
            label_id: Label identifier
            
        Returns:
            List of nodes with the label
        """
        label_node_id = f"label.{label_id}"
        return self.index.get_by_label(label_node_id)
    
    def query_by_type(self, node_type: SemanticNodeType) -> List[SemanticNode]:
        """
        Query semantic nodes by type - O(1)
        
        Args:
            node_type: Node type
            
        Returns:
            List of nodes of the specified type
        """
        return self.index.get_by_type(node_type)
    
    def semantic_search(
        self, 
        query_vector: np.ndarray, 
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Semantic vector search with similarity ranking
        
        Args:
            query_vector: Query vector
            top_k: Number of top results to return
            threshold: Minimum similarity threshold
            
        Returns:
            List of (node_id, similarity_score) tuples
        """
        results = []
        
        for node_id, node_vector in self.vector_index.items():
            # Compute cosine similarity
            dot_product = np.dot(query_vector, node_vector)
            norm_query = np.linalg.norm(query_vector)
            norm_node = np.linalg.norm(node_vector)
            
            if norm_query == 0 or norm_node == 0:
                similarity = 0.0
            else:
                similarity = dot_product / (norm_query * norm_node)
            
            if similarity >= threshold:
                results.append((node_id, similarity))
        
        # Sort by similarity (descending)
        results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top_k results
        return results[:top_k]
    
    def semantic_search_by_text(
        self, 
        query_text: str, 
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Semantic search by text (converts text to vector first)
        
        Args:
            query_text: Query text
            top_k: Number of top results
            threshold: Minimum similarity threshold
            
        Returns:
            List of (node_id, similarity_score) tuples
        """
        # Import here to avoid circular dependency
        try:
            from .semantic_folding import SemanticFoldingEngine
        except ImportError:
            from semantic_folding import SemanticFoldingEngine
        
        # Create vector from text features
        folding_engine = SemanticFoldingEngine(embedding_dim=128)
        query_vector = folding_engine._create_semantic_vector([query_text])
        
        return self.semantic_search(query_vector, top_k, threshold)
    
    def find_semantically_similar(
        self, 
        node_id: str, 
        top_k: int = 10,
        threshold: float = 0.0
    ) -> List[Tuple[str, float]]:
        """
        Find nodes semantically similar to a given node
        
        Args:
            node_id: Reference node ID
            top_k: Number of top results
            threshold: Minimum similarity threshold
            
        Returns:
            List of (node_id, similarity_score) tuples
        """
        node = self.graph.get_node(node_id)
        if not node or node.vector is None:
            return []
        
        return self.semantic_search(node.vector, top_k, threshold)
    
    def find_semantic_overlap(
        self, 
        node_a_id: str, 
        node_b_id: str
    ) -> Dict[str, Any]:
        """
        Find semantic overlap between two nodes
        
        Args:
            node_a_id: First node ID
            node_b_id: Second node ID
            
        Returns:
            Dictionary with overlap information
        """
        node_a = self.graph.get_node(node_a_id)
        node_b = self.graph.get_node(node_b_id)
        
        if not node_a or not node_b:
            return {'overlap': [], 'similarity': 0.0}
        
        # Find overlapping features
        features_a = set(node_a.features)
        features_b = set(node_b.features)
        overlap = features_a.intersection(features_b)
        
        # Calculate Jaccard similarity
        union = features_a.union(features_b)
        jaccard = len(overlap) / len(union) if union else 0.0
        
        # Calculate semantic similarity using vectors
        semantic_sim = node_a.semantic_similarity(node_b)
        
        return {
            'overlap_features': list(overlap),
            'jaccard_similarity': jaccard,
            'semantic_similarity': semantic_sim,
            'node_a_features': len(features_a),
            'node_b_features': len(features_b),
            'overlap_count': len(overlap)
        }
    
    def find_semantic_path(
        self, 
        source_id: str, 
        target_id: str
    ) -> Optional[List[str]]:
        """
        Find semantic path between two nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            List of node IDs representing the path, or None if no path
        """
        return self.graph.find_shortest_path(source_id, target_id)
    
    def query_related_nodes(
        self, 
        node_id: str, 
        relation_type: Optional[str] = None,
        depth: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Query nodes related to a given node
        
        Args:
            node_id: Reference node ID
            relation_type: Optional filter for relation type
            depth: How many levels deep to traverse
            
        Returns:
            List of related nodes with distance information
        """
        results = []
        visited = {node_id}
        queue = [(node_id, 0)]
        
        while queue:
            current_id, distance = queue.pop(0)
            
            if distance > depth:
                continue
            
            node = self.graph.get_node(current_id)
            if not node:
                continue
            
            # Find related nodes
            for edge in self.graph.edges:
                if edge.source_id == current_id:
                    related_id = edge.target_id
                    if related_id not in visited:
                        visited.add(related_id)
                        
                        # Check relation type filter
                        if relation_type is None or edge.relation_type == relation_type:
                            related_node = self.graph.get_node(related_id)
                            if related_node:
                                results.append({
                                    'id': related_id,
                                    'type': related_node.type.value,
                                    'distance': distance + 1,
                                    'relation': edge.relation_type,
                                    'metadata': related_node.metadata
                                })
                        
                        queue.append((related_id, distance + 1))
        
        return results
    
    def get_index_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index
        
        Returns:
            Dictionary with index statistics
        """
        return {
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'indexed_features': len(self.index.by_feature),
            'indexed_domains': len(self.index.by_domain),
            'indexed_capabilities': len(self.index.by_capability),
            'indexed_labels': len(self.index.by_label),
            'indexed_vectors': len(self.vector_index),
            'cache_size': len(self.similarity_cache)
        }
    
    def clear_cache(self):
        """Clear similarity cache"""
        self.similarity_cache.clear()