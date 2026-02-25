"""
Module Scanner — Deep-scan governance modules for GL annotations,
hash signatures, naming compliance, and configuration drift.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: governance-sensing
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    """A single issue discovered during a module scan."""

    path: str
    rule_id: str
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW
    message: str
    auto_fixable: bool = False
    context: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ScanReport:
    """Aggregated result of scanning the entire repository."""

    scan_id: str
    timestamp: str
    modules_scanned: int = 0
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    modules: list[dict[str, Any]] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    hashes: dict[str, str] = field(default_factory=dict)
    drift: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["findings"] = [f.to_dict() for f in self.findings]
        return data


# ---------------------------------------------------------------------------
# GL annotation pattern
# ---------------------------------------------------------------------------

GL_ANNOTATION_RE = re.compile(
    r"@GL-(governed|layer|semantic|audit-trail|version)\s*:\s*(.+)",
)

REQUIRED_GL_ANNOTATIONS = {"governed", "layer", "semantic"}

# ---------------------------------------------------------------------------
# Module naming conventions
# ---------------------------------------------------------------------------

DIRECTORY_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PYTHON_SNAKE_RE = re.compile(r"^[a-z][a-z0-9_]*\.py$")
CONFIG_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.(yaml|yml|json)$")

EXCLUDED_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".idea", ".vscode", ".governance", "outputs",
}


# ---------------------------------------------------------------------------
# ModuleScanner
# ---------------------------------------------------------------------------

class ModuleScanner:
    """Discovers governance modules, validates GL annotations, hashes,
    and naming compliance across the entire repository tree."""

    def __init__(self) -> None:
        self.log = structlog.get_logger(self.__class__.__name__)

    # -- public API ---------------------------------------------------------

    def scan_all(self, repo_root: Path) -> ScanReport:
        """Walk *repo_root*, discover responsibility-boundary modules,
        and return a full :class:`ScanReport`."""
        repo_root = repo_root.resolve()
        ts = datetime.now(timezone.utc)
        report = ScanReport(
            scan_id=f"SCAN-{ts.strftime('%Y%m%dT%H%M%S')}",
            timestamp=ts.isoformat(),
        )

        self.log.info("scan_all.start", repo_root=str(repo_root))

        # Each top-level directory that starts with "responsibility-" is a module
        module_dirs = sorted(
            p for p in repo_root.iterdir()
            if p.is_dir() and not p.name.startswith(".")
        )

        for mod_dir in module_dirs:
            if any(part in EXCLUDED_DIRS for part in mod_dir.parts):
                continue
            findings = self.scan_module(mod_dir)
            mod_hash = self._compute_hash_signature(mod_dir)

            report.modules.append({
                "module_id": mod_dir.name,
                "path": str(mod_dir),
                "hash": mod_hash,
                "finding_count": len(findings),
            })
            report.hashes[mod_dir.name] = mod_hash
            report.findings.extend(findings)

        report.modules_scanned = len(report.modules)
        report.total_findings = len(report.findings)
        report.critical_count = sum(1 for f in report.findings if f.severity == "CRITICAL")
        report.high_count = sum(1 for f in report.findings if f.severity == "HIGH")
        report.medium_count = sum(1 for f in report.findings if f.severity == "MEDIUM")
        report.low_count = sum(1 for f in report.findings if f.severity == "LOW")

        self.log.info(
            "scan_all.complete",
            modules=report.modules_scanned,
            findings=report.total_findings,
        )
        return report

    def scan_module(self, module_path: Path) -> list[Finding]:
        """Deep-scan a single module directory."""
        findings: list[Finding] = []
        module_path = module_path.resolve()

        if not module_path.is_dir():
            findings.append(Finding(
                path=str(module_path),
                rule_id="MOD-EXIST-001",
                severity="CRITICAL",
                message=f"Module directory does not exist: {module_path.name}",
            ))
            return findings

        # Check naming of the directory itself
        findings.extend(self._check_naming_convention(module_path))

        # Walk all Python files for GL annotations
        for py_file in module_path.rglob("*.py"):
            if any(part in EXCLUDED_DIRS for part in py_file.parts):
                continue
            findings.extend(self._check_gl_annotations(py_file))

        return findings

    # -- private helpers ----------------------------------------------------

    def _check_gl_annotations(self, file_path: Path) -> list[Finding]:
        """Verify that a Python file carries the required GL annotations."""
        findings: list[Finding] = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            findings.append(Finding(
                path=str(file_path),
                rule_id="GL-READ-001",
                severity="MEDIUM",
                message=f"Cannot read file: {file_path.name}",
            ))
            return findings

        found_annotations: set[str] = set()
        for match in GL_ANNOTATION_RE.finditer(content):
            found_annotations.add(match.group(1))

        missing = REQUIRED_GL_ANNOTATIONS - found_annotations
        if missing:
            # Only enforce on core governance files
            rel = file_path.name.lower()
            is_core = any(
                kw in rel
                for kw in ("enforcer", "scanner", "executor", "orchestr", "audit", "gate")
            )
            if is_core:
                findings.append(Finding(
                    path=str(file_path),
                    rule_id="GL-ANNOT-001",
                    severity="MEDIUM",
                    message=f"Missing GL annotations: {', '.join(sorted(missing))}",
                    auto_fixable=True,
                    context={"missing": sorted(missing)},
                ))

        return findings

    def _check_naming_convention(self, path: Path) -> list[Finding]:
        """Validate directory and file naming conventions."""
        findings: list[Finding] = []

        for child in path.rglob("*"):
            if any(part in EXCLUDED_DIRS for part in child.parts):
                continue
            name = child.name

            if child.is_dir():
                # Directories should be kebab-case (allow underscore for Python packages)
                if (child / "__init__.py").exists():
                    continue
                if name.startswith(".") or name.startswith("__"):
                    continue
                if "_" in name and not DIRECTORY_KEBAB_RE.match(name):
                    findings.append(Finding(
                        path=str(child),
                        rule_id="NAME-DIR-001",
                        severity="MEDIUM",
                        message=f"Directory '{name}' should use kebab-case",
                        auto_fixable=False,
                    ))

            elif child.is_file() and child.suffix == ".py":
                if name.startswith("__"):
                    continue
                if "-" in child.stem:
                    findings.append(Finding(
                        path=str(child),
                        rule_id="NAME-PY-001",
                        severity="HIGH",
                        message=f"Python file '{name}' must use snake_case",
                        auto_fixable=False,
                    ))

        return findings

    def _compute_hash_signature(self, path: Path) -> str:
        """Compute a deterministic SHA-256 over all files in *path*."""
        digest = hashlib.sha256()
        try:
            for file_path in sorted(
                p for p in path.rglob("*") if p.is_file()
            ):
                rel = str(file_path.relative_to(path))
                digest.update(rel.encode("utf-8"))
                file_hash = hashlib.sha256()
                with file_path.open("rb") as fh:
                    for chunk in iter(lambda: fh.read(8192), b""):
                        file_hash.update(chunk)
                digest.update(file_hash.hexdigest().encode("utf-8"))
        except OSError as exc:
            logger.warning("hash_computation_error", path=str(path), error=str(exc))
        return digest.hexdigest()

    def _detect_drift(
        self, module: dict[str, Any], baseline: dict[str, Any],
    ) -> list[Finding]:
        """Compare current module hashes against a known baseline."""
        findings: list[Finding] = []
        module_id = module.get("module_id", "unknown")
        current_hash = module.get("hash", "")
        baseline_hash = baseline.get(module_id, "")

        if not baseline_hash:
            return findings

        if current_hash != baseline_hash:
            findings.append(Finding(
                path=module.get("path", module_id),
                rule_id="DRIFT-001",
                severity="HIGH",
                message=(
                    f"Hash drift detected for {module_id}: "
                    f"expected {baseline_hash[:16]}..., "
                    f"got {current_hash[:16]}..."
                ),
                context={
                    "expected": baseline_hash,
                    "actual": current_hash,
                },
            ))
        return findings


def main() -> None:
    """Entry point for the ``govops-scan`` console script."""
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="GovOps Module Scanner")
    parser.add_argument("repo_root", nargs="?", default=".", help="Repository root path to scan")
    parser.add_argument("--output", help="Write JSON report to file instead of stdout")
    args = parser.parse_args()

    scanner = ModuleScanner()
    report = scanner.scan_all(Path(args.repo_root))

    output = json.dumps(report.to_dict(), indent=2)
    if args.output:
        Path(args.output).write_text(output)
    else:
        print(output)

    sys.exit(1 if report.total_findings > 0 else 0)


if __name__ == "__main__":
    main()
