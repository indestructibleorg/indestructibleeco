"""Compliance analysis utilities for the governance search layer.

Provides the ``ComplianceAnalyzer`` class which operates on data from the
:class:`~search.indexer.ModuleIndexer` to produce compliance distribution
reports, identify risk hotspots, compute trend data, and score dependency-
related risk.

@GL-governed
@GL-layer: GL30-49
@GL-semantic: compliance-analysis
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import TYPE_CHECKING

import structlog
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from search.indexer import IndexEntry, ModuleIndexer

logger = structlog.get_logger(__name__)


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class RiskLevel(StrEnum):
    """Qualitative risk assessment derived from a numeric score."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NONE = "none"

    @classmethod
    def from_score(cls, score: float) -> RiskLevel:
        """Map a 0-100 risk score to a qualitative level."""
        if score >= 80.0:
            return cls.CRITICAL
        if score >= 60.0:
            return cls.HIGH
        if score >= 40.0:
            return cls.MEDIUM
        if score >= 20.0:
            return cls.LOW
        return cls.NONE


# ---------------------------------------------------------------------------
# Report models
# ---------------------------------------------------------------------------

class ComplianceDistribution(BaseModel):
    """Breakdown of compliance statuses, optionally grouped by GL layer."""

    total_modules: int = 0
    compliant: int = 0
    non_compliant: int = 0
    partially_compliant: int = 0
    unknown: int = 0
    exempt: int = 0
    compliance_rate: float = Field(
        default=0.0,
        description="Percentage of modules in a passing state (compliant + exempt).",
    )
    by_gl_layer: dict[str, dict[str, int]] = Field(default_factory=dict)


class Hotspot(BaseModel):
    """A module identified as a risk hotspot requiring attention.

    Attributes:
        module_id: Identifier of the flagged module.
        name: Human-readable module name.
        gl_layer: Governance layer designation.
        risk_score: Numeric 0-100 risk score (higher is worse).
        risk_level: Qualitative risk level derived from the score.
        reasons: Human-readable explanations for the elevated risk.
    """

    module_id: str
    name: str
    gl_layer: str
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel = RiskLevel.NONE
    reasons: list[str] = Field(default_factory=list)


class TrendPoint(BaseModel):
    """A single data point in a compliance trend time-series."""

    timestamp: datetime
    total_modules: int = 0
    compliant_count: int = 0
    non_compliant_count: int = 0
    compliance_rate: float = 0.0


class ComplianceReport(BaseModel):
    """Comprehensive compliance analysis report.

    Attributes:
        generated_at: UTC timestamp when the report was produced.
        distribution: Global and per-layer compliance distribution.
        hotspots: Modules with the highest risk scores.
        trend: Time-series of compliance rate snapshots.
        summary: Free-form summary statistics.
    """

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
    )
    distribution: ComplianceDistribution = Field(
        default_factory=ComplianceDistribution,
    )
    hotspots: list[Hotspot] = Field(default_factory=list)
    trend: list[TrendPoint] = Field(default_factory=list)
    summary: dict[str, str | int | float] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Risk scoring weights
# ---------------------------------------------------------------------------

_STATUS_RISK_WEIGHTS: dict[str, float] = {
    "non_compliant": 60.0,
    "partially_compliant": 30.0,
    "unknown": 45.0,
    "compliant": 0.0,
    "exempt": 0.0,
}

_STALE_THRESHOLD_DAYS: int = 30


# ---------------------------------------------------------------------------
# Analyzer
# ---------------------------------------------------------------------------

