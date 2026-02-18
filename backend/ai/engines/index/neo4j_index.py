"""Neo4j Graph Index Adapter.

Optimizes storage and querying of relational data through a graph
database. Supports multi-hop traversal, pattern matching, and
fast lookup of associated entities via Cypher queries.
"""
from __future__ import annotations

import logging
import time
from typing import Any

logger = logging.getLogger(__name__)


class Neo4jIndexAdapter:
    """Manages graph data persistence and querying via Neo4j.

    Features:
    - Async driver with connection pooling
    - Batch node/edge ingestion with UNWIND
    - Cypher-based pattern matching and traversal
    - Full-text and vector index support (Neo4j 5.x)
    """

    def __init__(
        self,
        uri: str = "bolt://localhost:7687",
        user: str = "neo4j",
        password: str = "eco_graph_secret",
        database: str = "neo4j",
    ) -> None:
        self._uri = uri
        self._user = user
        self._password = password
        self._database = database
        self._driver: Any = None

    async def initialize(self) -> None:
        """Initialize Neo4j async driver and verify connectivity."""
        try:
            from neo4j import AsyncGraphDatabase
            self._driver = AsyncGraphDatabase.driver(self._uri, auth=(self._user, self._password))
            async with self._driver.session(database=self._database) as session:
                result = await session.run("RETURN 1 AS ping")
                record = await result.single()
                if record and record["ping"] == 1:
                    logger.info("Neo4j connected: %s (db=%s)", self._uri, self._database)
        except ImportError:
            logger.warning("neo4j driver not installed; graph index operating in mock mode")
            self._driver = None
        except Exception as e:
            logger.warning("Neo4j connection failed: %s; operating in mock mode", e)
            self._driver = None

    async def close(self) -> None:
        """Close the Neo4j driver."""
        if self._driver:
            await self._driver.close()
            logger.info("Neo4j driver closed")

    async def upsert_node(self, node_id: str, labels: list[str], properties: dict[str, Any]) -> bool:
        """Create or update a node.

        Args:
            node_id: Unique node identifier.
            labels: Neo4j labels for the node.
            properties: Node properties.

        Returns:
            True if operation succeeded.
        """
        if not self._driver:
            return False

        label_str = ":".join(labels) if labels else "Node"
        props = {**properties, "node_id": node_id, "updated_at": time.time()}

        query = f"""
        MERGE (n:{label_str} {{node_id: $node_id}})
        SET n += $props
        RETURN n.node_id AS id
        """
        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, node_id=node_id, props=props)
            record = await result.single()
            return record is not None

    async def upsert_edge(
        self, source_id: str, target_id: str, relation: str, properties: dict[str, Any] | None = None,
    ) -> bool:
        """Create or update a relationship between two nodes.

        Args:
            source_id: Source node ID.
            target_id: Target node ID.
            relation: Relationship type.
            properties: Edge properties.

        Returns:
            True if operation succeeded.
        """
        if not self._driver:
            return False

        props = {**(properties or {}), "updated_at": time.time()}
        query = f"""
        MATCH (a {{node_id: $source_id}})
        MATCH (b {{node_id: $target_id}})
        MERGE (a)-[r:{relation}]->(b)
        SET r += $props
        RETURN type(r) AS rel
        """
        async with self._driver.session(database=self._database) as session:
            result = await session.run(query, source_id=source_id, target_id=target_id, props=props)
            record = await result.single()
            return record is not None

    async def ingest_graph(self, graph_data: dict[str, Any]) -> dict[str, int]:
        """Batch ingest a full graph structure.

        Args:
            graph_data: Dict with nodes and edges lists.

        Returns:
            Dict with counts of ingested nodes and edges.
        """
        if not self._driver:
            return {"nodes": 0, "edges": 0}

        nodes = graph_data.get("nodes", [])
        edges = graph_data.get("edges", [])

        node_count = 0
        async with self._driver.session(database=self._database) as session:
            batch_query = """
            UNWIND $nodes AS node
            MERGE (n:Entity {node_id: node.id})
            SET n.label = node.label, n.type = node.type, n.updated_at = timestamp()
            """
            node_records = [{"id": n["id"], "label": n.get("label", ""), "type": n.get("type", "unknown")} for n in nodes]
            await session.run(batch_query, nodes=node_records)
            node_count = len(node_records)

        edge_count = 0
        async with self._driver.session(database=self._database) as session:
            for edge in edges:
                rel = edge.get("relation", "RELATED_TO").upper().replace(" ", "_")
                query = f"""
                MATCH (a:Entity {{node_id: $source}})
                MATCH (b:Entity {{node_id: $target}})
                MERGE (a)-[r:{rel}]->(b)
                SET r.weight = $weight, r.updated_at = timestamp()
                """
                await session.run(query, source=edge["source"], target=edge["target"], weight=edge.get("weight", 1.0))
                edge_count += 1

        logger.info("Ingested graph: %d nodes, %d edges", node_count, edge_count)
        return {"nodes": node_count, "edges": edge_count}

    async def search(
        self,
        query: str,
        top_k: int = 10,
        node_type: str | None = None,
    ) -> dict[str, Any]:
        """Search nodes by text matching on labels and properties.

        Args:
            query: Search text.
            top_k: Maximum results.
            node_type: Filter by node type.

        Returns:
            Dict with matched nodes and search metadata.
        """
        start = time.perf_counter()

        if not self._driver:
            return {"results": [], "metadata": {"index_type": "neo4j", "mode": "mock"}}

        type_filter = "AND n.type = $node_type" if node_type else ""
        cypher = f"""
        MATCH (n:Entity)
        WHERE toLower(n.label) CONTAINS toLower($query)
        {type_filter}
        RETURN n.node_id AS id, n.label AS label, n.type AS type
        LIMIT $top_k
        """
        params: dict[str, Any] = {"query": query, "top_k": top_k}
        if node_type:
            params["node_type"] = node_type

        results = []
        async with self._driver.session(database=self._database) as session:
            result = await session.run(cypher, **params)
            async for record in result:
                results.append({
                    "id": record["id"],
                    "label": record["label"],
                    "type": record["type"],
                    "score": 1.0,
                })

        elapsed_ms = (time.perf_counter() - start) * 1000
        return {
            "results": results,
            "metadata": {
                "index_type": "neo4j",
                "query": query,
                "returned": len(results),
                "query_time_ms": round(elapsed_ms, 2),
            },
        }

    async def traverse(
        self,
        start_node: str,
        relation: str | None = None,
        max_depth: int = 3,
        direction: str = "outgoing",
    ) -> dict[str, Any]:
        """Traverse graph from a starting node.

        Args:
            start_node: Starting node ID.
            relation: Filter by relationship type.
            max_depth: Maximum traversal depth.
            direction: One of outgoing, incoming, both.

        Returns:
            Subgraph of traversed nodes and edges.
        """
        if not self._driver:
            return {"nodes": [], "edges": []}

        rel_pattern = f":{relation}" if relation else ""
        if direction == "outgoing":
            path_pattern = f"(start)-[r{rel_pattern}*1..{max_depth}]->(end)"
        elif direction == "incoming":
            path_pattern = f"(start)<-[r{rel_pattern}*1..{max_depth}]-(end)"
        else:
            path_pattern = f"(start)-[r{rel_pattern}*1..{max_depth}]-(end)"

        cypher = f"""
        MATCH p = {path_pattern}
        WHERE start.node_id = $start_id
        UNWIND relationships(p) AS rel
        WITH DISTINCT startNode(rel) AS s, endNode(rel) AS e, type(rel) AS rtype
        RETURN s.node_id AS source, s.label AS source_label, s.type AS source_type,
               e.node_id AS target, e.label AS target_label, e.type AS target_type,
               rtype AS relation
        LIMIT 500
        """

        nodes_map: dict[str, dict[str, Any]] = {}
        edges = []

        async with self._driver.session(database=self._database) as session:
            result = await session.run(cypher, start_id=start_node)
            async for record in result:
                src_id = record["source"]
                tgt_id = record["target"]
                if src_id not in nodes_map:
                    nodes_map[src_id] = {"id": src_id, "label": record["source_label"], "type": record["source_type"]}
                if tgt_id not in nodes_map:
                    nodes_map[tgt_id] = {"id": tgt_id, "label": record["target_label"], "type": record["target_type"]}
                edges.append({"source": src_id, "target": tgt_id, "relation": record["relation"]})

        return {"nodes": list(nodes_map.values()), "edges": edges}

    async def get_stats(self) -> dict[str, Any]:
        """Return Neo4j index statistics."""
        if not self._driver:
            return {"mode": "mock", "node_count": 0, "edge_count": 0}

        async with self._driver.session(database=self._database) as session:
            node_result = await session.run("MATCH (n) RETURN count(n) AS cnt")
            node_record = await node_result.single()
            edge_result = await session.run("MATCH ()-[r]->() RETURN count(r) AS cnt")
            edge_record = await edge_result.single()

        return {
            "mode": "connected",
            "uri": self._uri,
            "node_count": node_record["cnt"] if node_record else 0,
            "edge_count": edge_record["cnt"] if edge_record else 0,
        }