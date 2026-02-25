"""Directed Acyclic Graph and dependency resolution for IaOps modules.

Provides a DAG data structure with topological sorting, cycle detection,
root/leaf discovery, and a DependencyResolver that computes build/deploy
ordering for governed modules.
"""
from __future__ import annotations

from collections import deque
from datetime import datetime, timezone
from enum import Enum
from typing import Any

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class NodeStatus(str, Enum):
    """Lifecycle status of a DAG node."""

    PENDING = "pending"
    READY = "ready"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class DagNode(BaseModel):
    """A single node in the dependency graph."""

    id: str
    label: str = ""
    deps: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    status: NodeStatus = NodeStatus.PENDING


class CycleInfo(BaseModel):
    """Information about a detected cycle."""

    cycle: list[str]
    description: str = ""


class TopologicalResult(BaseModel):
    """Result of a topological sort operation."""

    order: list[str]
    is_acyclic: bool
    cycles: list[CycleInfo] = Field(default_factory=list)


class ResolutionResult(BaseModel):
    """Result of dependency resolution."""

    build_order: list[str]
    layers: list[list[str]]
    roots: list[str]
    leaves: list[str]
    is_valid: bool
    errors: list[str] = Field(default_factory=list)
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


# ---------------------------------------------------------------------------
# DAG implementation
# ---------------------------------------------------------------------------


