"""
govops-platform engine -- Scanner subsystem.

Provides filesystem scanning for governance-managed modules, content-hash
drift detection, and semantic validation of naming / GL layer alignment.

Classes exported:
    ModuleScanner   -- walks a repo tree, discovers governance modules, checks
                       GL annotations, detects drift via hash comparison.
    HashScanner     -- computes deterministic SHA-256 hashes for files and
                       directories, compares them against stored baselines.
    SemanticScanner -- validates naming conventions, GL layer assignments, and
                       NG era alignment for every discovered module.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Sequence

import structlog
from pydantic import BaseModel, Field

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

GL_ANNOTATION_PATTERN = re.compile(
    r"@GL-governed|@GL-layer:\s*(?P<layer>GL\d{2}(?:-\d{2})?)"
)
GL_LAYER_PATTERN = re.compile(r"@GL-layer:\s*(?P<layer>GL\d{2}(?:-\d{2})?)")
GL_SEMANTIC_PATTERN = re.compile(r"@GL-semantic:\s*(?P<semantic>[\w-]+)")

KEBAB_CASE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
SNAKE_CASE = re.compile(r"^[a-z][a-z0-9]*(_[a-z0-9]+)*$")

VALID_GL_LAYERS: set[str] = {
    f"GL{lo:02d}-{hi:02d}"
    for lo, hi in (
        (0, 9),
        (10, 19),
        (20, 29),
        (30, 39),
        (40, 49),
        (50, 59),
        (60, 69),
        (70, 79),
        (80, 89),
        (90, 99),
    )
}

VALID_NG_ERAS: set[str] = {"Era-0", "Era-1", "Era-2", "Era-3"}

# Directories to skip while scanning
_SKIP_DIRS: frozenset[str] = frozenset(
    {
        ".git",
        "__pycache__",
        "node_modules",
        ".venv",
        "venv",
        ".idea",
        ".vscode",
        ".tox",
        ".mypy_cache",
        ".ruff_cache",
        ".pytest_cache",
    }
)


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class ScanSeverity(str, Enum):
    """Severity levels for scan findings."""

    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


class ScanStatus(str, Enum):
    """Aggregate scan status for a module."""

    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class CheckResult(BaseModel):
    """Single check result inside a module scan."""

    check: str
    passed: bool
    detail: str = ""
    severity: ScanSeverity = ScanSeverity.MEDIUM


class ModuleScanResult(BaseModel):
    """Result of scanning a single governance module."""

    module_id: str
    directory: str
    status: ScanStatus = ScanStatus.PASS
    checks: list[CheckResult] = Field(default_factory=list)
    content_hash: str | None = None
    file_count: int = 0
    gl_layer: str | None = None
    gl_semantic: str | None = None
    has_gl_annotation: bool = False
    scanned_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class DriftRecord(BaseModel):
    """Records detected hash drift between two scans."""

    module_id: str
    previous_hash: str
    current_hash: str
    detected_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class SemanticFinding(BaseModel):
    """A semantic-level finding (naming, GL layer, era alignment)."""

    module_id: str
    rule_id: str
    message: str
    severity: ScanSeverity
    suggestion: str = ""
    file_path: str | None = None
    line_number: int | None = None


class ScanViolation(BaseModel):
    """A cross-boundary or compliance violation."""

    boundary: str
    file: str
    pattern: str
    reason: str
    severity: ScanSeverity = ScanSeverity.HIGH
    action: str = ""


class RemediationItem(BaseModel):
    """An item that requires auto-remediation."""

    module_id: str
    issue: str
    action: str
    severity: ScanSeverity = ScanSeverity.HIGH


class ScanSummary(BaseModel):
    """High-level summary of a full scan run."""

    total: int = 0
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    pass_rate: float = 0.0
    violations_count: int = 0
    drift_count: int = 0
    remediation_count: int = 0
    scan_completed_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )


class FullScanReport(BaseModel):
    """Complete report produced by a full scan run."""

    scan_id: str
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    scanner_version: str = "3.0.0"
    mode: str = "autonomous"
    repo_root: str = ""
    total_modules: int = 0
    modules: list[ModuleScanResult] = Field(default_factory=list)
    summary: ScanSummary = Field(default_factory=ScanSummary)
    violations: list[ScanViolation] = Field(default_factory=list)
    drift_detected: list[DriftRecord] = Field(default_factory=list)
    remediation_required: list[RemediationItem] = Field(default_factory=list)
    semantic_findings: list[SemanticFinding] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# HashScanner
# ---------------------------------------------------------------------------


class HashScanner:
    """Computes and compares content hashes for files and directories.

    Uses SHA-256 with deterministic ordering (sorted relative paths) to
    produce reproducible hashes regardless of filesystem enumeration order.
    """

    ALGORITHM = "sha256"
    CHUNK_SIZE = 8192

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        """Return the hex SHA-256 digest of raw *data*."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def hash_text(text: str, *, encoding: str = "utf-8") -> str:
        """Return the hex SHA-256 digest of a text string."""
        return hashlib.sha256(text.encode(encoding)).hexdigest()

    @classmethod
    def hash_file(cls, path: Path) -> str:
        """Compute the SHA-256 hash of a single file, reading in chunks."""
        digest = hashlib.sha256()
        with path.open("rb") as fh:
            for chunk in iter(lambda: fh.read(cls.CHUNK_SIZE), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @classmethod
    def hash_directory(cls, directory: Path) -> str:
        """Compute a deterministic SHA-256 over *all* files in *directory*.

        The hash incorporates the relative path of every file (sorted) and
        each file's individual hash, making it sensitive to renames, content
        changes, and additions/deletions.
        """
        digest = hashlib.sha256()
        for file_path in sorted(
            p for p in directory.rglob("*") if p.is_file()
        ):
            rel = str(file_path.relative_to(directory))
            digest.update(rel.encode("utf-8"))
            digest.update(cls.hash_file(file_path).encode("utf-8"))
        return digest.hexdigest()

    # ------------------------------------------------------------------
    # Baseline comparison
    # ------------------------------------------------------------------

    @classmethod
    def compare_against_baseline(
        cls,
        modules: Sequence[ModuleScanResult],
        baseline: dict[str, str],
    ) -> list[DriftRecord]:
        """Compare current module hashes against a stored *baseline* dict.

        Returns a list of :class:`DriftRecord` for every module whose hash
        differs from the baseline.
        """
        drifts: list[DriftRecord] = []
        for mod in modules:
            prev = baseline.get(mod.module_id)
            if prev is None or mod.content_hash is None:
                continue
            if prev != mod.content_hash:
                drifts.append(
                    DriftRecord(
                        module_id=mod.module_id,
                        previous_hash=prev,
                        current_hash=mod.content_hash,
                    )
                )
        return drifts


# ---------------------------------------------------------------------------
# SemanticScanner
# ---------------------------------------------------------------------------


class SemanticScanner:
    """Validates naming conventions, GL layer assignments, and NG era alignment.

    Rules checked:
    * Directory names must be kebab-case (config/boundary dirs) or snake_case
      (Python package dirs containing ``__init__.py``).
    * Python files must be snake_case.
    * YAML / JSON config files must be kebab-case.
    * GL layer annotations must reference a valid GL range.
    * Module ``era`` field (if present) must be a recognised NG era.
    """

    def __init__(self, repo_root: Path) -> None:
        self.repo_root = repo_root

    # ------------------------------------------------------------------
    # Full semantic scan
    # ------------------------------------------------------------------

    async def scan(
        self,
        modules: Sequence[ModuleScanResult],
        *,
        registry_modules: Sequence[dict[str, Any]] | None = None,
    ) -> list[SemanticFinding]:
        """Run all semantic validations, returning findings."""
        findings: list[SemanticFinding] = []
        findings.extend(self._validate_naming(modules))
        findings.extend(self._validate_gl_layers(modules, registry_modules))
        findings.extend(self._validate_era_alignment(registry_modules))
        await logger.ainfo(
            "semantic_scan_complete", finding_count=len(findings)
        )
        return findings

    # ------------------------------------------------------------------
    # Naming conventions
    # ------------------------------------------------------------------

    def _validate_naming(
        self, modules: Sequence[ModuleScanResult]
    ) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        for mod in modules:
            mod_path = self.repo_root / mod.directory
            if not mod_path.is_dir():
                continue
            findings.extend(self._check_directory_naming(mod, mod_path))
            findings.extend(self._check_file_naming(mod, mod_path))
        return findings

    def _check_directory_naming(
        self, mod: ModuleScanResult, base: Path
    ) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        for d in base.rglob("*"):
            if not d.is_dir():
                continue
            if any(part in _SKIP_DIRS for part in d.parts):
                continue
            name = d.name
            if name.startswith(".") or name.startswith("__"):
                continue
            # Python packages are allowed to be snake_case
            if (d / "__init__.py").exists():
                if not SNAKE_CASE.match(name):
                    findings.append(
                        SemanticFinding(
                            module_id=mod.module_id,
                            rule_id="GL20-NAMING-DIR-001",
                            message=(
                                f"Python package directory '{name}' does not "
                                f"follow snake_case convention"
                            ),
                            severity=ScanSeverity.MEDIUM,
                            suggestion=f"Rename to '{name.replace('-', '_')}'",
                            file_path=str(d.relative_to(self.repo_root)),
                        )
                    )
                continue
            # Non-package directories should be kebab-case
            if "_" in name and not name.startswith("_"):
                findings.append(
                    SemanticFinding(
                        module_id=mod.module_id,
                        rule_id="GL20-NAMING-DIR-002",
                        message=(
                            f"Directory '{name}' uses underscores; "
                            f"kebab-case is required"
                        ),
                        severity=ScanSeverity.MEDIUM,
                        suggestion=f"Rename to '{name.replace('_', '-')}'",
                        file_path=str(d.relative_to(self.repo_root)),
                    )
                )
        return findings

    def _check_file_naming(
        self, mod: ModuleScanResult, base: Path
    ) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        for f in base.rglob("*"):
            if not f.is_file():
                continue
            if any(part in _SKIP_DIRS for part in f.parts):
                continue
            stem = f.stem
            suffix = f.suffix.lower()
            # Python files: must be snake_case
            if suffix == ".py":
                if stem.startswith("__") and stem.endswith("__"):
                    continue
                if "-" in stem:
                    findings.append(
                        SemanticFinding(
                            module_id=mod.module_id,
                            rule_id="GL20-NAMING-FILE-001",
                            message=(
                                f"Python file '{f.name}' uses hyphens; "
                                f"snake_case is required"
                            ),
                            severity=ScanSeverity.HIGH,
                            suggestion=(
                                f"Rename to "
                                f"'{stem.replace('-', '_')}{suffix}'"
                            ),
                            file_path=str(f.relative_to(self.repo_root)),
                        )
                    )
            # YAML / JSON configs: must be kebab-case
            elif suffix in {".yaml", ".yml", ".json"}:
                if stem.startswith("GL") and re.match(r"^GL\d{2}", stem):
                    continue
                if stem in {
                    "package",
                    "package-lock",
                    "tsconfig",
                    "Dockerfile",
                }:
                    continue
                if "_" in stem:
                    findings.append(
                        SemanticFinding(
                            module_id=mod.module_id,
                            rule_id="GL20-NAMING-FILE-002",
                            message=(
                                f"Config file '{f.name}' uses underscores; "
                                f"kebab-case is required"
                            ),
                            severity=ScanSeverity.MEDIUM,
                            suggestion=(
                                f"Rename to "
                                f"'{stem.replace('_', '-')}{suffix}'"
                            ),
                            file_path=str(f.relative_to(self.repo_root)),
                        )
                    )
        return findings

    # ------------------------------------------------------------------
    # GL layer validation
    # ------------------------------------------------------------------

    def _validate_gl_layers(
        self,
        modules: Sequence[ModuleScanResult],
        registry_modules: Sequence[dict[str, Any]] | None,
    ) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        registry_map: dict[str, dict[str, Any]] = {}
        if registry_modules:
            registry_map = {m["id"]: m for m in registry_modules}

        for mod in modules:
            reg = registry_map.get(mod.module_id, {})
            declared_layer = reg.get("gl_layer") or mod.gl_layer
            if declared_layer and declared_layer not in VALID_GL_LAYERS:
                findings.append(
                    SemanticFinding(
                        module_id=mod.module_id,
                        rule_id="GL-LAYER-001",
                        message=(
                            f"GL layer '{declared_layer}' is not a "
                            f"recognised governance layer"
                        ),
                        severity=ScanSeverity.HIGH,
                        suggestion=(
                            f"Use one of: {sorted(VALID_GL_LAYERS)}"
                        ),
                    )
                )
            if not mod.has_gl_annotation:
                findings.append(
                    SemanticFinding(
                        module_id=mod.module_id,
                        rule_id="GL-ANNOTATION-001",
                        message="Module has no @GL-governed annotation",
                        severity=ScanSeverity.MEDIUM,
                        suggestion=(
                            "Add @GL-governed and @GL-layer annotations "
                            "to the module entry point"
                        ),
                    )
                )
        return findings

    # ------------------------------------------------------------------
    # NG era alignment
    # ------------------------------------------------------------------

    def _validate_era_alignment(
        self,
        registry_modules: Sequence[dict[str, Any]] | None,
    ) -> list[SemanticFinding]:
        findings: list[SemanticFinding] = []
        if not registry_modules:
            return findings
        for mod in registry_modules:
            era = mod.get("era")
            if era and era not in VALID_NG_ERAS:
                findings.append(
                    SemanticFinding(
                        module_id=mod.get("id", "unknown"),
                        rule_id="NG-ERA-001",
                        message=(
                            f"Era '{era}' is not a recognised NG era"
                        ),
                        severity=ScanSeverity.HIGH,
                        suggestion=f"Use one of: {sorted(VALID_NG_ERAS)}",
                    )
                )
        return findings


# ---------------------------------------------------------------------------
# ModuleScanner
# ---------------------------------------------------------------------------

# Cross-boundary violation rules (matches reference autonomous_scanner.py)
_CROSS_BOUNDARY_RULES: dict[str, dict[str, Any]] = {
    "responsibility-governance-anchor-boundary": {
        "forbidden_patterns": [r"\.sh$", r"\.py$", r"Dockerfile"],
        "reason": "Anchor boundary must not contain executable scripts",
    },
    "responsibility-governance-specs-boundary": {
        "forbidden_patterns": [r"\.sh$", r"\.py$", r"Dockerfile", r"\.tmp$"],
        "reason": "Specs boundary must not contain scripts or temp files",
    },
    "responsibility-guardrails-boundary": {
        "forbidden_patterns": [r"scanner.*\.py$", r"scan.*\.sh$"],
        "reason": "Guardrails boundary must not contain scan scripts",
    },
    "responsibility-gateway-boundary": {
        "forbidden_patterns": [r"deploy.*\.sh$", r"Dockerfile"],
        "reason": "Gateway boundary must not contain deploy scripts",
    },
    "responsibility-mnga-architecture-boundary": {
        "forbidden_patterns": [r"ops.*\.sh$", r"runbook.*\.yaml$"],
        "reason": "MNGA boundary must not contain ops runbooks",
    },
    "responsibility-generation-boundary": {
        "forbidden_patterns": [r"\.bin$", r"\.tar\.gz$", r"\.zip$", r"\.jar$"],
        "reason": "Generation boundary must not contain binaries",
    },
}


class ModuleScanner:
    """Filesystem scanner for governance-managed modules.

    Given a repository root and a module registry (list of module descriptors),
    the scanner walks the tree, checks GL annotations, detects drift, and
    produces a :class:`FullScanReport`.
    """

    def __init__(
        self,
        repo_root: str | Path,
        *,
        registry_modules: Sequence[dict[str, Any]] | None = None,
        previous_module_hashes: dict[str, str] | None = None,
    ) -> None:
        self.repo_root = Path(repo_root).resolve()
        self.registry_modules = list(registry_modules or [])
        self.previous_hashes = dict(previous_module_hashes or {})
        self._hash_scanner = HashScanner()
        self._semantic_scanner = SemanticScanner(self.repo_root)
        self._scan_id = (
            f"SCAN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}"
        )

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    async def scan_all(self) -> FullScanReport:
        """Execute a full scan of all registered modules.

        Returns a :class:`FullScanReport` with per-module results, drift
        records, violations, semantic findings, and a summary.
        """
        await logger.ainfo(
            "scan_started",
            scan_id=self._scan_id,
            module_count=len(self.registry_modules),
        )

        report = FullScanReport(
            scan_id=self._scan_id,
            repo_root=str(self.repo_root),
            total_modules=len(self.registry_modules),
        )

        passed = failed = warnings = 0

        for mod_def in self.registry_modules:
            result = await self._scan_module(mod_def, report)
            report.modules.append(result)
            if result.status == ScanStatus.PASS:
                passed += 1
            elif result.status == ScanStatus.FAIL:
                failed += 1
            else:
                warnings += 1

        # Cross-boundary violations
        report.violations = await self._scan_cross_boundary_violations()

        # Drift detection
        report.drift_detected = HashScanner.compare_against_baseline(
            report.modules, self.previous_hashes
        )

        # Semantic validation
        report.semantic_findings = await self._semantic_scanner.scan(
            report.modules, registry_modules=self.registry_modules
        )

        # Build summary
        total = len(self.registry_modules)
        report.summary = ScanSummary(
            total=total,
            passed=passed,
            failed=failed,
            warnings=warnings,
            pass_rate=round(passed / max(total, 1) * 100, 2),
            violations_count=len(report.violations),
            drift_count=len(report.drift_detected),
            remediation_count=len(report.remediation_required),
        )

        await logger.ainfo(
            "scan_completed",
            scan_id=self._scan_id,
            passed=passed,
            failed=failed,
            warnings=warnings,
            violations=len(report.violations),
            drift=len(report.drift_detected),
        )

        return report

    # ------------------------------------------------------------------
    # Per-module scan
    # ------------------------------------------------------------------

    async def _scan_module(
        self,
        mod_def: dict[str, Any],
        report: FullScanReport,
    ) -> ModuleScanResult:
        module_id: str = mod_def["id"]
        directory: str = mod_def["directory"]
        module_path = self.repo_root / directory

        result = ModuleScanResult(module_id=module_id, directory=directory)

        # Check 1 -- directory existence
        exists = module_path.is_dir()
        result.checks.append(
            CheckResult(
                check="directory_exists",
                passed=exists,
                detail=f"{'exists' if exists else 'missing'}: {directory}",
                severity=ScanSeverity.CRITICAL,
            )
        )
        if not exists:
            result.status = ScanStatus.FAIL
            report.remediation_required.append(
                RemediationItem(
                    module_id=module_id,
                    issue="Directory does not exist",
                    action=f"mkdir -p {directory}",
                    severity=ScanSeverity.CRITICAL,
                )
            )
            await logger.awarn("module_dir_missing", module_id=module_id)
            return result

        # Check 2 -- README.md existence
        readme_exists = (module_path / "README.md").is_file()
        result.checks.append(
            CheckResult(
                check="readme_exists",
                passed=readme_exists,
                detail=f"README.md {'present' if readme_exists else 'missing'}",
                severity=ScanSeverity.HIGH,
            )
        )
        if not readme_exists:
            report.remediation_required.append(
                RemediationItem(
                    module_id=module_id,
                    issue="Missing README.md",
                    action=f"generate_readme:{directory}",
                    severity=ScanSeverity.HIGH,
                )
            )

        # Check 3 -- file count / has content
        files = [p for p in module_path.rglob("*") if p.is_file()]
        result.file_count = len(files)
        has_content = len(files) > 0
        result.checks.append(
            CheckResult(
                check="has_content",
                passed=has_content,
                detail=f"file_count={len(files)}",
                severity=ScanSeverity.HIGH,
            )
        )

        # Check 4 -- content hash
        try:
            dir_hash = HashScanner.hash_directory(module_path)
            result.content_hash = dir_hash
            result.checks.append(
                CheckResult(
                    check="hash_computed",
                    passed=True,
                    detail=f"SHA-256: {dir_hash[:16]}...",
                )
            )
        except Exception as exc:
            result.checks.append(
                CheckResult(
                    check="hash_computed",
                    passed=False,
                    detail=f"Hash computation failed: {exc}",
                    severity=ScanSeverity.MEDIUM,
                )
            )

        # Check 5 -- GL annotation detection
        gl_annotated = False
        gl_layer: str | None = None
        gl_semantic: str | None = None
        for py in module_path.rglob("*.py"):
            try:
                head = py.read_text(encoding="utf-8", errors="ignore")[:2048]
            except OSError:
                continue
            if GL_ANNOTATION_PATTERN.search(head):
                gl_annotated = True
            layer_m = GL_LAYER_PATTERN.search(head)
            if layer_m:
                gl_layer = layer_m.group("layer")
            sem_m = GL_SEMANTIC_PATTERN.search(head)
            if sem_m:
                gl_semantic = sem_m.group("semantic")
            if gl_annotated and gl_layer:
                break

        result.has_gl_annotation = gl_annotated
        result.gl_layer = gl_layer
        result.gl_semantic = gl_semantic
        result.checks.append(
            CheckResult(
                check="gl_annotation",
                passed=gl_annotated,
                detail=(
                    f"GL annotation {'found' if gl_annotated else 'missing'}"
                    + (f" (layer={gl_layer})" if gl_layer else "")
                ),
                severity=ScanSeverity.MEDIUM,
            )
        )

        # Determine final status
        critical_fail = any(
            not c.passed and c.severity in (ScanSeverity.CRITICAL,)
            for c in result.checks
        )
        high_fail = any(
            not c.passed and c.severity == ScanSeverity.HIGH
            for c in result.checks
        )
        if critical_fail:
            result.status = ScanStatus.FAIL
        elif high_fail:
            result.status = ScanStatus.WARNING
        else:
            result.status = ScanStatus.PASS

        await logger.ainfo(
            "module_scanned",
            module_id=module_id,
            status=result.status,
            file_count=result.file_count,
        )
        return result

    # ------------------------------------------------------------------
    # Cross-boundary violations
    # ------------------------------------------------------------------

    async def _scan_cross_boundary_violations(self) -> list[ScanViolation]:
        violations: list[ScanViolation] = []
        for boundary_dir, rules in _CROSS_BOUNDARY_RULES.items():
            boundary_path = self.repo_root / boundary_dir
            if not boundary_path.is_dir():
                continue
            for file_path in boundary_path.rglob("*"):
                if not file_path.is_file():
                    continue
                filename = file_path.name
                for pattern in rules["forbidden_patterns"]:
                    if re.search(pattern, filename):
                        violations.append(
                            ScanViolation(
                                boundary=boundary_dir,
                                file=str(
                                    file_path.relative_to(self.repo_root)
                                ),
                                pattern=pattern,
                                reason=rules["reason"],
                                action="move_to_correct_boundary",
                            )
                        )
                        await logger.awarn(
                            "cross_boundary_violation",
                            boundary=boundary_dir,
                            file=filename,
                        )
        return violations


__all__ = [
    # Models
    "ScanSeverity",
    "ScanStatus",
    "CheckResult",
    "ModuleScanResult",
    "DriftRecord",
    "SemanticFinding",
    "ScanViolation",
    "RemediationItem",
    "ScanSummary",
    "FullScanReport",
    # Scanners
    "HashScanner",
    "SemanticScanner",
    "ModuleScanner",
]
