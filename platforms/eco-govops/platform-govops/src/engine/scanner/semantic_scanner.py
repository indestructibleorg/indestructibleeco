"""
Semantic Scanner — Discover and verify semantic bindings between
governance modules (e.g. GL-layer references, cross-boundary links).

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-semantic-integrity
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".idea", ".vscode", ".governance", "outputs",
}

# Patterns that indicate a semantic reference to another module
IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+([\w.]+)", re.MULTILINE)
REFERENCE_RE = re.compile(
    r"@GL-audit-trail\s*:\s*(\S+)"
    r"|@GL-semantic\s*:\s*(\S+)"
    r"|responsibility-[\w-]+",
)
YAML_REF_RE = re.compile(r"(?:ref|source|target|module)\s*:\s*[\"']?([^\s\"']+)")


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class SemanticBinding:
    """A directed relationship between two governance artefacts."""

    source: str
    target: str
    binding_type: str  # "import" | "gl-reference" | "yaml-ref" | "path-ref"
    verified: bool = False
    detail: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# SemanticScanner
# ---------------------------------------------------------------------------

class SemanticScanner:
    """Discover semantic bindings across the repository and verify that
    every referenced target actually exists."""

    def __init__(self) -> None:
        self.log = structlog.get_logger(self.__class__.__name__)

    # -- public API ---------------------------------------------------------

    def scan_semantic_bindings(self, repo_root: Path) -> list[SemanticBinding]:
        """Walk the repository and collect all semantic bindings."""
        repo_root = repo_root.resolve()
        bindings: list[SemanticBinding] = []

        self.log.info("scan_semantic_bindings.start", repo_root=str(repo_root))

        for file_path in sorted(repo_root.rglob("*")):
            if not file_path.is_file():
                continue
            if any(part in EXCLUDED_DIRS for part in file_path.parts):
                continue

            rel = str(file_path.relative_to(repo_root))

            if file_path.suffix == ".py":
                bindings.extend(self._extract_python_bindings(file_path, rel))
            elif file_path.suffix in (".yaml", ".yml", ".json"):
                bindings.extend(self._extract_config_bindings(file_path, rel, repo_root))

        # Verify each binding
        for binding in bindings:
            binding.verified = self.verify_binding(binding, repo_root)

        self.log.info(
            "scan_semantic_bindings.complete",
            total=len(bindings),
            verified=sum(1 for b in bindings if b.verified),
        )
        return bindings

    def verify_binding(
        self, binding: SemanticBinding, repo_root: Path | None = None,
    ) -> bool:
        """Check that the target of a binding exists on disk or matches a
        known GL semantic identifier."""
        target = binding.target

        # GL semantic identifiers are always considered valid
        if target.startswith("governance-") or target.startswith("GL"):
            return True

        # Filesystem existence check
        if repo_root is not None:
            candidate = repo_root / target
            if candidate.exists():
                return True
            # Try with .py extension
            if not target.endswith(".py") and (repo_root / f"{target}.py").exists():
                return True
            # Try converting dots to slashes (Python module path)
            module_path = repo_root / target.replace(".", "/")
            if module_path.exists() or module_path.with_suffix(".py").exists():
                return True

        return False

    def detect_orphaned_modules(
        self,
        bindings: list[SemanticBinding],
        modules: list[str],
    ) -> list[str]:
        """Return module identifiers that are never referenced by any
        binding (i.e. orphans with no inbound semantic link)."""
        referenced: set[str] = set()
        for binding in bindings:
            referenced.add(binding.target)
            # Also consider partial matches (the module id may be a
            # substring of the target path)
            for mod in modules:
                if mod in binding.target or binding.target in mod:
                    referenced.add(mod)

        orphaned = [m for m in modules if m not in referenced]
        if orphaned:
            self.log.warning(
                "orphaned_modules_detected",
                count=len(orphaned),
                modules=orphaned,
            )
        return orphaned

    # -- private helpers ----------------------------------------------------

    def _extract_python_bindings(
        self, file_path: Path, rel_path: str,
    ) -> list[SemanticBinding]:
        """Extract bindings from Python import statements and GL annotations."""
        bindings: list[SemanticBinding] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return bindings

        # Python imports
        for match in IMPORT_RE.finditer(content):
            module_ref = match.group(1)
            if module_ref.startswith("__"):
                continue
            bindings.append(SemanticBinding(
                source=rel_path,
                target=module_ref,
                binding_type="import",
            ))

        # GL annotations / responsibility references
        for match in REFERENCE_RE.finditer(content):
            target = match.group(1) or match.group(2) or match.group(0)
            target = target.strip()
            if target:
                bindings.append(SemanticBinding(
                    source=rel_path,
                    target=target,
                    binding_type="gl-reference",
                ))

        return bindings

    def _extract_config_bindings(
        self, file_path: Path, rel_path: str, repo_root: Path,
    ) -> list[SemanticBinding]:
        """Extract bindings from YAML / JSON configuration files."""
        bindings: list[SemanticBinding] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return bindings

        for match in YAML_REF_RE.finditer(content):
            target = match.group(1).strip()
            if target and len(target) > 2:
                bindings.append(SemanticBinding(
                    source=rel_path,
                    target=target,
                    binding_type="yaml-ref",
                ))

        # Responsibility-boundary references
        for match in re.finditer(r"responsibility-[\w-]+", content):
            bindings.append(SemanticBinding(
                source=rel_path,
                target=match.group(0),
                binding_type="path-ref",
            ))

        return bindings