class ComplianceAnalyzer:
    """Analyses compliance data from the governance module index.

    The analyzer reads entries from a :class:`ModuleIndexer` and produces
    reports, hotspot lists, trend data, and risk scores.  All public methods
    are ``async`` for consistent composition within async pipelines.
    """

    def __init__(self, indexer: ModuleIndexer) -> None:
        self._indexer = indexer
        logger.info("compliance_analyzer_initialised")

    # -- distribution -------------------------------------------------------

    async def analyze_compliance_distribution(self) -> ComplianceDistribution:
        """Compute the compliance distribution across all indexed modules.

        Returns:
            A ``ComplianceDistribution`` summarising global and per-layer
            compliance counts plus the overall compliance rate.
        """
        entries = self._indexer.get_all_entries()

        status_counter: Counter[str] = Counter()
        layer_counters: dict[str, Counter[str]] = {}

        for entry in entries:
            status_counter[entry.compliance_status] += 1
            layer_counters.setdefault(entry.gl_layer, Counter())[
                entry.compliance_status
            ] += 1

        total = len(entries)
        compliant = status_counter.get("compliant", 0)
        exempt = status_counter.get("exempt", 0)
        passing = compliant + exempt
        rate = (passing / total * 100.0) if total > 0 else 0.0

        dist = ComplianceDistribution(
            total_modules=total,
            compliant=compliant,
            non_compliant=status_counter.get("non_compliant", 0),
            partially_compliant=status_counter.get("partially_compliant", 0),
            unknown=status_counter.get("unknown", 0),
            exempt=exempt,
            compliance_rate=round(rate, 2),
            by_gl_layer={
                layer: dict(counts) for layer, counts in sorted(layer_counters.items())
            },
        )

        logger.info(
            "compliance_distribution_computed",
            total=total,
            compliance_rate=dist.compliance_rate,
        )
        return dist

    # -- hotspots -----------------------------------------------------------

    async def find_hotspots(
        self,
        *,
        top_n: int = 10,
        min_risk_score: float = 20.0,
    ) -> list[Hotspot]:
        """Identify modules with the highest risk scores.

        Risk is computed from compliance status, data staleness, and tag
        indicators.  Results are sorted descending by ``risk_score``.

        Args:
            top_n: Maximum number of hotspots to return.
            min_risk_score: Minimum score threshold for inclusion.

        Returns:
            A list of ``Hotspot`` instances, highest risk first.
        """
        entries = self._indexer.get_all_entries()
        now = datetime.now(timezone.utc)
        hotspots: list[Hotspot] = []

        for entry in entries:
            score, reasons = self._compute_risk(entry, now)
            if score >= min_risk_score:
                hotspots.append(
                    Hotspot(
                        module_id=entry.module_id,
                        name=entry.name,
                        gl_layer=entry.gl_layer,
                        risk_score=round(score, 1),
                        risk_level=RiskLevel.from_score(score),
                        reasons=reasons,
                    )
                )

        hotspots.sort(key=lambda h: h.risk_score, reverse=True)
        result = hotspots[:top_n]

        logger.info(
            "hotspots_identified",
            total_candidates=len(hotspots),
            returned=len(result),
        )
        return result

    # -- trends -------------------------------------------------------------

    async def trend_analysis(
        self,
        *,
        period_days: int = 30,
        interval_days: int = 7,
    ) -> list[TrendPoint]:
        """Generate a compliance trend time-series from the current index.

        Because the indexer only holds the *current* snapshot, this method
        synthesises approximate trend points by bucketing entries according
        to their ``last_updated`` timestamps.  For a production system with
        historical storage this would query persisted snapshots instead.

        Args:
            period_days: How far back to look.
            interval_days: Bucket width in days.

        Returns:
            A chronologically ordered list of ``TrendPoint`` instances.
        """
        entries = self._indexer.get_all_entries()
        now = datetime.now(timezone.utc)
        start = now - timedelta(days=period_days)

        buckets: dict[datetime, list[IndexEntry]] = {}
        cursor = start
        while cursor <= now:
            buckets[cursor] = []
            cursor += timedelta(days=interval_days)

        bucket_keys = sorted(buckets.keys())

        for entry in entries:
            for i, bk in enumerate(bucket_keys):
                upper = bucket_keys[i + 1] if i + 1 < len(bucket_keys) else now
                if bk <= entry.last_updated < upper:
                    buckets[bk].append(entry)
                    break
            else:
                if entry.last_updated >= bucket_keys[-1]:
                    buckets[bucket_keys[-1]].append(entry)

        trend: list[TrendPoint] = []
        cumulative: list[IndexEntry] = []
        for bk in bucket_keys:
            cumulative.extend(buckets[bk])
            total = len(cumulative)
            compliant = sum(
                1 for e in cumulative
                if e.compliance_status in {"compliant", "exempt"}
            )
            non_compliant = sum(
                1 for e in cumulative if e.compliance_status == "non_compliant"
            )
            rate = (compliant / total * 100.0) if total > 0 else 0.0
            trend.append(
                TrendPoint(
                    timestamp=bk,
                    total_modules=total,
                    compliant_count=compliant,
                    non_compliant_count=non_compliant,
                    compliance_rate=round(rate, 2),
                )
            )

        logger.info(
            "trend_analysis_complete",
            period_days=period_days,
            data_points=len(trend),
        )
        return trend

    # -- dependency risk score ----------------------------------------------

    async def dependency_risk_score(self, module_id: str) -> float:
        """Compute a dependency-aware risk score for a specific module.

        The score combines the module's own compliance risk with a
        neighbourhood penalty based on how many other modules in the same
        GL layer are non-compliant.

        Args:
            module_id: Identifier of the module to evaluate.

        Returns:
            A float in ``[0.0, 100.0]`` where higher means riskier.
            Returns ``0.0`` if the module is not found in the index.
        """
        entry = self._indexer.get_entry(module_id)
        if entry is None:
            logger.warning("dependency_risk_module_not_found", module_id=module_id)
            return 0.0

        now = datetime.now(timezone.utc)
        base_score, _ = self._compute_risk(entry, now)

        siblings = [
            e for e in self._indexer.get_all_entries()
            if e.gl_layer == entry.gl_layer and e.module_id != module_id
        ]

        if not siblings:
            return min(round(base_score, 1), 100.0)

        non_compliant_siblings = sum(
            1 for s in siblings if s.compliance_status == "non_compliant"
        )
        sibling_ratio = non_compliant_siblings / len(siblings)
        neighbourhood_penalty = sibling_ratio * 25.0

        final = min(base_score + neighbourhood_penalty, 100.0)

        logger.info(
            "dependency_risk_computed",
            module_id=module_id,
            base_score=round(base_score, 1),
            neighbourhood_penalty=round(neighbourhood_penalty, 1),
            final_score=round(final, 1),
        )
        return round(final, 1)

    # -- full report --------------------------------------------------------

    async def generate_report(
        self,
        *,
        hotspot_limit: int = 10,
        trend_period_days: int = 30,
    ) -> ComplianceReport:
        """Generate a comprehensive ``ComplianceReport``.

        Combines distribution, hotspots, and trend analysis into a single
        report artefact.

        Args:
            hotspot_limit: Maximum hotspots to include.
            trend_period_days: Lookback window for trend data.

        Returns:
            A fully populated ``ComplianceReport``.
        """
        distribution = await self.analyze_compliance_distribution()
        hotspots = await self.find_hotspots(top_n=hotspot_limit)
        trend = await self.trend_analysis(period_days=trend_period_days)

        report = ComplianceReport(
            distribution=distribution,
            hotspots=hotspots,
            trend=trend,
            summary={
                "total_modules": distribution.total_modules,
                "compliance_rate": distribution.compliance_rate,
                "hotspot_count": len(hotspots),
                "worst_layer": self._worst_layer(distribution),
            },
        )

        logger.info(
            "compliance_report_generated",
            total=distribution.total_modules,
            compliance_rate=distribution.compliance_rate,
            hotspots=len(hotspots),
        )
        return report

    # -- private helpers ----------------------------------------------------

    @staticmethod
    def _compute_risk(
        entry: IndexEntry,
        now: datetime,
    ) -> tuple[float, list[str]]:
        """Score the risk for a single entry.

        Returns:
            A ``(score, reasons)`` tuple.
        """
        score = 0.0
        reasons: list[str] = []

        status_weight = _STATUS_RISK_WEIGHTS.get(entry.compliance_status, 25.0)
        if status_weight > 0:
            score += status_weight
            reasons.append(f"compliance_status={entry.compliance_status}")

        age = now - entry.last_updated
        if age > timedelta(days=_STALE_THRESHOLD_DAYS):
            staleness_penalty = min((age.days - _STALE_THRESHOLD_DAYS) * 0.5, 25.0)
            score += staleness_penalty
            reasons.append(f"stale_data ({age.days} days old)")

        critical_tags = {"critical", "deprecated", "eol", "unmaintained"}
        matched_tags = critical_tags.intersection(t.lower() for t in entry.tags)
        if matched_tags:
            tag_penalty = len(matched_tags) * 5.0
            score += tag_penalty
            reasons.append(f"risk_tags={sorted(matched_tags)}")

        return min(score, 100.0), reasons

    @staticmethod
    def _worst_layer(distribution: ComplianceDistribution) -> str:
        """Identify the GL layer with the lowest compliance ratio."""
        worst = ""
        worst_rate = 101.0

        for layer, counts in distribution.by_gl_layer.items():
            total = sum(counts.values())
            if total == 0:
                continue
            passing = counts.get("compliant", 0) + counts.get("exempt", 0)
            rate = passing / total * 100.0
            if rate < worst_rate:
                worst_rate = rate
                worst = layer

        return worst or "n/a"
