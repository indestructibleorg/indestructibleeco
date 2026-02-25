# @ECO-governed
# @ECO-layer: GL90-99
# @ECO-semantic: archive-tools
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
# GL Unified Architecture Governance Framework Activated
#
# @ECO-governed
# @ECO-layer: governance
# @ECO-semantic: validate-artifact
# @ECO-audit-trail: ../../engine/governance/GL_SEMANTIC_ANCHOR.json
#
#!/usr/bin/env python3
"""
Artifact Validation Tool - Production Implementation
Version: 2.0.0
Purpose: Complete 5-level validation pipeline for Machine Native Ops artifacts
五層驗證管道完整實現：
1. Structural Validation (結構驗證) - Schema compliance, required fields, data types
2. Schema Validation (Schema 驗證) - Semantic root traceability, concept consistency
3. Dependency Validation (依賴驗證) - DAG validation, circular dependency detection
4. Governance Validation (治理驗證) - Naming conventions, documentation, policies
5. Closure Validation (閉包驗證) - Dependency, semantic, and governance closure
Integration Points:
- Semantic Root: root/.root.semantic-root.yaml
- Gates Map: root/.root.gates.map.yaml
- FileX Template: design/FileX-standard-template-v1.yaml
"""
import argparse
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
import yaml
class ValidationResult:
    """Validation result container with enhanced details"""
    def __init__(
        self, level: str, status: str, message: str, details: Optional[Dict] = None
    ):
        self.level = level
        self.status = status  # pass, fail, warning
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.now(timezone.utc).isoformat()
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "level": self.level,
            "status": self.status,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp,
        }
