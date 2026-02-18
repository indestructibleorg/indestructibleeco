"""Inference & Reasoning Engine.

Derives implicit knowledge through logical rules and graph traversal.
Supports deductive, inductive, and abductive reasoning over knowledge
graphs with confidence scoring and explanation generation.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class ReasoningEngine:
    """Performs multi-hop reasoning over graph structures.

    Capabilities:
    - Deductive: A→B, B→C ∴ A→C (transitive closure)
    - Inductive: Pattern generalization from observed instances
    - Abductive: Best explanation inference from observations
    - Path finding: Shortest/all paths between entities
    - Subgraph extraction: Contextual neighborhood retrieval
    """

    def __init__(self, max_depth: int = 10, max_paths: int = 100) -> None:
        self._max_depth = max_depth
        self._max_paths = max_paths

    def reason(
        self,
        graph_data: dict[str, Any],
        start_node: str,
        relation_path: list[str] | None = None,
        target_node: str | None = None,
        max_depth: int | None = None,
        reasoning_type: str = "deductive",
    ) -> dict[str, Any]:
        """Execute reasoning query over a graph.

        Args:
            graph_data: Serialized graph with nodes and edges.
            start_node: Starting node ID.
            relation_path: Sequence of relation types to follow.
            target_node: Optional target node for path finding.
            max_depth: Maximum traversal depth.
            reasoning_type: One of deductive, inductive, abductive.

        Returns:
            Dict with paths, inferences, confidence, and explanations.
        """
        start = time.perf_counter()
        depth = min(max_depth or self._max_depth, self._max_depth)
        graph = self._deserialize_graph(graph_data)

        if reasoning_type == "deductive":
            result = self._deductive_reasoning(graph, start_node, relation_path, target_node, depth)
        elif reasoning_type == "inductive":
            result = self._inductive_reasoning(graph, start_node, depth)
        elif reasoning_type == "abductive":
            result = self._abductive_reasoning(graph, start_node, target_node, depth)
        else:
            raise ValueError(f"Unsupported reasoning type: {reasoning_type}")

        elapsed_ms = (time.perf_counter() - start) * 1000
        result["metadata"] = {
            "reasoning_type": reasoning_type,
            "start_node": start_node,
            "target_node": target_node,
            "max_depth": depth,
            "query_time_ms": round(elapsed_ms, 2),
        }
        return result

    def find_paths(
        self,
        graph_data: dict[str, Any],
        source: str,
        target: str,
        max_depth: int | None = None,
    ) -> list[dict[str, Any]]:
        """Find all simple paths between two nodes.

        Args:
            graph_data: Serialized graph.
            source: Source node ID.
            target: Target node ID.
            max_depth: Maximum path length.

        Returns:
            List of paths with nodes, edges, and lengths.
        """
        graph = self._deserialize_graph(graph_data)
        depth = min(max_depth or self._max_depth, self._max_depth)

        if source not in graph or target not in graph:
            return []

        paths = []
        try:
            for path in nx.all_simple_paths(graph, source, target, cutoff=depth):
                if len(paths) >= self._max_paths:
                    break
                edge_sequence = []
                for i in range(len(path) - 1):
                    edge_data = graph.edges[path[i], path[i + 1]]
                    edge_sequence.append({
                        "from": path[i],
                        "to": path[i + 1],
                        "relation": edge_data.get("relation", "related"),
                    })
                paths.append({
                    "nodes": path,
                    "edges": edge_sequence,
                    "length": len(path) - 1,
                })
        except nx.NetworkXError:
            pass

        return paths

    def extract_subgraph(
        self,
        graph_data: dict[str, Any],
        center_node: str,
        radius: int = 2,
    ) -> dict[str, Any]:
        """Extract neighborhood subgraph around a center node.

        Args:
            graph_data: Serialized graph.
            center_node: Center node ID.
            radius: Hop distance for neighborhood.

        Returns:
            Serialized subgraph.
        """
        graph = self._deserialize_graph(graph_data)
        if center_node not in graph:
            return {"nodes": [], "edges": []}

        neighborhood = nx.ego_graph(graph, center_node, radius=radius)
        return self._serialize_graph(neighborhood)

    def _deductive_reasoning(
        self,
        graph: nx.DiGraph,
        start: str,
        relation_path: list[str] | None,
        target: str | None,
        max_depth: int,
    ) -> dict[str, Any]:
        """Deductive reasoning: follow relation chains to derive conclusions."""
        if start not in graph:
            return {"inferences": [], "confidence": 0.0, "explanation": f"Start node '{start}' not found."}

        inferences: list[dict[str, Any]] = []

        if relation_path:
            reachable = self._follow_relation_chain(graph, start, relation_path)
            for node_id, path_taken in reachable:
                confidence = 1.0 / (1.0 + len(path_taken) * 0.1)
                inferences.append({
                    "conclusion": node_id,
                    "path": path_taken,
                    "confidence": round(confidence, 4),
                    "rule": f"Transitive closure over [{' → '.join(relation_path)}]",
                })
        elif target:
            paths = self.find_paths({"nodes": [], "edges": []}, start, target, max_depth)
            graph_data = self._serialize_graph(graph)
            paths = self.find_paths(graph_data, start, target, max_depth)
            for p in paths:
                confidence = 1.0 / (1.0 + p["length"] * 0.15)
                relations = [e["relation"] for e in p["edges"]]
                inferences.append({
                    "conclusion": target,
                    "path": p["nodes"],
                    "confidence": round(confidence, 4),
                    "rule": f"Path via [{' → '.join(relations)}]",
                })
        else:
            for neighbor in graph.successors(start):
                edge_data = graph.edges[start, neighbor]
                inferences.append({
                    "conclusion": neighbor,
                    "path": [start, neighbor],
                    "confidence": 0.95,
                    "rule": f"Direct edge: {edge_data.get('relation', 'related')}",
                })

        inferences.sort(key=lambda x: x["confidence"], reverse=True)
        avg_conf = sum(i["confidence"] for i in inferences) / max(len(inferences), 1)

        return {
            "inferences": inferences[:50],
            "confidence": round(avg_conf, 4),
            "explanation": f"Deductive reasoning from '{start}': {len(inferences)} conclusions derived.",
        }

    def _inductive_reasoning(
        self,
        graph: nx.DiGraph,
        start: str,
        max_depth: int,
    ) -> dict[str, Any]:
        """Inductive reasoning: generalize patterns from observed instances."""
        if start not in graph:
            return {"inferences": [], "confidence": 0.0, "explanation": f"Node '{start}' not found."}

        node_type = graph.nodes[start].get("type", "unknown")
        same_type_nodes = [n for n, d in graph.nodes(data=True) if d.get("type") == node_type and n != start]

        patterns: dict[str, int] = {}
        for node in same_type_nodes:
            for _, target, data in graph.out_edges(node, data=True):
                rel = data.get("relation", "related")
                target_type = graph.nodes[target].get("type", "unknown")
                pattern_key = f"{rel}→{target_type}"
                patterns[pattern_key] = patterns.get(pattern_key, 0) + 1

        total_same = max(len(same_type_nodes), 1)
        inferences = []
        for pattern, count in sorted(patterns.items(), key=lambda x: x[1], reverse=True):
            confidence = count / total_same
            rel, target_type = pattern.split("→", 1)
            inferences.append({
                "conclusion": f"{start} likely has relation '{rel}' to a '{target_type}' node",
                "pattern": pattern,
                "support": count,
                "confidence": round(confidence, 4),
                "rule": f"Inductive: {count}/{total_same} nodes of type '{node_type}' exhibit this pattern",
            })

        avg_conf = sum(i["confidence"] for i in inferences) / max(len(inferences), 1)

        return {
            "inferences": inferences[:30],
            "confidence": round(avg_conf, 4),
            "explanation": f"Inductive reasoning: {len(inferences)} patterns generalized from {total_same} similar nodes.",
        }

    def _abductive_reasoning(
        self,
        graph: nx.DiGraph,
        observation: str,
        hypothesis: str | None,
        max_depth: int,
    ) -> dict[str, Any]:
        """Abductive reasoning: find best explanation for an observation."""
        if observation not in graph:
            return {"inferences": [], "confidence": 0.0, "explanation": f"Observation node '{observation}' not found."}

        predecessors = list(graph.predecessors(observation))
        explanations = []

        for pred in predecessors:
            edge_data = graph.edges[pred, observation]
            pred_in_degree = graph.in_degree(pred)
            pred_out_degree = graph.out_degree(pred)
            specificity = 1.0 / (1.0 + pred_out_degree * 0.2)
            support = 1.0 / (1.0 + pred_in_degree * 0.1)
            confidence = (specificity + support) / 2.0

            explanations.append({
                "hypothesis": pred,
                "relation": edge_data.get("relation", "causes"),
                "confidence": round(confidence, 4),
                "specificity": round(specificity, 4),
                "support": round(support, 4),
                "rule": f"'{pred}' —[{edge_data.get('relation', 'causes')}]→ '{observation}'",
            })

        if hypothesis and hypothesis in graph:
            for expl in explanations:
                if expl["hypothesis"] == hypothesis:
                    expl["confidence"] = min(expl["confidence"] * 1.2, 1.0)
                    expl["rule"] += " (matches target hypothesis)"

        explanations.sort(key=lambda x: x["confidence"], reverse=True)
        best_conf = explanations[0]["confidence"] if explanations else 0.0

        return {
            "inferences": explanations[:20],
            "confidence": round(best_conf, 4),
            "explanation": f"Abductive reasoning: {len(explanations)} candidate explanations for '{observation}'.",
        }

    def _follow_relation_chain(
        self,
        graph: nx.DiGraph,
        start: str,
        relations: list[str],
    ) -> list[tuple[str, list[str]]]:
        """Follow a specific sequence of relation types from start node."""
        current_nodes = [(start, [start])]

        for rel in relations:
            next_nodes = []
            for node, path in current_nodes:
                for _, target, data in graph.out_edges(node, data=True):
                    if data.get("relation") == rel:
                        next_nodes.append((target, path + [target]))
            current_nodes = next_nodes
            if not current_nodes:
                break

        return current_nodes

    @staticmethod
    def _deserialize_graph(graph_data: dict[str, Any]) -> nx.DiGraph:
        """Reconstruct NetworkX graph from serialized format."""
        graph = nx.DiGraph()
        for node in graph_data.get("nodes", []):
            attrs = {k: v for k, v in node.items() if k != "id"}
            if "properties" in attrs:
                props = attrs.pop("properties")
                attrs.update(props)
            graph.add_node(node["id"], **attrs)

        for edge in graph_data.get("edges", []):
            attrs = {k: v for k, v in edge.items() if k not in ("source", "target")}
            graph.add_edge(edge["source"], edge["target"], **attrs)

        return graph

    @staticmethod
    def _serialize_graph(graph: nx.DiGraph) -> dict[str, Any]:
        """Serialize NetworkX graph to portable dict."""
        nodes = []
        for nid, attrs in graph.nodes(data=True):
            nodes.append({"id": nid, **attrs})
        edges = []
        for src, tgt, attrs in graph.edges(data=True):
            edges.append({"source": src, "target": tgt, **attrs})
        return {"nodes": nodes, "edges": edges}