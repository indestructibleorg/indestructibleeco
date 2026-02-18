"""Graph Structure Folding Engine.

Constructs knowledge graphs from text/code, expressing hierarchical
relationships through nodes and edges. Suitable for complex relational
data analysis such as dependency trees, call graphs, and entity relations.
"""
from __future__ import annotations

import hashlib
import logging
import re
import time
from typing import Any

import networkx as nx

logger = logging.getLogger(__name__)


class GraphFoldingEngine:
    """Transforms content into graph representations.

    Pipeline: parse → extract entities → build edges → compute metrics → output.
    Uses NetworkX for in-memory graph operations.
    """

    def __init__(self, max_nodes: int = 10000, max_depth: int = 50) -> None:
        self._max_nodes = max_nodes
        self._max_depth = max_depth

    def fold(
        self,
        content: str,
        content_type: str = "source_code",
        language: str | None = None,
    ) -> dict[str, Any]:
        """Full graph folding pipeline.

        Args:
            content: Raw text or code to fold into a graph.
            content_type: One of source_code, document, config, log.
            language: Programming language hint.

        Returns:
            Dict with id, graph (nodes/edges), metadata, folding_time_ms.
        """
        start = time.perf_counter()

        if content_type == "source_code":
            graph = self._fold_source_code(content, language)
        elif content_type == "config":
            graph = self._fold_config(content)
        elif content_type == "log":
            graph = self._fold_log(content)
        else:
            graph = self._fold_document(content)

        metrics = self._compute_graph_metrics(graph)
        serialized = self._serialize_graph(graph)
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
        elapsed_ms = (time.perf_counter() - start) * 1000

        return {
            "id": f"gf-{content_hash}",
            "graph": serialized,
            "metadata": {
                "content_type": content_type,
                "language": language,
                "node_count": graph.number_of_nodes(),
                "edge_count": graph.number_of_edges(),
                **metrics,
            },
            "folding_time_ms": round(elapsed_ms, 2),
        }

    def _fold_source_code(self, content: str, language: str | None) -> nx.DiGraph:
        """Extract call graph and dependency structure from source code."""
        graph = nx.DiGraph()
        lines = content.split("\n")

        current_scope: str | None = None
        scope_stack: list[str] = []
        indent_stack: list[int] = []

        func_pattern = re.compile(
            r"^(\s*)(def|class|function|func|fn|pub fn|async def|async function)\s+(\w+)"
        )
        import_pattern = re.compile(
            r"^(?:import|from|require|use|include|#include)\s+(.+)"
        )
        call_pattern = re.compile(r"(\w+)\s*\(")

        module_node = "module::root"
        graph.add_node(module_node, type="module", label="root", depth=0)

        for line_num, line in enumerate(lines, 1):
            if line_num > self._max_nodes:
                break

            import_match = import_pattern.match(line.strip())
            if import_match:
                dep = import_match.group(1).strip().split()[0].rstrip(";")
                dep_node = f"import::{dep}"
                if not graph.has_node(dep_node):
                    graph.add_node(dep_node, type="import", label=dep, depth=1)
                    graph.add_edge(module_node, dep_node, relation="imports")
                continue

            func_match = func_pattern.match(line)
            if func_match:
                indent = len(func_match.group(1))
                kind = func_match.group(2)
                name = func_match.group(3)

                while indent_stack and indent <= indent_stack[-1]:
                    indent_stack.pop()
                    if scope_stack:
                        scope_stack.pop()

                node_type = "class" if kind == "class" else "function"
                node_id = f"{node_type}::{name}"
                depth = len(scope_stack) + 1

                if not graph.has_node(node_id):
                    graph.add_node(node_id, type=node_type, label=name, depth=depth, line=line_num)

                parent = scope_stack[-1] if scope_stack else module_node
                relation = "contains" if node_type == "function" else "defines"
                graph.add_edge(parent, node_id, relation=relation)

                scope_stack.append(node_id)
                indent_stack.append(indent)
                current_scope = node_id
                continue

            if current_scope:
                calls = call_pattern.findall(line)
                for callee in calls:
                    if callee in ("if", "for", "while", "return", "print", "len", "range", "str", "int", "float"):
                        continue
                    callee_node = f"function::{callee}"
                    if not graph.has_node(callee_node):
                        graph.add_node(callee_node, type="function", label=callee, depth=0, external=True)
                    if not graph.has_edge(current_scope, callee_node):
                        graph.add_edge(current_scope, callee_node, relation="calls")

        return graph

    def _fold_config(self, content: str) -> nx.DiGraph:
        """Extract hierarchical structure from configuration files."""
        graph = nx.DiGraph()
        root = "config::root"
        graph.add_node(root, type="config_root", label="root", depth=0)

        lines = content.split("\n")
        parent_stack: list[tuple[str, int]] = [(root, -1)]

        for line in lines:
            stripped = line.rstrip()
            if not stripped or stripped.startswith("#") or stripped.startswith("//"):
                continue

            indent = len(line) - len(line.lstrip())
            key_match = re.match(r"^(\s*)([a-zA-Z_][\w.-]*)\s*[:=]", line)
            if not key_match:
                continue

            key = key_match.group(2)
            node_id = f"config::{key}_{indent}"

            while len(parent_stack) > 1 and indent <= parent_stack[-1][1]:
                parent_stack.pop()

            parent = parent_stack[-1][0]
            graph.add_node(node_id, type="config_key", label=key, depth=len(parent_stack))
            graph.add_edge(parent, node_id, relation="contains")
            parent_stack.append((node_id, indent))

        return graph

    def _fold_log(self, content: str) -> nx.DiGraph:
        """Extract event sequences and error chains from log content."""
        graph = nx.DiGraph()
        root = "log::timeline"
        graph.add_node(root, type="timeline", label="timeline", depth=0)

        lines = content.split("\n")
        prev_node: str | None = None
        error_count = 0

        for i, line in enumerate(lines):
            if not line.strip():
                continue
            if i >= self._max_nodes:
                break

            is_error = any(kw in line.upper() for kw in ("ERROR", "FATAL", "EXCEPTION", "TRACEBACK", "PANIC"))
            is_warn = "WARN" in line.upper()

            node_type = "error" if is_error else ("warning" if is_warn else "info")
            node_id = f"log::entry_{i}"
            graph.add_node(node_id, type=node_type, label=line[:80], depth=1, line_num=i)
            graph.add_edge(root, node_id, relation="contains")

            if prev_node:
                graph.add_edge(prev_node, node_id, relation="followed_by")

            if is_error:
                error_count += 1
                error_group = f"log::error_group_{error_count}"
                if not graph.has_node(error_group):
                    graph.add_node(error_group, type="error_group", label=f"Error #{error_count}", depth=1)
                    graph.add_edge(root, error_group, relation="error_cluster")
                graph.add_edge(error_group, node_id, relation="instance")

            prev_node = node_id

        return graph

    def _fold_document(self, content: str) -> nx.DiGraph:
        """Extract section hierarchy and entity relationships from documents."""
        graph = nx.DiGraph()
        root = "doc::root"
        graph.add_node(root, type="document", label="document", depth=0)

        sections = re.split(r"\n(?=#{1,6}\s)", content)
        heading_pattern = re.compile(r"^(#{1,6})\s+(.+)")

        parent_stack: list[tuple[str, int]] = [(root, 0)]

        for i, section in enumerate(sections):
            heading_match = heading_pattern.match(section)
            if heading_match:
                level = len(heading_match.group(1))
                title = heading_match.group(2).strip()
                node_id = f"section::{title.lower().replace(' ', '_')}_{i}"

                while len(parent_stack) > 1 and level <= parent_stack[-1][1]:
                    parent_stack.pop()

                parent = parent_stack[-1][0]
                graph.add_node(node_id, type="section", label=title, depth=level)
                graph.add_edge(parent, node_id, relation="contains")
                parent_stack.append((node_id, level))
            elif section.strip():
                para_id = f"paragraph::{i}"
                parent = parent_stack[-1][0]
                graph.add_node(para_id, type="paragraph", label=section.strip()[:60], depth=parent_stack[-1][1] + 1)
                graph.add_edge(parent, para_id, relation="contains")

        return graph

    @staticmethod
    def _compute_graph_metrics(graph: nx.DiGraph) -> dict[str, Any]:
        """Compute structural metrics for the graph."""
        metrics: dict[str, Any] = {
            "density": round(nx.density(graph), 6) if graph.number_of_nodes() > 0 else 0,
            "is_dag": nx.is_directed_acyclic_graph(graph),
        }

        if graph.number_of_nodes() > 0 and graph.number_of_nodes() < 5000:
            try:
                if nx.is_weakly_connected(graph):
                    undirected = graph.to_undirected()
                    metrics["diameter"] = nx.diameter(undirected)
                    metrics["avg_path_length"] = round(nx.average_shortest_path_length(undirected), 4)
            except (nx.NetworkXError, nx.NetworkXUnfeasible):
                pass

            degrees = [d for _, d in graph.degree()]
            if degrees:
                metrics["avg_degree"] = round(sum(degrees) / len(degrees), 4)
                metrics["max_degree"] = max(degrees)

        return metrics

    @staticmethod
    def _serialize_graph(graph: nx.DiGraph) -> dict[str, Any]:
        """Serialize NetworkX graph to portable dict format."""
        nodes = []
        for node_id, attrs in graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": attrs.get("label", node_id),
                "type": attrs.get("type", "unknown"),
                "properties": {k: v for k, v in attrs.items() if k not in ("label", "type")},
            })

        edges = []
        for src, tgt, attrs in graph.edges(data=True):
            edges.append({
                "source": src,
                "target": tgt,
                "relation": attrs.get("relation", "related"),
                "weight": attrs.get("weight", 1.0),
            })

        return {"nodes": nodes, "edges": edges}