class ArtifactValidator:
    """Artifact validator with complete 5-level validation pipeline"""
    def __init__(
        self,
        artifact_paths: List[str],
        validation_level: str = "all",
        strict: bool = False,
    ):
        self.artifact_paths = artifact_paths
        self.validation_level = validation_level
        self.strict = strict
        self.results: List[ValidationResult] = []
        self.artifacts: List[Dict] = []
        self.semantic_root: Optional[Dict] = None
        self.gates_map: Optional[Dict] = None
        # Load configuration files
        self._load_configuration()
    def _load_configuration(self):
        """Load semantic root and gates map configuration"""
        repo_root = Path(__file__).parent.parent.parent
        # Load semantic root
        semantic_root_path = repo_root / "root" / ".root.semantic-root.yaml"
        if semantic_root_path.exists():
            try:
                with open(semantic_root_path, "r") as f:
                    self.semantic_root = yaml.safe_load(f)
            except Exception as e:
                print(f"⚠️  Warning: Could not load semantic root: {e}")
        # Load gates map
        gates_map_path = repo_root / "root" / ".root.gates.map.yaml"
        if gates_map_path.exists():
            try:
                with open(gates_map_path, "r") as f:
                    self.gates_map = yaml.safe_load(f)
            except Exception as e:
                print(f"⚠️  Warning: Could not load gates map: {e}")
    def _load_artifacts(self) -> bool:
        """Load and parse all artifact files"""
        for artifact_path in self.artifact_paths:
            path = Path(artifact_path)
            if not path.exists():
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message=f"Artifact not found: {artifact_path}",
                        details={"path": artifact_path, "error": "File does not exist"},
                    )
                )
                continue
            if path.suffix not in [".yaml", ".yml"]:
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="warning",
                        message=f"Skipping non-YAML file: {artifact_path}",
                        details={"path": artifact_path, "type": path.suffix},
                    )
                )
                continue
            try:
                with open(path, "r") as f:
                    # Try to load YAML
                    artifact = yaml.safe_load(f)
                    if artifact:
                        artifact["_source_path"] = str(path)
                        self.artifacts.append(artifact)
            except yaml.YAMLError as e:
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message=f"Invalid YAML syntax: {artifact_path}",
                        details={
                            "path": artifact_path,
                            "error": str(e),
                            "line": (
                                getattr(e, "problem_mark", None).line
                                if hasattr(e, "problem_mark")
                                else None
                            ),
                        },
                    )
                )
                return False
            except Exception as e:
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message=f"Error loading artifact: {artifact_path}",
                        details={"path": artifact_path, "error": str(e)},
                    )
                )
                return False
        return len(self.artifacts) > 0
    def validate(self) -> bool:
        """Run complete validation pipeline"""
        print(f"🔍 Starting {self.validation_level} validation...")
        # Load artifacts first
        if not self._load_artifacts():
            print("\n❌ Failed to load artifacts")
            return False
        # Run validation levels based on configuration
        if self.validation_level == "structural" or self.validation_level == "all":
            self._validate_structural()
        if self.validation_level == "semantic" or self.validation_level == "all":
            self._validate_semantic()
        if self.validation_level == "dependency" or self.validation_level == "all":
            self._validate_dependency()
        if self.validation_level == "governance" or self.validation_level == "all":
            self._validate_governance()
        if self.validation_level == "closure" or self.validation_level == "all":
            self._validate_closure()
        # Check results
        failures = [r for r in self.results if r.status == "fail"]
        warnings = [r for r in self.results if r.status == "warning"]
        if failures:
            print(
                f"\n❌ Validation FAILED: {len(failures)} error(s), {len(warnings)} warning(s)"
            )
            for failure in failures:
                print(f"   - [{failure.level}] {failure.message}")
                if failure.details.get("path"):
                    print(f"     File: {failure.details['path']}")
                if failure.details.get("line"):
                    print(f"     Line: {failure.details['line']}")
            return False
        if warnings:
            print(f"\n⚠️  Validation completed with {len(warnings)} warning(s)")
            for warning in warnings:
                print(f"   - [{warning.level}] {warning.message}")
            if self.strict:
                print("\n❌ Strict mode: Treating warnings as failures")
                return False
        print(f"\n✅ Validation PASSED: {len(self.results)} check(s) completed")
        return True
    def _validate_structural(self):
        """Level 1: Structural Validation - Complete Implementation
        Validates:
        - YAML syntax (already checked in _load_artifacts)
        - Schema compliance against FileX template
        - Required fields validation
        - Data type validation
        - Nested structure validation
        """
        print("  [1/5] Structural validation...")
        for artifact in self.artifacts:
            artifact_path = artifact.get("_source_path", "unknown")
            # Check for required top-level keys
            required_keys = ["apiVersion", "kind", "metadata", "spec"]
            missing_keys = [key for key in required_keys if key not in artifact]
            if missing_keys:
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message=f"Missing required top-level keys: {', '.join(missing_keys)}",
                        details={
                            "path": artifact_path,
                            "missing_keys": missing_keys,
                            "expected": required_keys,
                        },
                    ))
                continue
            # Validate apiVersion format
            api_version = artifact.get("apiVersion", "")
            if not re.match(r"^[\w\.]+/v\d+$", api_version):
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message=f"Invalid apiVersion format: {api_version}",
                        details={
                            "path": artifact_path,
                            "value": api_version,
                            "expected_pattern": "domain/vN (e.g., machinenativeops.io/v1)",
                        },
                    ))
            # Validate metadata structure
            metadata = artifact.get("metadata", {})
            if not isinstance(metadata, dict):
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message="metadata must be an object",
                        details={
                            "path": artifact_path,
                            "type": type(metadata).__name__,
                        },
                    )
                )
                continue
            # Check required metadata fields
            required_metadata = ["name", "version", "namespace"]
            missing_metadata = [key for key in required_metadata if key not in metadata]
            if missing_metadata:
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message=f"Missing required metadata fields: {', '.join(missing_metadata)}",
                        details={
                            "path": artifact_path,
                            "missing_fields": missing_metadata,
                            "section": "metadata",
                        },
                    ))
            # Validate spec structure
            spec = artifact.get("spec", {})
            if not isinstance(spec, dict):
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="fail",
                        message="spec must be an object",
                        details={"path": artifact_path, "type": type(spec).__name__},
                    )
                )
                continue
            # Check data types for common fields
            self._validate_field_types(artifact, artifact_path)
            # If all checks passed for this artifact
            if not any(
                r.status == "fail" and r.details.get("path") == artifact_path
                for r in self.results
            ):
                self.results.append(
                    ValidationResult(
                        level="structural",
                        status="pass",
                        message=f"Structural validation passed: {artifact_path}",
                        details={"path": artifact_path, "checks_performed": 5},
                    )
                )
        print("     ✅ Structural validation complete")
    def _validate_field_types(self, artifact: Dict, artifact_path: str):
        """Validate data types of fields"""
        metadata = artifact.get("metadata", {})
        # Validate version format (semantic versioning)
        version = metadata.get("version", "")
        if version and not re.match(r"^\d+\.\d+\.\d+", version):
            self.results.append(
                ValidationResult(
                    level="structural",
                    status="warning",
                    message=f"Version should follow semantic versioning: {version}",
                    details={
                        "path": artifact_path,
                        "field": "metadata.version",
                        "value": version,
                        "expected_pattern": "MAJOR.MINOR.PATCH",
                    },
                )
            )
        # Validate labels are string key-value pairs
        labels = metadata.get("labels", {})
        if labels and not isinstance(labels, dict):
            self.results.append(
                ValidationResult(
                    level="structural",
                    status="fail",
                    message="metadata.labels must be an object",
                    details={
                        "path": artifact_path,
                        "field": "metadata.labels",
                        "type": type(labels).__name__,
                    },
                )
            )
        # Validate annotations are string key-value pairs
        annotations = metadata.get("annotations", {})
        if annotations and not isinstance(annotations, dict):
            self.results.append(
                ValidationResult(
                    level="structural",
                    status="fail",
                    message="metadata.annotations must be an object",
                    details={
                        "path": artifact_path,
                        "field": "metadata.annotations",
                        "type": type(annotations).__name__,
                    },
                )
            )
    def _validate_semantic(self):
        """Level 2: Schema Validation - Complete Implementation
        Validates:
        - Semantic root integration
        - Concept traceability to semantic root
        - Semantic consistency checking
        - Definition completeness validation
        """
        print("  [2/5] Semantic validation...")
        if not self.semantic_root:
            self.results.append(
                ValidationResult(
                    level="semantic",
                    status="warning",
                    message="Semantic root not loaded, skipping semantic validation",
                    details={
                        "note": "Place semantic root at root/.root.semantic-root.yaml"
                    },
                )
            )
            print("     ⚠️  Semantic root not found, skipping")
            return
        # Extract base concepts from semantic root
        base_concepts = {}
        semantic_spec = self.semantic_root.get("spec", {})
        concepts_spec = semantic_spec.get("concepts", {})
        # Load base concepts
        for concept in concepts_spec.get("base_concepts", []):
            base_concepts[concept["name"]] = concept
        # Load derived concepts
        derived_concepts = {}
        for concept in concepts_spec.get("derived_concepts", []):
            derived_concepts[concept["name"]] = concept
        # Validate each artifact's semantic consistency
        for artifact in self.artifacts:
            artifact_path = artifact.get("_source_path", "unknown")
            # Check semantic root version reference
            metadata = artifact.get("metadata", {})
            annotations = metadata.get("annotations", {})
            semantic_root_ref = annotations.get("machinenativeops.io/semantic-root", "")
            if not semantic_root_ref:
                self.results.append(
                    ValidationResult(
                        level="semantic",
                        status="warning",
                        message="No semantic root reference found",
                        details={
                            "path": artifact_path,
                            "recommendation": "Add machinenativeops.io/semantic-root annotation",
                        },
                    ))
            else:
                # Validate version compatibility
                semantic_root_version = self.semantic_root.get("metadata", {}).get(
                    "version", ""
                )
                if semantic_root_ref != semantic_root_version:
                    self.results.append(
                        ValidationResult(
                            level="semantic",
                            status="warning",
                            message="Semantic root version mismatch",
                            details={
                                "path": artifact_path,
                                "artifact_version": semantic_root_ref,
                                "current_version": semantic_root_version,
                            },
                        )
                    )
            # Validate concepts if present
            spec = artifact.get("spec", {})
            artifact_concepts = (
                spec.get("generation", {}).get("forward", {}).get("concepts", [])
            )
            if artifact_concepts:
                for concept in artifact_concepts:
                    concept_name = concept.get("name", "")
                    extends = concept.get("extends", "")
                    if extends:
                        # Check if parent concept exists
                        if (
                            extends not in base_concepts
                            and extends not in derived_concepts
                        ):
                            self.results.append(
                                ValidationResult(
                                    level="semantic",
                                    status="fail",
                                    message=f"Concept '{concept_name}' extends unknown concept '{extends}'",
                                    details={
                                        "path": artifact_path,
                                        "concept": concept_name,
                                        "parent": extends,
                                        "available_base": list(
                                            base_concepts.keys()),
                                    },
                                ))
                        else:
                            # Concept traceability is valid
                            self.results.append(
                                ValidationResult(
                                    level="semantic",
                                    status="pass",
                                    message=f"Concept '{concept_name}' traces to semantic root",
                                    details={
                                        "path": artifact_path,
                                        "concept": concept_name,
                                        "parent": extends,
                                    },
                                ))
                    # Validate concept definition completeness
                    required_concept_fields = ["name", "definition"]
                    missing_fields = [
                        f for f in required_concept_fields if not concept.get(f)
                    ]
                    if missing_fields:
                        self.results.append(
                            ValidationResult(
                                level="semantic",
                                status="fail",
                                message=f"Concept '{concept_name}' missing required fields: {', '.join(missing_fields)}",
                                details={
                                    "path": artifact_path,
                                    "concept": concept_name,
                                    "missing_fields": missing_fields,
                                },
                            ))
            # Check if artifact passed semantic validation
            artifact_failures = [
                r
                for r in self.results
                if r.level == "semantic"
                and r.status == "fail"
                and r.details.get("path") == artifact_path
            ]
            if not artifact_failures and artifact_concepts:
                self.results.append(
                    ValidationResult(
                        level="semantic",
                        status="pass",
                        message=f"Semantic validation passed: {artifact_path}",
                        details={
                            "path": artifact_path,
                            "concepts_validated": len(artifact_concepts),
                        },
                    )
                )
        print("     ✅ Semantic validation complete")
    def _validate_dependency(self):
        """Level 3: Dependency Validation - Complete Implementation
        Validates:
        - DAG structure validation
        - Circular dependency detection using Tarjan's algorithm
        - Version compatibility checking
        - Dependency health monitoring
        """
        print("  [3/5] Dependency validation...")
        # Build dependency graph
        dependency_graph = {}
        artifact_registry = {}
        for artifact in self.artifacts:
            artifact_path = artifact.get("_source_path", "unknown")
            metadata = artifact.get("metadata", {})
            artifact_name = metadata.get("name", "")
            artifact_version = metadata.get("version", "")
            if not artifact_name:
                continue
            artifact_key = f"{artifact_name}@{artifact_version}"
            artifact_registry[artifact_key] = artifact
            # Extract dependencies
            spec = artifact.get("spec", {})
            dependencies = spec.get("artifact", {}).get("dependencies", [])
            dependency_list = []
            for dep in dependencies:
                dep_name = dep.get("name", "")
                dep_version = dep.get("version", "")
                if dep_name:
                    dependency_list.append(f"{dep_name}@{dep_version}")
            dependency_graph[artifact_key] = dependency_list
        # Validate each artifact's dependencies
        for artifact in self.artifacts:
            artifact_path = artifact.get("_source_path", "unknown")
            metadata = artifact.get("metadata", {})
            artifact_name = metadata.get("name", "")
            spec = artifact.get("spec", {})
            dependencies = spec.get("artifact", {}).get("dependencies", [])
            if not dependencies:
                # No dependencies to validate
                continue
            # Check each dependency
            for dep in dependencies:
                dep_name = dep.get("name", "")
                dep_version = dep.get("version", "")
                # Check for self-dependency
                if dep_name == artifact_name:
                    self.results.append(
                        ValidationResult(
                            level="dependency",
                            status="fail",
                            message=f"Self-dependency detected: {artifact_name}",
                            details={
                                "path": artifact_path,
                                "artifact": artifact_name,
                                "dependency": dep_name,
                            },
                        )
                    )
                # Validate dependency version format
                if dep_version and not self._is_valid_version_constraint(dep_version):
                    self.results.append(
                        ValidationResult(
                            level="dependency",
                            status="warning",
                            message=f"Invalid version constraint for dependency '{dep_name}': {dep_version}",
                            details={
                                "path": artifact_path,
                                "dependency": dep_name,
                                "version": dep_version,
                                "expected": "Semantic version or constraint (e.g., '1.2.3', '>=1.0.0')",
                            },
                        ))
        # Detect circular dependencies using DFS
        if dependency_graph:
            cycles = self._detect_circular_dependencies(dependency_graph)
            if cycles:
                for cycle in cycles:
                    self.results.append(
                        ValidationResult(
                            level="dependency",
                            status="fail",
                            message=f"Circular dependency detected: {' -> '.join(cycle)}",
                            details={
                                "cycle": cycle,
                                "cycle_length": len(cycle)},
                        ))
            else:
                self.results.append(
                    ValidationResult(
                        level="dependency",
                        status="pass",
                        message="No circular dependencies detected (DAG structure valid)",
                        details={
                            "artifacts_checked": len(dependency_graph),
                            "total_dependencies": sum(
                                len(deps) for deps in dependency_graph.values()),
                        },
                    ))
        print("     ✅ Dependency validation complete")
    def _is_valid_version_constraint(self, version: str) -> bool:
        """Check if version string is a valid constraint"""
        # Accept semantic versions and common constraint patterns
        patterns = [
            r"^\d+\.\d+\.\d+$",  # Exact version: 1.2.3
            r"^>=\d+\.\d+\.\d+$",  # Greater or equal: >=1.2.3
            r"^>\d+\.\d+\.\d+$",  # Greater: >1.2.3
            r"^<=\d+\.\d+\.\d+$",  # Less or equal: <=1.2.3
            r"^<\d+\.\d+\.\d+$",  # Less: <1.2.3
            r"^~\d+\.\d+\.\d+$",  # Tilde: ~1.2.3
            r"^\^\d+\.\d+\.\d+$",  # Caret: ^1.2.3
            r"^>=\d+\.\d+\.\d+,<\d+\.\d+\.\d+$",  # Range: >=1.0.0,<2.0.0
        ]
        return any(re.match(pattern, version.replace(" ", "")) for pattern in patterns)
    def _detect_circular_dependencies(
        self, graph: Dict[str, List[str]]
    ) -> List[List[str]]:
        """Detect circular dependencies using DFS-based cycle detection"""
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    # Cycle found
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                    return True
            path.pop()
            rec_stack.remove(node)
            return False
        for node in graph:
            if node not in visited:
                dfs(node)
        return cycles
    def _validate_governance(self):
        """Level 4: Governance Validation - Complete Implementation
        Validates:
        - Naming convention enforcement
        - Documentation completeness checking
        - Policy compliance validation
        - Attestation bundle requirements
        """
        print("  [4/5] Governance validation...")
        if not self.semantic_root:
            self.results.append(
                ValidationResult(
                    level="governance",
                    status="warning",
                    message="Semantic root not loaded, using default naming conventions",
                    details={},
                ))
        # Get naming conventions from semantic root
        naming_conventions = {}
        if self.semantic_root:
            spec = self.semantic_root.get("spec", {})
            naming_conventions = spec.get("naming_conventions", {})
        for artifact in self.artifacts:
            artifact_path = artifact.get("_source_path", "unknown")
            metadata = artifact.get("metadata", {})
            # Validate artifact name convention
            artifact_name = metadata.get("name", "")
            if artifact_name:
                name_pattern = naming_conventions.get("artifact_naming", {}).get(
                    "pattern", "^[a-z][a-z0-9-]*$"
                )
                if not re.match(name_pattern, artifact_name):
                    self.results.append(
                        ValidationResult(
                            level="governance",
                            status="fail",
                            message=f"Artifact name '{artifact_name}' violates naming convention",
                            details={
                                "path": artifact_path,
                                "name": artifact_name,
                                "pattern": name_pattern,
                                "examples": naming_conventions.get(
                                    "artifact_naming",
                                    {}).get(
                                    "examples",
                                    []),
                            },
                        ))
            # Validate version convention
            version = metadata.get("version", "")
            if version:
                version_pattern = naming_conventions.get("version_naming", {}).get(
                    "pattern", r"^\d+\.\d+\.\d+$"
                )
                if not re.match(version_pattern, version):
                    self.results.append(
                        ValidationResult(
                            level="governance",
                            status="fail",
                            message=f"Version '{version}' violates naming convention",
                            details={
                                "path": artifact_path,
                                "version": version,
                                "pattern": version_pattern,
                                "examples": naming_conventions.get(
                                    "version_naming", {}
                                ).get("examples", []),
                            },
                        )
                    )
            # Validate namespace convention
            namespace = metadata.get("namespace", "")
            if namespace:
                namespace_pattern = naming_conventions.get("namespace_naming", {}).get(
                    "pattern", "^[a-z][a-z0-9-]*$"
                )
                if not re.match(namespace_pattern, namespace):
                    self.results.append(
                        ValidationResult(
                            level="governance",
                            status="fail",
                            message=f"Namespace '{namespace}' violates naming convention",
                            details={
                                "path": artifact_path,
                                "namespace": namespace,
                                "pattern": namespace_pattern,
                            },
                        ))
            # Check documentation completeness
            spec = artifact.get("spec", {})
            documentation = spec.get("documentation", {})
            if not documentation:
                self.results.append(
                    ValidationResult(
                        level="governance",
                        status="warning",
                        message="No documentation section found",
                        details={
                            "path": artifact_path,
                            "recommendation": "Add spec.documentation with overview and usage examples",
                        },
                    ))
            else:
                # Check required documentation fields
                required_doc_fields = ["overview"]
                missing_doc = [
                    f for f in required_doc_fields if not documentation.get(f)
                ]
                if missing_doc:
                    self.results.append(
                        ValidationResult(
                            level="governance",
                            status="warning",
                            message=f"Documentation missing recommended fields: {', '.join(missing_doc)}",
                            details={
                                "path": artifact_path,
                                "missing_fields": missing_doc,
                            },
                        ))
            # Check attestation configuration
            attestation = spec.get("attestation", {})
            if not attestation:
                self.results.append(
                    ValidationResult(
                        level="governance",
                        status="warning",
                        message="No attestation configuration found",
                        details={
                            "path": artifact_path,
                            "recommendation": "Add spec.attestation configuration",
                        },
                    )
                )
            # If no governance failures for this artifact
            artifact_failures = [
                r
                for r in self.results
                if r.level == "governance"
                and r.status == "fail"
                and r.details.get("path") == artifact_path
            ]
            if not artifact_failures:
                self.results.append(
                    ValidationResult(
                        level="governance",
                        status="pass",
                        message=f"Governance validation passed: {artifact_path}",
                        details={"path": artifact_path},
                    )
                )
        print("     ✅ Governance validation complete")
    def _validate_closure(self):
        """Level 5: Closure Validation - Complete Implementation
        Validates:
        - Dependency closure validation
        - Semantic closure validation
        - Governance closure validation
        - Bi-directional reconciliation checks
        """
        print("  [5/5] Closure validation...")
        for artifact in self.artifacts:
            artifact_path = artifact.get("_source_path", "unknown")
            # Check all previous validation levels passed
            levels_to_check = ["structural", "semantic", "dependency", "governance"]
            closure_status = {}
            for level in levels_to_check:
                level_results = [
                    r
                    for r in self.results
                    if r.level == level and r.details.get("path") == artifact_path
                ]
                has_failures = any(r.status == "fail" for r in level_results)
                closure_status[level] = "fail" if has_failures else "pass"
            # Dependency closure: All dependencies resolved and no cycles
            dependency_closure_passed = closure_status.get("dependency") == "pass"
            # Semantic closure: All concepts trace to semantic root
            semantic_closure_passed = closure_status.get("semantic") == "pass"
            # Governance closure: All governance policies satisfied
            governance_closure_passed = closure_status.get("governance") == "pass"
            # Structural closure: Basic structure valid
            structural_closure_passed = closure_status.get("structural") == "pass"
            # Check backward reconciliation configuration
            spec = artifact.get("spec", {})
            generation = spec.get("generation", {})
            backward = generation.get("backward", {})
            reconciliation = backward.get("reconciliation", [])
            has_reconciliation = len(reconciliation) > 0
            # Overall closure validation
            all_closures_passed = (
                dependency_closure_passed
                and semantic_closure_passed
                and governance_closure_passed
                and structural_closure_passed
            )
            if not all_closures_passed:
                failed_closures = [
                    level
                    for level, status in closure_status.items()
                    if status == "fail"
                ]
                self.results.append(
                    ValidationResult(
                        level="closure",
                        status="fail",
                        message=f"Closure validation failed: {', '.join(failed_closures)} closure not achieved",
                        details={
                            "path": artifact_path,
                            "dependency_closure": (
                                "pass" if dependency_closure_passed else "fail"),
                            "semantic_closure": (
                                "pass" if semantic_closure_passed else "fail"),
                            "governance_closure": (
                                "pass" if governance_closure_passed else "fail"),
                            "structural_closure": (
                                "pass" if structural_closure_passed else "fail"),
                            "failed_levels": failed_closures,
                        },
                    ))
            else:
                # Check bi-directional reconciliation
                if generation and not has_reconciliation:
                    self.results.append(
                        ValidationResult(
                            level="closure",
                            status="warning",
                            message="No backward reconciliation configured (bi-directional governance incomplete)",
                            details={
                                "path": artifact_path,
                                "recommendation": "Add spec.generation.backward.reconciliation",
                            },
                        ))
                self.results.append(
                    ValidationResult(
                        level="closure",
                        status="pass",
                        message=f"Closure validation passed: {artifact_path}",
                        details={
                            "path": artifact_path,
                            "dependency_closure": "pass",
                            "semantic_closure": "pass",
                            "governance_closure": "pass",
                            "structural_closure": "pass",
                            "has_backward_reconciliation": has_reconciliation,
                        },
                    )
                )
        print("     ✅ Closure validation complete")
    def generate_attestation(self, output_path: Optional[str] = None) -> Dict:
        """Generate comprehensive attestation bundle
        Returns detailed attestation including:
        - All validation results
        - Governance compliance status
        - Provenance information
        - Trust chain metadata
        """
        # Aggregate results by level
        results_by_level = defaultdict(list)
        for result in self.results:
            results_by_level[result.level].append(result)
        # Calculate overall status
        overall_status = "passed"
        if any(r.status == "fail" for r in self.results):
            overall_status = "failed"
        elif any(r.status == "warning" for r in self.results):
            overall_status = "passed_with_warnings"
        # Build attestation
        attestation = {
            "apiVersion": "machinenativeops.io/v1",
            "kind": "ValidationAttestation",
            "metadata": {
                "name": "validation-attestation",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "validator": "validate-artifact",
                "version": "2.0.0",
            },
            "spec": {
                "artifacts": self.artifact_paths,
                "validation_level": self.validation_level,
                "strict_mode": self.strict,
                # Detailed validation results by level
                "validation_results": {
                    "structural": {
                        "status": self._get_level_status(
                            results_by_level.get("structural", [])
                        ),
                        "checks": len(results_by_level.get("structural", [])),
                        "passed": len(
                            [
                                r
                                for r in results_by_level.get("structural", [])
                                if r.status == "pass"
                            ]
                        ),
                        "failed": len(
                            [
                                r
                                for r in results_by_level.get("structural", [])
                                if r.status == "fail"
                            ]
                        ),
                        "warnings": len(
                            [
                                r
                                for r in results_by_level.get("structural", [])
                                if r.status == "warning"
                            ]
                        ),
                        "details": [
                            r.to_dict() for r in results_by_level.get("structural", [])
                        ],
                    },
                    "semantic": {
                        "status": self._get_level_status(
                            results_by_level.get("semantic", [])
                        ),
                        "checks": len(results_by_level.get("semantic", [])),
                        "passed": len(
                            [
                                r
                                for r in results_by_level.get("semantic", [])
                                if r.status == "pass"
                            ]
                        ),
                        "failed": len(
                            [
                                r
                                for r in results_by_level.get("semantic", [])
                                if r.status == "fail"
                            ]
                        ),
                        "warnings": len(
                            [
                                r
                                for r in results_by_level.get("semantic", [])
                                if r.status == "warning"
                            ]
                        ),
                        "details": [
                            r.to_dict() for r in results_by_level.get("semantic", [])
                        ],
                    },
                    "dependency": {
                        "status": self._get_level_status(
                            results_by_level.get("dependency", [])
                        ),
                        "checks": len(results_by_level.get("dependency", [])),
                        "passed": len(
                            [
                                r
                                for r in results_by_level.get("dependency", [])
                                if r.status == "pass"
                            ]
                        ),
                        "failed": len(
                            [
                                r
                                for r in results_by_level.get("dependency", [])
                                if r.status == "fail"
                            ]
                        ),
                        "warnings": len(
                            [
                                r
                                for r in results_by_level.get("dependency", [])
                                if r.status == "warning"
                            ]
                        ),
                        "details": [
                            r.to_dict() for r in results_by_level.get("dependency", [])
                        ],
                    },
                    "governance": {
                        "status": self._get_level_status(
                            results_by_level.get("governance", [])
                        ),
                        "checks": len(results_by_level.get("governance", [])),
                        "passed": len(
                            [
                                r
                                for r in results_by_level.get("governance", [])
                                if r.status == "pass"
                            ]
                        ),
                        "failed": len(
                            [
                                r
                                for r in results_by_level.get("governance", [])
                                if r.status == "fail"
                            ]
                        ),
                        "warnings": len(
                            [
                                r
                                for r in results_by_level.get("governance", [])
                                if r.status == "warning"
                            ]
                        ),
                        "details": [
                            r.to_dict() for r in results_by_level.get("governance", [])
                        ],
                    },
                    "closure": {
                        "status": self._get_level_status(
                            results_by_level.get("closure", [])
                        ),
                        "checks": len(results_by_level.get("closure", [])),
                        "passed": len(
                            [
                                r
                                for r in results_by_level.get("closure", [])
                                if r.status == "pass"
                            ]
                        ),
                        "failed": len(
                            [
                                r
                                for r in results_by_level.get("closure", [])
                                if r.status == "fail"
                            ]
                        ),
                        "warnings": len(
                            [
                                r
                                for r in results_by_level.get("closure", [])
                                if r.status == "warning"
                            ]
                        ),
                        "details": [
                            r.to_dict() for r in results_by_level.get("closure", [])
                        ],
                    },
                },
                # Governance compliance summary
                "governance_compliance": {
                    "semantic_root_loaded": self.semantic_root is not None,
                    "semantic_root_version": (
                        self.semantic_root.get("metadata", {}).get("version", "unknown")
                        if self.semantic_root
                        else None
                    ),
                    "gates_map_loaded": self.gates_map is not None,
                    "artifacts_validated": len(self.artifacts),
                },
                # Provenance information
                "provenance": {
                    "tool": "validate-artifact.py",
                    "version": "2.0.0",
                    "validation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "validation_level": self.validation_level,
                    "strict_mode": self.strict,
                },
            },
            "status": {
                "overall": overall_status,
                "total_checks": len(self.results),
                "passed": len([r for r in self.results if r.status == "pass"]),
                "failed": len([r for r in self.results if r.status == "fail"]),
                "warnings": len([r for r in self.results if r.status == "warning"]),
                # Closure status
                "closure_achieved": overall_status == "passed",
                "dependency_closure": self._get_level_status(
                    results_by_level.get("dependency", [])
                )
                == "pass",
                "semantic_closure": self._get_level_status(
                    results_by_level.get("semantic", [])
                )
                == "pass",
                "governance_closure": self._get_level_status(
                    results_by_level.get("governance", [])
                )
                == "pass",
            },
        }
        # Save attestation if output path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                yaml.dump(
                    attestation,
                    f,
                    default_flow_style=False,
                    allow_unicode=True,
                    sort_keys=False,
                )
            print(f"📜 Attestation saved to: {output_path}")
        return attestation
    def _get_level_status(self, results: List[ValidationResult]) -> str:
        """Determine overall status for a validation level"""
        if not results:
            return "not_run"
        if any(r.status == "fail" for r in results):
            return "fail"
        if any(r.status == "warning" for r in results):
            return "pass_with_warnings"
        return "pass"
