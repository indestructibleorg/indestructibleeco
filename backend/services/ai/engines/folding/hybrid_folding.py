"""Hybrid Folding Orchestrator.

Combines vector and graph folding methods to balance efficiency with
semantic richness. Uses vectors for base feature representation and
graph structures for supplementary relationship information.
"""
from __future__ import annotations

import hashlib
import logging
import time
from typing import Any

import numpy as np

from .vector_folding import VectorFoldingEngine
from .graph_folding import GraphFoldingEngine

logger = logging.getLogger(__name__)


class HybridFoldingOrchestrator:
    """Orchestrates combined vector + graph folding pipelines.

    Strategy:
    1. Run vector folding to produce dense embeddings.
    2. Run graph folding to extract structural relationships.
    3. Compute graph-derived features (degree centrality, PageRank).
    4. Concatenate vector embedding with graph features.
    5. Return unified representation.
    """

    def __init__(
        self,
        vector_engine: VectorFoldingEngine,
        graph_engine: GraphFoldingEngine,
        graph_feature_dim: int = 32,
    ) -> None:
        self._vector_engine = vector_engine
        self._graph_engine = graph_engine
        self._graph_feature_dim = graph_feature_dim

    def fold(
        self,
        content: str,
        content_type: str = "source_code",
        language: str | None = None,
        target_dimensions: int | None = None,
    ) -> dict[str, Any]:
        """Execute hybrid folding: vector + graph combined.

        Args:
            content: Raw content to fold.
            content_type: Content classification.
            language: Programming language hint.
            target_dimensions: Final output dimensionality.

        Returns:
            Dict with id, vector, graph, metadata, folding_time_ms.
        """
        start = time.perf_counter()

        vector_result = self._vector_engine.fold(content, content_type, language, target_dimensions)
        graph_result = self._graph_engine.fold(content, content_type, language)

        graph_features = self._extract_graph_features(graph_result["graph"])
        combined_vector = self._fuse_representations(
            np.array(vector_result["vector"], dtype=np.float32),
            graph_features,
            target_dimensions,
        )

        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "id": f"hf-{content_hash}",
            "vector": combined_vector.tolist(),
            "graph": graph_result["graph"],
            "metadata": {
                "content_type": content_type,
                "language": language,
                "strategy": "hybrid",
                "vector_dim": len(vector_result["vector"]),
                "graph_feature_dim": len(graph_features),
                "combined_dim": len(combined_vector),
                "node_count": graph_result["metadata"]["node_count"],
                "edge_count": graph_result["metadata"]["edge_count"],
                "vector_time_ms": vector_result["folding_time_ms"],
                "graph_time_ms": graph_result["folding_time_ms"],
            },
            "folding_time_ms": round(elapsed_ms, 2),
        }

    def _extract_graph_features(self, graph_data: dict[str, Any]) -> np.ndarray:
        """Extract fixed-size feature vector from graph structure.

        Computes:
        - Node type distribution
        - Degree statistics (mean, max, std)
        - Structural metrics (density, depth distribution)
        - Relation type distribution
        """
        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        features: list[float] = []

        features.append(float(len(nodes)))
        features.append(float(len(edges)))
        features.append(len(edges) / max(len(nodes), 1))

        type_counts: dict[str, int] = {}
        for node in nodes:
            ntype = node.get("type", "unknown")
            type_counts[ntype] = type_counts.get(ntype, 0) + 1
        type_entropy = self._compute_entropy(list(type_counts.values()))
        features.append(type_entropy)
        features.append(float(len(type_counts)))

        in_degree: dict[str, int] = {}
        out_degree: dict[str, int] = {}
        for edge in edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            out_degree[src] = out_degree.get(src, 0) + 1
            in_degree[tgt] = in_degree.get(tgt, 0) + 1

        all_degrees = [in_degree.get(n["id"], 0) + out_degree.get(n["id"], 0) for n in nodes]
        if all_degrees:
            features.append(float(np.mean(all_degrees)))
            features.append(float(np.max(all_degrees)))
            features.append(float(np.std(all_degrees)))
        else:
            features.extend([0.0, 0.0, 0.0])

        relation_counts: dict[str, int] = {}
        for edge in edges:
            rel = edge.get("relation", "unknown")
            relation_counts[rel] = relation_counts.get(rel, 0) + 1
        rel_entropy = self._compute_entropy(list(relation_counts.values()))
        features.append(rel_entropy)
        features.append(float(len(relation_counts)))

        depths = [n.get("properties", {}).get("depth", 0) for n in nodes]
        if depths:
            features.append(float(max(depths)))
            features.append(float(np.mean(depths)))
        else:
            features.extend([0.0, 0.0])

        leaf_count = sum(1 for n in nodes if out_degree.get(n["id"], 0) == 0)
        features.append(float(leaf_count))
        features.append(leaf_count / max(len(nodes), 1))

        feature_array = np.array(features, dtype=np.float32)

        if len(feature_array) < self._graph_feature_dim:
            feature_array = np.pad(feature_array, (0, self._graph_feature_dim - len(feature_array)))
        elif len(feature_array) > self._graph_feature_dim:
            feature_array = feature_array[: self._graph_feature_dim]

        norm = np.linalg.norm(feature_array) + 1e-10
        return feature_array / norm

    def _fuse_representations(
        self,
        vector: np.ndarray,
        graph_features: np.ndarray,
        target_dimensions: int | None,
    ) -> np.ndarray:
        """Fuse vector embedding with graph features via weighted concatenation."""
        graph_weight = 0.3
        vector_weight = 0.7

        weighted_vector = vector * vector_weight
        weighted_graph = graph_features * graph_weight
        combined = np.concatenate([weighted_vector, weighted_graph])

        if target_dimensions and target_dimensions < len(combined):
            combined = combined[:target_dimensions]

        norm = np.linalg.norm(combined) + 1e-10
        return combined / norm

    @staticmethod
    def _compute_entropy(counts: list[int]) -> float:
        """Compute Shannon entropy from a list of counts."""
        total = sum(counts)
        if total == 0:
            return 0.0
        probs = [c / total for c in counts if c > 0]
        return -sum(p * np.log2(p) for p in probs)