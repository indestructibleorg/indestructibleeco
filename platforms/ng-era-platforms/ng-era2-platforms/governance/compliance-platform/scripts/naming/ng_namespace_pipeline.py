#!/usr/bin/env python3
"""
NG Era-1 Namespace Governance Pipeline

Strict flow model:
  [internal] -> [external] -> [global] -> [cross-validate] -> [insight] -> (next loop)

External/global/cross/insight stages require authorized team tag per access policy.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

try:
    import yaml
except ImportError:  # pragma: no cover - runtime check
    yaml = None

try:
    import tomllib
except ImportError:  # pragma: no cover - python < 3.11
    tomllib = None


STAGES = ["internal", "external", "global", "cross-validate", "insight"]

DEFAULT_SPEC_PATH = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/ng-era1-namespace.yaml"
)
DEFAULT_MAPPING_PATH = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/ng-era1-era2-mapping.yaml"
)
DEFAULT_EXTERNAL_SNAPSHOT = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/external-best-practices.yaml"
)
DEFAULT_GLOBAL_ALIASES = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/global-aliases.yaml"
)
DEFAULT_REGISTRY_DIR = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/registry"
)
DEFAULT_ACCESS_POLICY = Path(
    "/workspace/gl-governance-compliance-platform/governance/naming/ng-namespace-access-policy.yaml"
)

TEAM_TAG_ENV = "IND_AUTOOPS_TEAM_TAG"

DEFAULT_OUTPUTS = {
    "internal": "ng-era1-internal.json",
    "external": "ng-era1-external.json",
    "global": "ng-era1-global.json",
    "cross-validate": "ng-era1-cross-validation.json",
    "insight": "ng-era1-insights.md",
}

CATEGORY_DEFINITIONS = {
    "NG10100": ("Code Package Namespace", "code_level"),
    "NG10200": ("Class/Interface Namespace", "code_level"),
    "NG10300": ("Method/Function Namespace", "code_level"),
    "NG10400": ("Variable Namespace", "code_level"),
    "NG10500": ("Constant Namespace", "code_level"),
    "NG10600": ("Annotation Namespace", "code_level"),
    "NG10700": ("Configuration Namespace", "code_level"),
    "NG10800": ("Resource File Namespace", "code_level"),
    "NG10900": ("Test Namespace", "code_level"),
    "NG11000": ("Build Namespace", "code_level"),
    "NG20100": ("Module Namespace", "architecture_level"),
    "NG20200": ("Component Namespace", "architecture_level"),
    "NG20300": ("Layer Namespace", "architecture_level"),
    "NG20400": ("Service Namespace", "architecture_level"),
    "NG20500": ("API Endpoint Namespace", "architecture_level"),
    "NG20600": ("Database Table Namespace", "architecture_level"),
    "NG20700": ("Message Queue Namespace", "architecture_level"),
    "NG20800": ("Cache Key Namespace", "architecture_level"),
    "NG20900": ("Filesystem Namespace", "architecture_level"),
    "NG21000": ("Network Endpoint Namespace", "architecture_level"),
}

LAYER_MAP = {
    "gl-enterprise-architecture": "GL00-09",
    "gl-platform-services": "GL10-29",
    "gl-data-processing": "GL20-29",
    "gl-execution-runtime": "GL30-49",
    "gl-observability": "GL50-59",
    "gl-governance-compliance": "GL60-80",
    "gl-extension-services": "GL81-83",
    "gl-meta-specifications": "GL90-99",
    "gl-governance-architecture-platform": "GL00-09",
    "gl-platform-core-platform": "GL10-29",
    "gl-data-processing-platform": "GL20-29",
    "gl-runtime-engine-platform": "GL30-49",
    "gl-runtime-execution-platform": "GL30-49",
    "gl-monitoring-observability-platform": "GL50-59",
    "gl-monitoring-system-platform": "GL50-59",
    "gl-governance-compliance-platform": "GL60-80",
    "gl-extension-services-platform": "GL81-83",
    "gl-meta-specifications-platform": "GL90-99",
}

CODE_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx"}
CONFIG_EXTENSIONS = {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg"}
SQL_EXTENSIONS = {".sql"}
TEXT_EXTENSIONS = CODE_EXTENSIONS | CONFIG_EXTENSIONS | SQL_EXTENSIONS | {".md", ".sh"}

RESOURCE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".csv",
    ".txt",
}

BUILD_FILES = {
    "Dockerfile",
    "Makefile",
    "build.gradle",
    "pom.xml",
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "go.mod",
    "go.sum",
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_yaml_file(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing YAML file: {path}")
    if yaml is None:
        raise RuntimeError("PyYAML is required to load YAML files.")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_json_file(path: Path) -> Dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing JSON file: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_structured_file(path: Path) -> Dict:
    if path.suffix.lower() == ".json":
        return load_json_file(path)
    if path.suffix.lower() in {".yaml", ".yml"}:
        return load_yaml_file(path)
    raise ValueError(f"Unsupported structured file: {path}")


def load_access_policy(path: Path) -> Dict:
    if not path.exists():
        return {}
    if yaml is None:
        raise RuntimeError("PyYAML is required to load access policy files.")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def resolve_team_tag(args: argparse.Namespace) -> str:
    return (args.team_tag or os.environ.get(TEAM_TAG_ENV, "")).strip()


def authorized_teams(policy: Dict) -> List[str]:
    return policy.get("ng_namespace_access_policy", {}).get("authorized_teams", [])


def is_authorized(team_tag: str, policy: Dict) -> bool:
    if not team_tag:
        return False
    return team_tag in authorized_teams(policy)


def require_authorization(stage: str, team_tag: str, policy: Dict) -> None:
    restricted = {"external", "global", "cross-validate", "insight"}
    if stage not in restricted:
        return
    if not is_authorized(team_tag, policy):
        allowed = authorized_teams(policy)
        message = (
            f"Stage '{stage}' requires authorized team tag. "
            f"Provide --team-tag or set {TEAM_TAG_ENV}. "
            f"Allowed teams: {allowed}"
        )
        raise RuntimeError(message)


def ensure_offline_path(stage: str, path_value: str) -> None:
    lowered = path_value.lower()
    if "://" in lowered or lowered.startswith("http"):
        raise RuntimeError(
            f"Stage '{stage}' requires offline snapshot path. "
            f"Remote URLs are not allowed: {path_value}"
        )


def build_authorization_context(team_tag: str, policy_path: Path, policy: Dict) -> Dict:
    return {
        "team_tag": team_tag,
        "authorized": is_authorized(team_tag, policy),
        "policy_path": str(policy_path),
    }


def write_json(path: Path, payload: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        handle.write(content)


def infer_layer_from_module(module: str) -> str:
    if module in LAYER_MAP:
        return LAYER_MAP[module]
    if module.startswith("gl-governance-compliance"):
        return "GL60-80"
    if module.startswith("gl-extension-services"):
        return "GL81-83"
    if module.startswith("gl-meta-specifications"):
        return "GL90-99"
    if module.startswith("gl-platform"):
        return "GL10-29"
    if module.startswith("gl-data-processing"):
        return "GL20-29"
    if module.startswith("gl-runtime") or "execution" in module:
        return "GL30-49"
    if module.startswith("gl-enterprise-architecture") or module.startswith("gl-governance-architecture"):
        return "GL00-09"
    if module.startswith("gl-observability") or "monitoring" in module:
        return "GL50-59"
    return "UNMAPPED"


def derive_module_component(path: Path, repo_root: Path) -> Tuple[str, str, str]:
    relative = path.relative_to(repo_root)
    parts = relative.parts
    module = parts[0] if parts else "root"
    component = parts[1] if len(parts) > 1 else ""
    layer = infer_layer_from_module(module)
    return module, component, layer


def extract_prefix(name: str) -> str:
    for separator in [".", "/", "-", "_"]:
        if separator in name:
            return name.split(separator)[0]
    return name[:3] if len(name) > 3 else name


@dataclass
class NamespaceRecord:
    category_id: str
    category_name: str
    level: str
    name: str
    module: str
    app.kubernetes.io/component: str
    layer: str
    model: str
    sources: List[Dict[str, str]] = field(default_factory=list)
    occurrences: int = 0


class NamespaceRegistry:
    def __init__(self, max_sources: int = 3) -> None:
        self.records: Dict[Tuple[str, str, str, str, str, str], NamespaceRecord] = {}
        self.max_sources = max_sources

    def add_record(
        self,
        category_id: str,
        name: str,
        module: str,
        app.kubernetes.io/component: str,
        layer: str,
        model: str,
        source: Optional[Dict[str, str]] = None,
    ) -> None:
        category_name, level = CATEGORY_DEFINITIONS.get(
            category_id, (category_id, "unknown")
        )
        key = (category_id, name, module, component, layer, model)
        record = self.records.get(key)
        if record is None:
            record = NamespaceRecord(
                category_id=category_id,
                category_name=category_name,
                level=level,
                name=name,
                module=module,
                component=component,
                layer=layer,
                model=model,
                sources=[],
                occurrences=0,
            )
            self.records[key] = record
        record.occurrences += 1
        if source and len(record.sources) < self.max_sources:
            record.sources.append(source)

    def to_jsonl(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for record in self.records.values():
                handle.write(json.dumps(record.__dict__, ensure_ascii=False))
                handle.write("\n")

    def summarize(self) -> Dict:
        by_category: Dict[str, int] = {}
        by_level: Dict[str, int] = {}
        for record in self.records.values():
            by_category[record.category_id] = by_category.get(record.category_id, 0) + 1
            by_level[record.level] = by_level.get(record.level, 0) + 1
        return {
            "total_records": len(self.records),
            "by_category": dict(sorted(by_category.items())),
            "by_level": dict(sorted(by_level.items())),
        }


class NamespaceScanner:
    def __init__(
        self,
        repo_root: Path,
        registry: NamespaceRegistry,
        max_file_size: int = 2_000_000,
        exclude_dirs: Optional[List[str]] = None,
    ) -> None:
        self.repo_root = repo_root
        self.registry = registry
        self.max_file_size = max_file_size
        default_excludes = {".git", "node_modules", "__pycache__", ".venv", "venv"}
        self.exclude_dirs = set(default_excludes)
        if exclude_dirs:
            self.exclude_dirs.update(exclude_dirs)
        self.skipped_files: List[Dict[str, str]] = []

    def scan(self) -> None:
        self._scan_modules()
        for path in self._iter_files():
            self._scan_file(path)

    def _iter_files(self) -> Iterable[Path]:
        for path in self.repo_root.rglob("*"):
            if path.is_dir():
                if path.name in self.exclude_dirs:
                    continue
                continue
            if any(part in self.exclude_dirs for part in path.parts):
                continue
            yield path

    def _scan_modules(self) -> None:
        for module_path in self.repo_root.iterdir():
            if not module_path.is_dir():
                continue
            if module_path.name.startswith("."):
                continue
            module = module_path.name
            layer = infer_layer_from_module(module)
            self.registry.add_record(
                "NG20100",
                module,
                module=module,
                component="",
                layer=layer,
                model="architecture",
                source={"path": str(module_path.relative_to(self.repo_root)), "line": "", "context": ""},
            )
            for component_path in module_path.iterdir():
                if not component_path.is_dir():
                    continue
                if component_path.name.startswith("."):
                    continue
                component = component_path.name
                self.registry.add_record(
                    "NG20200",
                    component,
                    module=module,
                    component=component,
                    layer=layer,
                    model="architecture",
                    source={"path": str(component_path.relative_to(self.repo_root)), "line": "", "context": ""},
                )
            self.registry.add_record(
                "NG20300",
                layer,
                module=module,
                component="",
                layer=layer,
                model="architecture",
                source={"path": str(module_path.relative_to(self.repo_root)), "line": "", "context": ""},
            )

    def _scan_file(self, path: Path) -> None:
        try:
            size = path.stat().st_size
        except OSError:
            return
        if size > self.max_file_size:
            self.skipped_files.append({"path": str(path), "reason": "file_too_large"})
            return

        module, component, layer = derive_module_component(path, self.repo_root)
        relative = str(path.relative_to(self.repo_root))
        extension = path.suffix.lower()
        filename = path.name

        if extension in CODE_EXTENSIONS:
            package_name = str(Path(relative).with_suffix("")).replace(os.sep, ".")
            self.registry.add_record(
                "NG10100",
                package_name,
                module=module,
                component=component,
                layer=layer,
                model="code",
                source={"path": relative, "line": "", "context": package_name},
            )

        if filename in BUILD_FILES:
            self.registry.add_record(
                "NG11000",
                filename,
                module=module,
                component=component,
                layer=layer,
                model="build",
                source={"path": relative, "line": "", "context": filename},
            )

        if extension in RESOURCE_EXTENSIONS or "assets" in path.parts or "resources" in path.parts:
            self.registry.add_record(
                "NG10800",
                filename,
                module=module,
                component=component,
                layer=layer,
                model="resource",
                source={"path": relative, "line": "", "context": filename},
            )

        if "test" in filename.lower() or "tests" in path.parts:
            self.registry.add_record(
                "NG10900",
                filename,
                module=module,
                component=component,
                layer=layer,
                model="test",
                source={"path": relative, "line": "", "context": filename},
            )

        service_name = None
        for index, part in enumerate(path.parts):
            if part.lower() in {"service", "services"} and index + 1 < len(path.parts):
                service_name = path.parts[index + 1]
                break
        if service_name or "service" in filename.lower():
            name = service_name or path.stem
            self.registry.add_record(
                "NG20400",
                name,
                module=module,
                component=component,
                layer=layer,
                model="architecture",
                source={"path": relative, "line": "", "context": name},
            )

        if extension not in TEXT_EXTENSIONS:
            return

        try:
            with path.open("r", encoding="utf-8", errors="ignore") as handle:
                lines = list(handle)
        except OSError:
            return

        if extension in CODE_EXTENSIONS:
            self._scan_code_lines(lines, module, component, layer, relative)

        if extension in CONFIG_EXTENSIONS:
            self._scan_config_file(path, module, component, layer, relative, lines)

        self._scan_architecture_signals(lines, module, component, layer, relative)

    def _scan_code_lines(
        self,
        lines: List[str],
        module: str,
        app.kubernetes.io/component: str,
        layer: str,
        relative: str,
    ) -> None:
        class_regex = re.compile(r"^\s*(?:export\s+)?(?:default\s+)?class\s+([A-Za-z_][A-Za-z0-9_]*)")
        interface_regex = re.compile(r"^\s*(?:export\s+)?interface\s+([A-Za-z_][A-Za-z0-9_]*)")
        python_class_regex = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
        function_regex = re.compile(r"^\s*(?:export\s+)?function\s+([A-Za-z_][A-Za-z0-9_]*)")
        python_function_regex = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)")
        variable_regex = re.compile(r"^\s*(?:const|let|var)\s+([A-Za-z_][A-Za-z0-9_]*)")
        python_variable_regex = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=")
        constant_regex = re.compile(r"^\s*const\s+([A-Z][A-Z0-9_]*)")
        python_constant_regex = re.compile(r"^\s*([A-Z][A-Z0-9_]*)\s*=")
        decorator_regex = re.compile(r"^\s*@([A-Za-z_][A-Za-z0-9_]*)")

        for line_number, line in enumerate(lines, start=1):
            context = line.strip()[:200]
            match = python_class_regex.match(line) or class_regex.match(line) or interface_regex.match(line)
            if match:
                name = match.group(1)
                self.registry.add_record(
                    "NG10200",
                    name,
                    module,
                    component,
                    layer,
                    model="code",
                    source={"path": relative, "line": str(line_number), "context": context},
                )
                if name.lower().endswith("service"):
                    self.registry.add_record(
                        "NG20400",
                        name,
                        module,
                        component,
                        layer,
                        model="code",
                        source={"path": relative, "line": str(line_number), "context": context},
                    )

            match = python_function_regex.match(line) or function_regex.match(line)
            if match:
                name = match.group(1)
                self.registry.add_record(
                    "NG10300",
                    name,
                    module,
                    component,
                    layer,
                    model="code",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            match = python_constant_regex.match(line) or constant_regex.match(line)
            if match:
                name = match.group(1)
                self.registry.add_record(
                    "NG10500",
                    name,
                    module,
                    component,
                    layer,
                    model="code",
                    source={"path": relative, "line": str(line_number), "context": context},
                )
                continue

            match = python_variable_regex.match(line) or variable_regex.match(line)
            if match:
                name = match.group(1)
                if name.isupper():
                    self.registry.add_record(
                        "NG10500",
                        name,
                        module,
                        component,
                        layer,
                        model="code",
                        source={"path": relative, "line": str(line_number), "context": context},
                    )
                else:
                    self.registry.add_record(
                        "NG10400",
                        name,
                        module,
                        component,
                        layer,
                        model="code",
                        source={"path": relative, "line": str(line_number), "context": context},
                    )

            match = decorator_regex.match(line)
            if match:
                name = match.group(1)
                self.registry.add_record(
                    "NG10600",
                    name,
                    module,
                    component,
                    layer,
                    model="code",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            if "/" in line:
                for endpoint in re.findall(r"['\"](/(?:api|gl|v\d+)/[^'\"\s]+)['\"]", line):
                    self.registry.add_record(
                        "NG20500",
                        endpoint,
                        module,
                        component,
                        layer,
                        model="code",
                        source={"path": relative, "line": str(line_number), "context": context},
                    )

            for table in re.findall(r"\b(?:CREATE\s+TABLE|FROM|JOIN)\s+([A-Za-z0-9_.-]+)", line, flags=re.IGNORECASE):
                self.registry.add_record(
                    "NG20600",
                    table,
                    module,
                    component,
                    layer,
                    model="data",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            for topic in re.findall(r"\b(?:topic|queue)\s*[:=]\s*['\"]([^'\"]+)['\"]", line, flags=re.IGNORECASE):
                self.registry.add_record(
                    "NG20700",
                    topic,
                    module,
                    component,
                    layer,
                    model="integration",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            for key in re.findall(r"\b(?:cache_key|cacheKey|CACHE_KEY)\s*[:=]\s*['\"]([^'\"]+)['\"]", line):
                self.registry.add_record(
                    "NG20800",
                    key,
                    module,
                    component,
                    layer,
                    model="cache",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            for path_match in re.findall(r"\b(?:path|file|dir|directory)\s*[:=]\s*['\"]([^'\"]+)['\"]", line):
                if "/" in path_match or "\\" in path_match:
                    self.registry.add_record(
                        "NG20900",
                        path_match,
                        module,
                        component,
                        layer,
                        model="filesystem",
                        source={"path": relative, "line": str(line_number), "context": context},
                    )

            for endpoint in re.findall(r"https?://[^\s'\"<>]+", line):
                self.registry.add_record(
                    "NG21000",
                    endpoint,
                    module,
                    component,
                    layer,
                    model="network",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            for endpoint in re.findall(r"\b[A-Za-z0-9.-]+:\d{2,5}\b", line):
                self.registry.add_record(
                    "NG21000",
                    endpoint,
                    module,
                    component,
                    layer,
                    model="network",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

    def _scan_config_file(
        self,
        path: Path,
        module: str,
        app.kubernetes.io/component: str,
        layer: str,
        relative: str,
        lines: List[str],
    ) -> None:
        extension = path.suffix.lower()
        data = None
        try:
            if extension == ".json":
                data = json.loads("".join(lines))
            elif extension in {".yaml", ".yml"} and yaml is not None:
                data = yaml.safe_load("".join(lines))
            elif extension == ".toml" and tomllib is not None:
                data = tomllib.loads("".join(lines))
        except Exception:
            data = None

        if isinstance(data, dict):
            for key in data.keys():
                self.registry.add_record(
                    "NG10700",
                    str(key),
                    module,
                    component,
                    layer,
                    model="config",
                    source={"path": relative, "line": "", "context": str(key)},
                )
        else:
            for line_number, line in enumerate(lines, start=1):
                if line.lstrip() != line:
                    continue
                match = re.match(r"^([A-Za-z0-9_.-]+)\s*:", line)
                if match:
                    key = match.group(1)
                    self.registry.add_record(
                        "NG10700",
                        key,
                        module,
                        component,
                        layer,
                        model="config",
                        source={"path": relative, "line": str(line_number), "context": line.strip()[:200]},
                    )

    def _scan_architecture_signals(
        self,
        lines: List[str],
        module: str,
        app.kubernetes.io/component: str,
        layer: str,
        relative: str,
    ) -> None:
        for line_number, line in enumerate(lines, start=1):
            context = line.strip()[:200]
            if "service" in line.lower():
                for match in re.findall(r"\b([A-Za-z0-9_-]*service[A-Za-z0-9_-]*)\b", line, flags=re.IGNORECASE):
                    self.registry.add_record(
                        "NG20400",
                        match,
                        module,
                        component,
                        layer,
                        model="architecture",
                        source={"path": relative, "line": str(line_number), "context": context},
                    )

            for endpoint in re.findall(r"['\"](/(?:api|gl|v\d+)/[^'\"\s]+)['\"]", line):
                self.registry.add_record(
                    "NG20500",
                    endpoint,
                    module,
                    component,
                    layer,
                    model="architecture",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            for match in re.findall(r"\b(?:topic|queue)\s*[:=]\s*['\"]([^'\"]+)['\"]", line, flags=re.IGNORECASE):
                self.registry.add_record(
                    "NG20700",
                    match,
                    module,
                    component,
                    layer,
                    model="integration",
                    source={"path": relative, "line": str(line_number), "context": context},
                )

            for match in re.findall(r"\b(?:cache_key|cacheKey|CACHE_KEY)\s*[:=]\s*['\"]([^'\"]+)['\"]", line):
                self.registry.add_record(
                    "NG20800",
                    match,
                    module,
                    component,
                    layer,
                    model="cache",
                    source={"path": relative, "line": str(line_number), "context": context},
                )


def read_registry_jsonl(path: Path) -> List[Dict]:
    records = []
    if not path.exists():
        return records
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def internal_stage(
    repo_root: Path,
    spec_path: Path,
    registry_dir: Path,
    output_path: Path,
    max_file_size: int,
    exclude_dirs: List[str],
    auth_context: Dict,
) -> Path:
    spec = load_yaml_file(spec_path)
    registry_dir.mkdir(parents=True, exist_ok=True)
    registry_path = registry_dir / "namespace-registry.jsonl"

    registry = NamespaceRegistry()
    scanner = NamespaceScanner(repo_root, registry, max_file_size=max_file_size, exclude_dirs=exclude_dirs)
    scanner.scan()
    registry.to_jsonl(registry_path)

    summary = registry.summarize()
    payload = {
        "stage": "internal",
        "timestamp": utc_now(),
        "flow_model": STAGES,
        "authorization": auth_context,
        "repo_root": str(repo_root),
        "spec_path": str(spec_path),
        "spec_version": spec.get("ngera1namespace_governance", {}).get("version"),
        "counts": summary,
        "registry_path": str(registry_path),
        "skipped_files": len(scanner.skipped_files),
        "skipped_details": scanner.skipped_files[:20],
    }
    write_json(output_path, payload)
    return output_path


def external_stage(snapshot_path: Path, output_path: Path, auth_context: Dict) -> Path:
    data = load_structured_file(snapshot_path) if snapshot_path.exists() else {}
    payload = {
        "stage": "external",
        "timestamp": utc_now(),
        "flow_model": STAGES,
        "authorization": auth_context,
        "snapshot_path": str(snapshot_path),
        "snapshot_keys": sorted(list(data.keys())) if isinstance(data, dict) else [],
    }
    write_json(output_path, payload)
    return output_path


def global_stage(aliases_path: Path, output_path: Path, auth_context: Dict) -> Path:
    data = load_structured_file(aliases_path) if aliases_path.exists() else {}
    payload = {
        "stage": "global",
        "timestamp": utc_now(),
        "flow_model": STAGES,
        "authorization": auth_context,
        "aliases_path": str(aliases_path),
        "aliases_keys": sorted(list(data.keys())) if isinstance(data, dict) else [],
    }
    write_json(output_path, payload)
    return output_path


def cross_validate_stage(
    internal_path: Path,
    mapping_path: Path,
    registry_path: Path,
    external_path: Optional[Path],
    global_path: Optional[Path],
    output_path: Path,
    auth_context: Dict,
) -> Path:
    internal_payload = load_json_file(internal_path)
    mapping_payload = load_yaml_file(mapping_path)
    records = read_registry_jsonl(registry_path)

    missing_required_fields = [
        record
        for record in records
        if not record.get("module") or record.get("layer") in {"", None}
    ]

    unmapped_layers = [record for record in records if record.get("layer") == "UNMAPPED"]

    mapping = mapping_payload.get("era1toera2_mapping", {})
    missing_era2_mapping = [
        record for record in records if record.get("category_id") not in mapping
    ]

    prefix_collisions: Dict[str, Dict[str, int]] = {}
    for record in records:
        category_id = record.get("category_id")
        prefix = extract_prefix(record.get("name", ""))
        prefix_collisions.setdefault(category_id, {})
        prefix_collisions[category_id][prefix] = prefix_collisions[category_id].get(prefix, 0) + 1

    collision_summary = {
        category: {
            prefix: count
            for prefix, count in prefixes.items()
            if count > 1
        }
        for category, prefixes in prefix_collisions.items()
    }

    payload = {
        "stage": "cross-validate",
        "timestamp": utc_now(),
        "flow_model": STAGES,
        "authorization": auth_context,
        "inputs": {
            "internal": str(internal_path),
            "external": str(external_path) if external_path else "",
            "global": str(global_path) if global_path else "",
            "mapping": str(mapping_path),
            "registry": str(registry_path),
        },
        "counts": {
            "total_records": len(records),
            "missing_required_fields": len(missing_required_fields),
            "unmapped_layers": len(unmapped_layers),
            "missing_era2_mapping": len(missing_era2_mapping),
            "prefix_collisions": sum(
                len(prefixes) for prefixes in collision_summary.values()
            ),
        },
        "details": {
            "missing_required_fields": missing_required_fields[:20],
            "unmapped_layers": unmapped_layers[:20],
            "missing_era2_mapping": missing_era2_mapping[:20],
            "prefix_collisions": collision_summary,
        },
    }
    write_json(output_path, payload)
    return output_path


def insight_stage(cross_validation_path: Path, output_path: Path, auth_context: Dict) -> Path:
    data = load_json_file(cross_validation_path)
    counts = data.get("counts", {})
    details = data.get("details", {})

    insights = [
        f"- Total records scanned: {counts.get('total_records', 0)}",
        f"- Unmapped layers: {counts.get('unmapped_layers', 0)}",
        f"- Missing Era-2 mapping: {counts.get('missing_era2_mapping', 0)}",
        f"- Prefix collisions: {counts.get('prefix_collisions', 0)}",
    ]

    questions = [
        "Which modules require explicit layer mapping to avoid UNMAPPED results?",
        "Should additional Era-1 categories be mapped to Era-2 for completeness?",
        "Do prefix collision rules need stronger normalization for cross-module consistency?",
        "Should scanning include additional file types for API and queue detection?",
    ]

    report = [
        "# NG Era-1 Namespace Governance Insights",
        "",
        f"Timestamp: {utc_now()}",
        f"Authorization: {auth_context.get('team_tag', '')}",
        "",
        "## Summary Insights",
        *insights,
        "",
        "## Top Findings",
        f"- Missing required fields (sample): {len(details.get('missing_required_fields', []))}",
        f"- Unmapped layers (sample): {len(details.get('unmapped_layers', []))}",
        f"- Missing Era-2 mapping (sample): {len(details.get('missing_era2_mapping', []))}",
        "",
        "## New Questions",
        *[f"- {question}" for question in questions],
        "",
    ]

    write_text(output_path, "\n".join(report))
    return output_path


def resolve_output_path(stage: str, registry_dir: Path, override: Optional[str]) -> Path:
    if override:
        return Path(override)
    return registry_dir / DEFAULT_OUTPUTS[stage]


def ensure_prerequisites(stage: str, registry_dir: Path) -> None:
    prerequisites = {
        "external": ["internal"],
        "global": ["internal"],
        "cross-validate": ["internal", "external", "global"],
        "insight": ["cross-validate"],
    }
    needed = prerequisites.get(stage, [])
    missing = []
    for required in needed:
        path = registry_dir / DEFAULT_OUTPUTS[required]
        if not path.exists():
            missing.append(str(path))
    if missing:
        raise RuntimeError(
            f"Stage '{stage}' requires prior outputs: {', '.join(missing)}"
        )


def run_all(args: argparse.Namespace) -> None:
    registry_dir = Path(args.registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)
    policy_path = Path(args.access_policy)
    policy = load_access_policy(policy_path)
    team_tag = resolve_team_tag(args)
    auth_context = build_authorization_context(team_tag, policy_path, policy)

    internal_path = resolve_output_path("internal", registry_dir, args.out if args.stage == "internal" else None)
    internal_stage(
        repo_root=Path(args.repo_root),
        spec_path=Path(args.spec),
        registry_dir=registry_dir,
        output_path=internal_path,
        max_file_size=args.max_file_size,
        exclude_dirs=args.exclude_dir,
        auth_context=auth_context,
    )

    require_authorization("external", team_tag, policy)
    ensure_offline_path("external", args.snapshot)
    external_path = resolve_output_path("external", registry_dir, None)
    external_stage(Path(args.snapshot), external_path, auth_context)

    require_authorization("global", team_tag, policy)
    ensure_offline_path("global", args.global_aliases)
    global_path = resolve_output_path("global", registry_dir, None)
    global_stage(Path(args.global_aliases), global_path, auth_context)

    registry_path = registry_dir / "namespace-registry.jsonl"
    cross_path = resolve_output_path("cross-validate", registry_dir, None)
    require_authorization("cross-validate", team_tag, policy)
    cross_validate_stage(
        internal_path=internal_path,
        mapping_path=Path(args.mapping),
        registry_path=registry_path,
        external_path=external_path,
        global_path=global_path,
        output_path=cross_path,
        auth_context=auth_context,
    )

    insight_path = resolve_output_path("insight", registry_dir, None)
    require_authorization("insight", team_tag, policy)
    insight_stage(cross_path, insight_path, auth_context)

    print(f"Pipeline completed. Output directory: {registry_dir}")


def run_single(args: argparse.Namespace) -> None:
    registry_dir = Path(args.registry_dir)
    registry_dir.mkdir(parents=True, exist_ok=True)
    ensure_prerequisites(args.stage, registry_dir)
    policy_path = Path(args.access_policy)
    policy = load_access_policy(policy_path)
    team_tag = resolve_team_tag(args)
    auth_context = build_authorization_context(team_tag, policy_path, policy)

    if args.stage == "internal":
        internal_stage(
            repo_root=Path(args.repo_root),
            spec_path=Path(args.spec),
            registry_dir=registry_dir,
            output_path=resolve_output_path("internal", registry_dir, args.out),
            max_file_size=args.max_file_size,
            exclude_dirs=args.exclude_dir,
            auth_context=auth_context,
        )
        return

    if args.stage == "external":
        require_authorization("external", team_tag, policy)
        ensure_offline_path("external", args.snapshot)
        external_stage(
            snapshot_path=Path(args.snapshot),
            output_path=resolve_output_path("external", registry_dir, args.out),
            auth_context=auth_context,
        )
        return

    if args.stage == "global":
        require_authorization("global", team_tag, policy)
        ensure_offline_path("global", args.global_aliases)
        global_stage(
            aliases_path=Path(args.global_aliases),
            output_path=resolve_output_path("global", registry_dir, args.out),
            auth_context=auth_context,
        )
        return

    if args.stage == "cross-validate":
        require_authorization("cross-validate", team_tag, policy)
        cross_validate_stage(
            internal_path=registry_dir / DEFAULT_OUTPUTS["internal"],
            mapping_path=Path(args.mapping),
            registry_path=registry_dir / "namespace-registry.jsonl",
            external_path=registry_dir / DEFAULT_OUTPUTS["external"],
            global_path=registry_dir / DEFAULT_OUTPUTS["global"],
            output_path=resolve_output_path("cross-validate", registry_dir, args.out),
            auth_context=auth_context,
        )
        return

    if args.stage == "insight":
        require_authorization("insight", team_tag, policy)
        insight_stage(
            cross_validation_path=registry_dir / DEFAULT_OUTPUTS["cross-validate"],
            output_path=resolve_output_path("insight", registry_dir, args.out),
            auth_context=auth_context,
        )
        return

    raise RuntimeError(f"Unknown stage: {args.stage}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="NG Era-1 Namespace Governance Pipeline",
    )
    parser.add_argument(
        "--stage",
        choices=STAGES,
        help="Run a single stage (requires previous outputs).",
    )
    parser.add_argument(
        "--run-all",
        action="store_true",
        help="Run the full pipeline in strict order.",
    )
    parser.add_argument(
        "--repo-root",
        default="/workspace",
        help="Repository root for scanning.",
    )
    parser.add_argument(
        "--spec",
        default=str(DEFAULT_SPEC_PATH),
        help="Path to NG Era-1 namespace spec YAML.",
    )
    parser.add_argument(
        "--mapping",
        default=str(DEFAULT_MAPPING_PATH),
        help="Path to Era-1 -> Era-2 mapping YAML.",
    )
    parser.add_argument(
        "--snapshot",
        default=str(DEFAULT_EXTERNAL_SNAPSHOT),
        help="External best practices snapshot (offline).",
    )
    parser.add_argument(
        "--global-aliases",
        default=str(DEFAULT_GLOBAL_ALIASES),
        help="Global aliases mapping file.",
    )
    parser.add_argument(
        "--access-policy",
        default=str(DEFAULT_ACCESS_POLICY),
        help="Access policy file for conditional stage authorization.",
    )
    parser.add_argument(
        "--team-tag",
        help=f"Team tag for authorized stages (or set {TEAM_TAG_ENV}).",
    )
    parser.add_argument(
        "--registry-dir",
        default=str(DEFAULT_REGISTRY_DIR),
        help="Central registry directory.",
    )
    parser.add_argument(
        "--out",
        help="Override output path for the selected stage.",
    )
    parser.add_argument(
        "--max-file-size",
        type=int,
        default=2_000_000,
        help="Max file size (bytes) for scanning.",
    )
    parser.add_argument(
        "--exclude-dir",
        action="append",
        default=[],
        help="Directory name to exclude (repeatable).",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.run_all or not args.stage:
        run_all(args)
    else:
        run_single(args)


if __name__ == "__main__":
    main()