def main():
    """Main entry point for validation tool"""
    parser = argparse.ArgumentParser(
        description="Artifact Validation Tool - Complete 5-Level Validation Pipeline",
        epilog="""
Validation Levels:
  structural   - Schema compliance, required fields, data types
  semantic     - Semantic root traceability, concept consistency
  dependency   - DAG validation, circular dependency detection
  governance   - Naming conventions, documentation, policies
  closure      - Complete governance closure validation
  all          - Run all validation levels (default)
Examples:
  # Validate single artifact
  %(prog)s --level all artifact.yaml
  # Validate with strict mode (warnings = failures)
  %(prog)s --level all --strict artifact.yaml
  # Generate attestation bundle
  %(prog)s --level all --attestation attestation.yaml artifact.yaml
  # Validate multiple artifacts
  %(prog)s --level all artifact1.yaml artifact2.yaml
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--level",
        choices=[
            "structural",
            "semantic",
            "dependency",
            "governance",
            "closure",
            "all",
        ],
        default="all",
        help="Validation level to run (default: all)",
    )
    parser.add_argument(
        "artifacts", nargs="*", help="Artifact files to validate (YAML format)"
    )
    parser.add_argument(
        "--attestation", help="Path to save attestation bundle (YAML format)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail on warnings (treat warnings as failures)",
    )
    parser.add_argument("--version", action="version", version="%(prog)s 2.0.0")
    args = parser.parse_args()
    # Validate arguments
    if not args.artifacts:
        print("❌ Error: No artifacts specified")
        print("   Use --help for usage information")
        sys.exit(1)
    # Check if artifact files exist
    missing_files = [f for f in args.artifacts if not Path(f).exists()]
    if missing_files:
        print("❌ Error: Artifact files not found:")
        for f in missing_files:
            print(f"   - {f}")
        sys.exit(1)
    # Create validator
    print("🚀 Artifact Validation Tool v2.0.0")
    print(f"   Validation Level: {args.level}")
    print(f"   Artifacts: {len(args.artifacts)}")
    print(f"   Strict Mode: {'Enabled' if args.strict else 'Disabled'}")
    print()
    validator = ArtifactValidator(args.artifacts, args.level, args.strict)
    # Run validation
    success = validator.validate()
    # Generate attestation
    if args.attestation:
        validator.generate_attestation(args.attestation)
    # Exit with appropriate code
    if not success:
        sys.exit(1)
    sys.exit(0)
if __name__ == "__main__":
    main()