class DAG:
    """Directed Acyclic Graph for module dependencies.

    Stores nodes and edges, provides traversal and analysis operations.
    Edge semantics: an edge from A -> B means "A depends on B" (B must come
    before A in topological order).
    """

    def __init__(self) -> None:
        self._nodes: dict[str, DagNode] = {}
        self._forward: dict[str, set[str]] = {}   # node -> set of its dependencies
        self._reverse: dict[str, set[str]] = {}    # node -> set of dependants

    # -- construction -------------------------------------------------------

    def add_node(self, node_id: str, *, label: str = "", deps: list[str] | None = None,
                 metadata: dict[str, Any] | None = None) -> DagNode:
        """Add a node to the graph.

        Args:
            node_id: Unique identifier for the node.
            label: Human-readable label.
            deps: List of node IDs this node depends on.
            metadata: Arbitrary key-value metadata.

        Returns:
            The created DagNode.

        Raises:
            ValueError: If the node_id already exists.
        """
        if node_id in self._nodes:
            raise ValueError(f"Node '{node_id}' already exists in the DAG")
        dep_list = deps or []
        node = DagNode(id=node_id, label=label or node_id, deps=dep_list,
                       metadata=metadata or {})
        self._nodes[node_id] = node
        self._forward[node_id] = set(dep_list)
        if node_id not in self._reverse:
            self._reverse[node_id] = set()
        for dep in dep_list:
            if dep not in self._reverse:
                self._reverse[dep] = set()
            self._reverse[dep].add(node_id)
        logger.debug("dag_node_added", node_id=node_id, deps=dep_list)
        return node

    def add_edge(self, from_id: str, to_id: str) -> None:
        """Add a dependency edge: *from_id* depends on *to_id*.

        Args:
            from_id: The dependent node.
            to_id: The dependency (prerequisite).

        Raises:
            KeyError: If either node does not exist.
            ValueError: If the edge would create a self-loop.
        """
        if from_id not in self._nodes:
            raise KeyError(f"Node '{from_id}' not found in the DAG")
        if to_id not in self._nodes:
            raise KeyError(f"Node '{to_id}' not found in the DAG")
        if from_id == to_id:
            raise ValueError(f"Self-loop not allowed: '{from_id}'")
        self._forward[from_id].add(to_id)
        self._reverse[to_id].add(from_id)
        if to_id not in self._nodes[from_id].deps:
            self._nodes[from_id].deps.append(to_id)

    def remove_node(self, node_id: str) -> None:
        """Remove a node and all its edges from the graph.

        Raises:
            KeyError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found in the DAG")
        # Remove forward edges
        for dep in self._forward.pop(node_id, set()):
            self._reverse.get(dep, set()).discard(node_id)
        # Remove reverse edges
        for dependant in self._reverse.pop(node_id, set()):
            self._forward.get(dependant, set()).discard(node_id)
            node = self._nodes.get(dependant)
            if node and node_id in node.deps:
                node.deps.remove(node_id)
        del self._nodes[node_id]
        logger.debug("dag_node_removed", node_id=node_id)

    # -- class methods for bulk construction --------------------------------

    @classmethod
    def from_nodes(cls, nodes: list[dict[str, Any]]) -> DAG:
        """Construct a DAG from a list of node dictionaries.

        Each dictionary must have an ``id`` key and may include ``deps``,
        ``label``, and ``metadata``.
        """
        dag = cls()
        for n in nodes:
            dag.add_node(
                node_id=n["id"],
                label=n.get("label", ""),
                deps=list(n.get("deps", [])),
                metadata=n.get("metadata", {}),
            )
        return dag

    @classmethod
    def from_edges(cls, node_ids: list[str], edges: list[tuple[str, str]]) -> DAG:
        """Construct a DAG from node IDs and a list of ``(from, to)`` edges."""
        dag = cls()
        for nid in node_ids:
            if nid not in dag._nodes:
                dag.add_node(nid)
        for from_id, to_id in edges:
            dag.add_edge(from_id, to_id)
        return dag

    # -- queries ------------------------------------------------------------

    @property
    def node_ids(self) -> list[str]:
        """Return all node IDs in insertion order."""
        return list(self._nodes.keys())

    @property
    def size(self) -> int:
        """Number of nodes in the graph."""
        return len(self._nodes)

    def get_node(self, node_id: str) -> DagNode:
        """Retrieve a node by ID.

        Raises:
            KeyError: If the node does not exist.
        """
        if node_id not in self._nodes:
            raise KeyError(f"Node '{node_id}' not found in the DAG")
        return self._nodes[node_id]

    def has_node(self, node_id: str) -> bool:
        """Check whether a node exists in the graph."""
        return node_id in self._nodes

    def dependencies_of(self, node_id: str) -> list[str]:
        """Return the direct dependencies of a node (what it depends on)."""
        return list(self._forward.get(node_id, set()))

    def dependants_of(self, node_id: str) -> list[str]:
        """Return the direct dependants of a node (what depends on it)."""
        return list(self._reverse.get(node_id, set()))

    def transitive_dependencies(self, node_id: str) -> set[str]:
        """Return all transitive dependencies (deep) of a given node."""
        visited: set[str] = set()
        queue = deque(self.dependencies_of(node_id))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.dependencies_of(current))
        return visited

    def transitive_dependants(self, node_id: str) -> set[str]:
        """Return all transitive dependants (everything depending on this node)."""
        visited: set[str] = set()
        queue = deque(self.dependants_of(node_id))
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            queue.extend(self.dependants_of(current))
        return visited

    # -- structural analysis ------------------------------------------------

    def find_roots(self) -> list[str]:
        """Find root nodes -- nodes with no dependencies (in-degree zero).

        These are the starting points of the graph: they have no prerequisites.
        """
        return sorted(
            nid for nid, deps in self._forward.items()
            if not deps or not deps.intersection(self._nodes.keys())
        )

    def find_leaves(self) -> list[str]:
        """Find leaf nodes -- nodes with no dependants (out-degree zero).

        These are the terminal endpoints: nothing depends on them.
        """
        return sorted(
            nid for nid, dependants in self._reverse.items()
            if not dependants.intersection(self._nodes.keys())
        )

    def detect_cycles(self) -> list[CycleInfo]:
        """Detect all cycles in the graph using DFS-based cycle detection.

        Returns a list of CycleInfo objects, each describing one cycle found.
        An empty list means the graph is acyclic.
        """
        WHITE, GRAY, BLACK = 0, 1, 2
        color: dict[str, int] = {nid: WHITE for nid in self._nodes}
        parent: dict[str, str | None] = {nid: None for nid in self._nodes}
        cycles: list[CycleInfo] = []

        def _dfs(node: str) -> None:
            color[node] = GRAY
            for dep in sorted(self._forward.get(node, set())):
                if dep not in self._nodes:
                    continue
                if color[dep] == GRAY:
                    # Back-edge found => cycle
                    cycle_path = [dep, node]
                    cur = node
                    while cur != dep:
                        cur = parent[cur]  # type: ignore[assignment]
                        if cur is None:
                            break
                        cycle_path.append(cur)
                    cycle_path.reverse()
                    cycles.append(CycleInfo(
                        cycle=cycle_path,
                        description=f"Cycle detected: {' -> '.join(cycle_path)}",
                    ))
                elif color[dep] == WHITE:
                    parent[dep] = node
                    _dfs(dep)
            color[node] = BLACK

        for nid in sorted(self._nodes.keys()):
            if color[nid] == WHITE:
                _dfs(nid)

        if cycles:
            logger.warning("dag_cycles_detected", count=len(cycles))
        return cycles

    def is_acyclic(self) -> bool:
        """Return True if the graph has no cycles."""
        return len(self.detect_cycles()) == 0

    def topological_sort(self) -> TopologicalResult:
        """Compute a topological ordering of all nodes using Kahn's algorithm.

        Returns a TopologicalResult containing the order if acyclic, or
        cycle information if cycles are present.
        """
        ids = set(self._nodes.keys())
        # Build adjacency: dep -> list of dependants within the graph
        adj: dict[str, list[str]] = {nid: [] for nid in ids}
        indeg: dict[str, int] = {nid: 0 for nid in ids}

        for nid in ids:
            for dep in self._forward.get(nid, set()):
                if dep in ids:
                    adj[dep].append(nid)
                    indeg[nid] += 1

        # Seed with zero-indegree nodes (sorted for deterministic output)
        queue: deque[str] = deque(sorted(nid for nid in ids if indeg[nid] == 0))
        result: list[str] = []

        while queue:
            current = queue.popleft()
            result.append(current)
            next_ready: list[str] = []
            for successor in adj[current]:
                indeg[successor] -= 1
                if indeg[successor] == 0:
                    next_ready.append(successor)
            for n in sorted(next_ready):
                queue.append(n)

        if len(result) == len(ids):
            logger.debug("topological_sort_success", order=result)
            return TopologicalResult(order=result, is_acyclic=True)

        cycles = self.detect_cycles()
        logger.warning("topological_sort_failed", processed=len(result), total=len(ids))
        return TopologicalResult(order=result, is_acyclic=False, cycles=cycles)

    def parallel_layers(self) -> list[list[str]]:
        """Compute parallel execution layers (nodes in the same layer have no
        inter-dependencies and can be processed concurrently).

        Returns a list of layers, where each layer is a list of node IDs.
        """
        ids = set(self._nodes.keys())
        adj: dict[str, list[str]] = {nid: [] for nid in ids}
        indeg: dict[str, int] = {nid: 0 for nid in ids}

        for nid in ids:
            for dep in self._forward.get(nid, set()):
                if dep in ids:
                    adj[dep].append(nid)
                    indeg[nid] += 1

        layers: list[list[str]] = []
        current_layer = sorted(nid for nid in ids if indeg[nid] == 0)

        while current_layer:
            layers.append(current_layer)
            next_layer_set: set[str] = set()
            for node in current_layer:
                for successor in adj[node]:
                    indeg[successor] -= 1
                    if indeg[successor] == 0:
                        next_layer_set.add(successor)
            current_layer = sorted(next_layer_set)

        return layers

    def subgraph(self, node_ids: set[str]) -> DAG:
        """Create a new DAG containing only the specified node IDs and edges
        between them."""
        sub = DAG()
        for nid in sorted(node_ids):
            if nid in self._nodes:
                original = self._nodes[nid]
                filtered_deps = [d for d in original.deps if d in node_ids]
                sub.add_node(
                    node_id=nid,
                    label=original.label,
                    deps=filtered_deps,
                    metadata=dict(original.metadata),
                )
        return sub

    def to_dict(self) -> dict[str, Any]:
        """Serialize the DAG to a plain dictionary."""
        return {
            "nodes": [
                {
                    "id": n.id,
                    "label": n.label,
                    "deps": n.deps,
                    "metadata": n.metadata,
                    "status": n.status.value,
                }
                for n in self._nodes.values()
            ],
        }

    def __repr__(self) -> str:
        return f"DAG(nodes={len(self._nodes)}, roots={self.find_roots()}, leaves={self.find_leaves()})"


# ---------------------------------------------------------------------------
# DependencyResolver
# ---------------------------------------------------------------------------


class DependencyResolver:
    """Resolves module build/deploy order from a dependency graph.

    Wraps a DAG and provides high-level resolution semantics: validates the
    graph, computes a safe execution order, and identifies parallelisable
    layers for concurrent processing.
    """

    def __init__(self, dag: DAG) -> None:
        self._dag = dag
        self._log = logger.bind(component="dependency_resolver")

    @property
    def dag(self) -> DAG:
        """Access the underlying DAG."""
        return self._dag

    def resolve(self) -> ResolutionResult:
        """Resolve the full dependency graph into a build order.

        Validates acyclicity, computes topological order, parallel layers,
        and identifies root/leaf nodes.
        """
        self._log.info("resolve_start", node_count=self._dag.size)
        errors: list[str] = []

        # Check for missing dependencies (referenced but not in the graph)
        for nid in self._dag.node_ids:
            for dep in self._dag.dependencies_of(nid):
                if not self._dag.has_node(dep):
                    errors.append(
                        f"Node '{nid}' depends on '{dep}' which is not in the graph"
                    )

        topo = self._dag.topological_sort()
        if not topo.is_acyclic:
            for ci in topo.cycles:
                errors.append(ci.description)
            self._log.error("resolve_failed", errors=errors)
            return ResolutionResult(
                build_order=[],
                layers=[],
                roots=self._dag.find_roots(),
                leaves=self._dag.find_leaves(),
                is_valid=False,
                errors=errors,
            )

        layers = self._dag.parallel_layers()
        roots = self._dag.find_roots()
        leaves = self._dag.find_leaves()

        self._log.info(
            "resolve_success",
            build_order=topo.order,
            layer_count=len(layers),
            root_count=len(roots),
            leaf_count=len(leaves),
        )

        return ResolutionResult(
            build_order=topo.order,
            layers=layers,
            roots=roots,
            leaves=leaves,
            is_valid=len(errors) == 0,
            errors=errors,
        )

    def resolve_subset(self, target_ids: set[str], *, include_transitive: bool = True) -> ResolutionResult:
        """Resolve a subset of the graph starting from the given target nodes.

        When *include_transitive* is True (the default), all transitive
        dependencies of *target_ids* are included in the resolution.
        """
        all_ids = set(target_ids)
        if include_transitive:
            for tid in target_ids:
                all_ids |= self._dag.transitive_dependencies(tid)

        sub_dag = self._dag.subgraph(all_ids)
        sub_resolver = DependencyResolver(sub_dag)
        return sub_resolver.resolve()

    def impact_of(self, node_id: str) -> set[str]:
        """Return the set of nodes that would be affected if *node_id* changes.

        This is the transitive closure of dependants -- everything downstream.
        """
        return self._dag.transitive_dependants(node_id)
