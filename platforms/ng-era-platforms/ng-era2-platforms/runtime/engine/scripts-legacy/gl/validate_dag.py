#
# @ECO-governed
# @ECO-layer: gl-platform.gl-platform.governance
# @ECO-semantic: validate-dag
# @ECO-audit-trail: ../../engine/gl-platform.gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
GL DAG Validator
Validates DAG structure and dependencies
"""
# MNGA-002: Import organization needs review
import argparse
import sys
import yaml
from pathlib import Path
from typing import Dict, Optional
from collections import defaultdict, deque


def load_dag_file(dag_path: str) -> Optional[Dict]:
    """Load and parse DAG YAML file"""
    path = Path(dag_path)
    if not path.exists():
        print(f"  [✗] DAG file not found: {dag_path}")
        return None
    
    try:
        with open(path, 'r') as f:
            dag_data = yaml.safe_load(f)
        return dag_data
    except yaml.YAMLError as e:
        print(f"  [✗] Invalid YAML format: {e}")
        return None
    except Exception as e:
        print(f"  [✗] Error loading DAG file: {e}")
        return None


def validate_dag_structure(dag_path: str) -> bool:
    """Validate DAG structure"""
    dag_data = load_dag_file(dag_path)
    if dag_data is None:
        return False
    
    # Validate that dag_data is a dictionary
    if not isinstance(dag_data, dict):
        print("  [✗] DAG file must contain a dictionary at the top level")
        return False
    
    errors = []
    
    # Check required top-level fields
    required_fields = ['nodes', 'edges']
    for field in required_fields:
        if field not in dag_data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        for error in errors:
            print(f"  [✗] {error}")
        return False
    
    # Validate that nodes and edges are lists
    nodes = dag_data.get('nodes', [])
    edges = dag_data.get('edges', [])
    
    if not isinstance(nodes, list):
        print("  [✗] 'nodes' field must be a list")
        return False
    
    if not isinstance(edges, list):
        print("  [✗] 'edges' field must be a list")
        return False
    
    # Validate nodes
    if not nodes:
        print("  [✗] DAG must contain at least one node")
        return False
    
    # Check for duplicate node_ids
    node_ids = set()
    for node in nodes:
        if 'node_id' not in node:
            errors.append(f"Node missing 'node_id' field: {node}")
            continue
        
        node_id = node['node_id']
        if node_id in node_ids:
            errors.append(f"Duplicate node_id: {node_id}")
        node_ids.add(node_id)
    
    # Validate edges
    edges = dag_data.get('edges', [])
    for i, edge in enumerate(edges):
        if 'from' not in edge or 'to' not in edge:
            errors.append(f"Edge {i} missing 'from' or 'to' field")
            continue
        
        # Check that edge references valid nodes
        if edge['from'] not in node_ids:
            errors.append(f"Edge references non-existent node: {edge['from']}")
        if edge['to'] not in node_ids:
            errors.append(f"Edge references non-existent node: {edge['to']}")
    
    if errors:
        for error in errors:
            print(f"  [✗] {error}")
        return False
    
    print(f"  [✓] DAG structure validation passed ({len(nodes)} nodes, {len(edges)} edges)")
    return True


def validate_dag_cycles(dag_path: str) -> bool:
    """Validate no cycles in DAG using topological sort (Kahn's algorithm)"""
    dag_data = load_dag_file(dag_path)
    if dag_data is None:
        return False
    
    # Validate that dag_data is a dictionary
    if not isinstance(dag_data, dict):
        print("  [✗] DAG file must contain a dictionary at the top level")
        return False
    
    nodes = dag_data.get('nodes', [])
    edges = dag_data.get('edges', [])
    
    # Validate that nodes and edges are lists
    if not isinstance(nodes, list):
        print("  [✗] 'nodes' field must be a list")
        return False
    
    if not isinstance(edges, list):
        print("  [✗] 'edges' field must be a list")
        return False
    
    # Build adjacency list and in-degree count
    graph = defaultdict(list)
    in_degree = defaultdict(int)
    
    # Initialize all nodes with 0 in-degree
    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get('node_id')
        if node_id:
            in_degree[node_id] = 0
    
    # Build graph (only count solid edges, not feedback loops)
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        from_node = edge.get('from')
        to_node = edge.get('to')
        
        # Skip feedback loops (dashed edges) in cycle detection
        if edge.get('style') == 'dashed' or edge.get('type') == 'feedback_loop':
            continue
        
        if from_node and to_node:
            graph[from_node].append(to_node)
            in_degree[to_node] += 1
    
    # Kahn's algorithm for topological sort
    queue = deque()
    
    # Start with nodes that have no incoming edges
    for node_id, degree in in_degree.items():
        if degree == 0:
            queue.append(node_id)
    
    processed = []
    
    while queue:
        node = queue.popleft()
        processed.append(node)
        
        # Reduce in-degree for neighbors
        for neighbor in graph[node]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    # If we processed all nodes, there's no cycle
    total_nodes = len([n for n in nodes if n.get('node_id')])
    
    if len(processed) != total_nodes:
        # Find nodes involved in cycle
        unprocessed = set(in_degree.keys()) - set(processed)
        print(f"  [✗] Cycle detected! Nodes involved: {', '.join(unprocessed)}")
        return False
    
    print(f"  [✓] DAG cycle validation passed (no cycles detected)")
    return True
def main():
    parser = argparse.ArgumentParser(description='Validate GL DAG')
    parser.add_argument('--path', required=True, help='DAG path')
    args = parser.parse_args()
    print(f"GL DAG Validation for {args.path}:")
    all_passed = True
    if not validate_dag_structure(args.path):
        all_passed = False
    if not validate_dag_cycles(args.path):
        all_passed = False
    if all_passed:
        print("\\n[✓] DAG validation passed")
        sys.exit(0)
    else:
        print("\\n[✗] DAG validation failed")
        sys.exit(1)
if __name__ == "__main__":
    main()