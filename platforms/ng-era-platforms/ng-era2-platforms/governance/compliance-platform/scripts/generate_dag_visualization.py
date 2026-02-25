#!/usr/bin/env python3
#
# @ECO-governed
# @ECO-layer: GL30-49
# @ECO-semantic: generate-dag-visualization
# @ECO-audit-trail: ../../engine/gl-platform.governance/GL_SEMANTIC_ANCHOR.json
#
"""
Module Dependency DAG Visualization Generator
Generates Mermaid diagram and DOT graph of module dependencies
"""
# MNGA-002: Import organization needs review
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Set


def load_module_registry() -> Dict:
    """Load the module registry.

    Returns:
        Parsed registry dictionary.

    Raises:
        SystemExit: If the registry file is missing, unreadable, or contains invalid YAML.
    """
    registry_path = Path("controlplane/baseline/modules/REGISTRY.yaml")
    try:
        with registry_path.open('r', encoding='utf-8') as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        print(
            f"Error: Module registry file not found at '{registry_path}'.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except yaml.YAMLError as exc:
        print(
            f"Error: Failed to parse YAML module registry at '{registry_path}': {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    except OSError as exc:
        print(
            f"Error: Could not read module registry file at '{registry_path}': {exc}",
            file=sys.stderr,
        )
        raise SystemExit(1)
    if not isinstance(data, dict):
        print(
            f"Error: Module registry at '{registry_path}' must be a YAML mapping at the root.",
            file=sys.stderr,
        )
        raise SystemExit(1)
    return data


def build_dependency_graph(registry: Dict) -> Dict[str, List[str]]:
    """Build dependency graph from registry"""
    modules = registry.get('modules', [])
    graph = {}

    for module in modules:
        module_id = module.get('module_id')
        if module_id is None:
            continue
        dependencies = module.get('dependencies', [])
        # Filter out 'none' dependencies
        deps = [d for d in dependencies if d != 'none']
        graph[module_id] = deps

    return graph


def detect_cycles(graph: Dict[str, List[str]]) -> List[List[str]]:
    """Detect cycles in the dependency graph"""
    cycles = []
    def dfs(node: str, visited: Set[str], path: List[str]):
        if node in path:
            # Found a cycle
            cycle_start = path.index(node)
            cycle = path[cycle_start:] + [node]
            cycles.append(cycle)
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        for neighbor in graph.get(node, []):
            dfs(neighbor, visited, path.copy())
    visited = set()
    for node in graph:
        if node not in visited:
            dfs(node, visited, [])
    return cycles


def calculate_depths(graph: Dict[str, List[str]]) -> Dict[str, int]:
    """Calculate depth of each module in dependency tree"""
    depths = {}
    def get_depth(node: str, visited: Set[str]) -> int:
        if node in depths:
            return depths[node]
        if node in visited:
            # Cycle detected, return 0
            return 0
        visited.add(node)
        deps = graph.get(node, [])
        if not deps:
            depth = 0
        else:
            depth = 1 + max(get_depth(d, visited.copy()) for d in deps)
        depths[node] = depth
        return depth
    for node in graph:
        get_depth(node, set())
    return depths


def generate_mermaid_diagram(graph: Dict[str, List[str]], registry: Dict) -> str:
    """Generate Mermaid flowchart diagram"""
    modules = {m['module_id']: m for m in registry.get('modules', []) if 'module_id' in m}
    mermaid = """```mermaid
graph TD
    %% Module Dependency Graph
"""
    # Define nodes with styling based on autonomy level
    for module_id in graph:
        module = modules.get(module_id, {})
        autonomy = module.get('autonomy_level', 'unknown')
        status = module.get('status', 'unknown')
        # Choose style based on status
        if status == 'active':
            style_class = 'active'
        elif status == 'in-development':
            style_class = 'dev'
        else:
            style_class = 'planned'
        # Create node label
        label = f"{module_id}\\n{autonomy}"
        mermaid += f"    {module_id}[\"{label}\"]:::{style_class}\n"
    mermaid += "\n"
    # Define edges
    for module_id, deps in graph.items():
        for dep in deps:
            mermaid += f"    {dep} --> {module_id}\n"
    # Define styles
    mermaid += """
    %% Styles
    classDef active fill:#90EE90,stroke:#228B22,stroke-width:2px
    classDef dev fill:#FFD700,stroke:#FFA500,stroke-width:2px
    classDef planned fill:#E0E0E0,stroke:#808080,stroke-width:2px
```
"""
    return mermaid


def generate_dot_graph(graph: Dict[str, List[str]], registry: Dict) -> str:
    """Generate DOT graph for Graphviz"""
    modules = {m['module_id']: m for m in registry.get('modules', []) if 'module_id' in m}
    dot = """digraph ModuleDependencies {
    rankdir=BT;
    node [shape=box, style=rounded];
"""
    # Define nodes
    for module_id in graph:
        module = modules.get(module_id, {})
        autonomy = module.get('autonomy_level', 'unknown')
        status = module.get('status', 'unknown')
        # Choose color based on status
        if status == 'active':
            color = '#90EE90'
        elif status == 'in-development':
            color = '#FFD700'
        else:
            color = '#E0E0E0'
        label = f"{module_id}\\n{autonomy}"
        dot += f'    "{module_id}" [label="{label}", fillcolor="{color}", style=filled];\n'
    dot += "\n"
    # Define edges
    for module_id, deps in graph.items():
        for dep in deps:
            dot += f'    "{dep}" -> "{module_id}";\n'
    dot += "}\n"
    return dot


def generate_ascii_tree(graph: Dict[str, List[str]], registry: Dict) -> str:
    """Generate ASCII tree representation"""
    modules = {m['module_id']: m for m in registry.get('modules', []) if 'module_id' in m}
    depths = calculate_depths(graph)
    # Sort modules by depth
    sorted_modules = sorted(graph.keys(), key=lambda x: depths.get(x, 0))
    tree = "Module Dependency Tree (Bottom-Up)\n"
    tree += "=" * 60 + "\n\n"
    for module_id in sorted_modules:
        depth = depths.get(module_id, 0)
        module = modules.get(module_id, {})
        autonomy = module.get('autonomy_level', 'unknown')
        status = module.get('status', 'unknown')
        indent = "  " * depth
        status_emoji = {
            'active': '🟢',
            'in-development': '🟡',
            'planned': '⚪'
        }.get(status, '❓')
        tree += f"{indent}├─ {status_emoji} {module_id} ({autonomy})\n"
        # Show dependencies
        deps = graph.get(module_id, [])
        if deps:
            for i, dep in enumerate(deps):
                is_last = i == len(deps) - 1
                prefix = "└─" if is_last else "├─"
                tree += f"{indent}│  {prefix} depends on: {dep}\n"
    return tree


def generate_statistics(graph: Dict[str, List[str]], registry: Dict) -> str:
    """Generate dependency statistics"""
    depths = calculate_depths(graph)
    cycles = detect_cycles(graph)
    stats = "Dependency Statistics\n"
    stats += "=" * 60 + "\n\n"
    stats += f"Total Modules: {len(graph)}\n"
    stats += f"Total Dependencies: {sum(len(deps) for deps in graph.values())}\n"
    stats += f"Maximum Depth: {max(depths.values()) if depths else 0}\n"
    stats += f"Cycles Detected: {len(cycles)}\n\n"
    # Modules with no dependencies (leaf nodes)
    leaf_modules = [m for m, deps in graph.items() if not deps]
    stats += f"Leaf Modules (no dependencies): {len(leaf_modules)}\n"
    for module in leaf_modules:
        stats += f"  - {module}\n"
    stats += "\n"
    # Modules with most dependencies
    most_deps = sorted(graph.items(), key=lambda x: len(x[1]), reverse=True)[:3]
    stats += "Modules with Most Dependencies:\n"
    for module, deps in most_deps:
        stats += f"  - {module}: {len(deps)} dependencies\n"
    stats += "\n"
    # Module depth distribution
    stats += "Depth Distribution:\n"
    depth_counts = {}
    for depth in depths.values():
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    for depth in sorted(depth_counts.keys()):
        count = depth_counts[depth]
        bar = "█" * count
        stats += f"  Level {depth}: {count} modules {bar}\n"
    if cycles:
        stats += "\n⚠️  WARNING: Circular Dependencies Detected!\n"
        for i, cycle in enumerate(cycles, 1):
            stats += f"  Cycle {i}: {' -> '.join(cycle)}\n"
    return stats


def generate_visualization(output_dir: str = "docs/dag-visualization"):
    """Generate all visualization formats"""
    # Load data
    registry = load_module_registry()
    graph = build_dependency_graph(registry)
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    # Generate main documentation
    from datetime import datetime
    doc = f"""# Module Dependency DAG Visualization
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}  
**Purpose**: Visualize module dependencies and gl-platform.governance structure
---
## 📊 Dependency Graph (Mermaid)
{generate_mermaid_diagram(graph, registry)}
**Legend**:
- 🟢 Green: Active modules
- 🟡 Yellow: In development
- ⚪ Gray: Planned modules
- Arrows point from dependency to dependent (bottom-up)
---
## 🌳 ASCII Tree View
```
{generate_ascii_tree(graph, registry)}
```
---
## 📈 Statistics
{generate_statistics(graph, registry)}
---
## 🔍 Detailed Dependency Matrix
| Module | Dependencies | Dependents | Depth |
|--------|--------------|------------|-------|
"""
    # Calculate reverse dependencies (dependents)
    dependents = {m: [] for m in graph}
    for module, deps in graph.items():
        for dep in deps:
            if dep in dependents:
                dependents[dep].append(module)
    depths = calculate_depths(graph)
    for module in sorted(graph.keys()):
        deps = graph.get(module, [])
        dept_list = dependents.get(module, [])
        depth = depths.get(module, 0)
        deps_str = ', '.join(deps) if deps else 'none'
        dept_str = ', '.join(dept_list) if dept_list else 'none'
        doc += f"| {module} | {deps_str} | {dept_str} | {depth} |\n"
    doc += """
---
## 🔗 Export Formats
This visualization is available in multiple formats:
1. **Mermaid Diagram** (embedded above) - Render in GitHub, GitLab, or Mermaid Live Editor
2. **DOT Graph** (`module-dependencies.dot`) - Use with Graphviz
3. **ASCII Tree** (embedded above) - Plain text representation
4. **JSON Data** (`module-dependencies.json`) - Machine-readable format
### Using Graphviz
To generate PNG from DOT file:
```bash
dot -Tpng docs/dag-visualization/module-dependencies.dot -o module-dependencies.png
```
### Using Mermaid CLI
```bash
mmdc -i docs/DAG_VISUALIZATION.md -o dag-visualization.png
```
---
## 📚 Related Documentation
- [Module Registry](../../controlplane/baseline/modules/REGISTRY.yaml)
- [Integration Guide](../PHASE1_INTEGRATION_GUIDE.md)
- [Governance Dashboard](../LANGUAGE_GOVERNANCE_DASHBOARD.md)
---
*This visualization is automatically generated from the module registry.*
"""
    # Write main documentation
    with open(output_path / "DAG_VISUALIZATION.md", 'w') as f:
        f.write(doc)
    print(f"✅ Generated: {output_path}/DAG_VISUALIZATION.md")
    # Write DOT file
    with open(output_path / "module-dependencies.dot", 'w') as f:
        f.write(generate_dot_graph(graph, registry))
    print(f"✅ Generated: {output_path}/module-dependencies.dot")
    # Write JSON data
    import json
    json_data = {
        'graph': graph,
        'depths': depths,
        'cycles': detect_cycles(graph),
        'statistics': {
            'total_modules': len(graph),
            'total_dependencies': sum(len(deps) for deps in graph.values()),
            'max_depth': max(depths.values()) if depths else 0
        }
    }
    with open(output_path / "module-dependencies.json", 'w') as f:
        json.dump(json_data, f, indent=2)
    print(f"✅ Generated: {output_path}/module-dependencies.json")

    print(f"\n✅ All DAG visualizations generated in: {output_dir}")


if __name__ == "__main__":
    generate_visualization()
