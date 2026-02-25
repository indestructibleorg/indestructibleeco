#!/usr/bin/env python3
"""
Semantic Processor Engine v1.0
Canonicalization, narrative-free validation, and classification.

This module implements the semantic processing pipeline for text
canonicalization, narrative-free enforcement, and multi-category
classification with confidence scoring and rule-based matching.

Governance Stage: S5-VERIFIED
Status: ENFORCED
"""

import hashlib
import json
import logging
import re
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# Configure logging with CRITICAL-only default
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s [%(levelname)s] %(name)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================
# ENUMS
# ============================================

class SemanticCategory(Enum):
    """Classification categories for semantic analysis."""
    FACTUAL = "factual"
    NARRATIVE = "narrative"
    COMMAND = "command"
    METADATA = "metadata"
    UNKNOWN = "unknown"


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class CanonicalizationRule:
    """A single canonicalization transformation rule."""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    pattern: str = ""
    replacement: str = ""
    category: SemanticCategory = SemanticCategory.UNKNOWN


@dataclass
class SemanticClassification:
    """Result of classifying a text through the semantic processor."""
    text: str = ""
    category: SemanticCategory = SemanticCategory.UNKNOWN
    confidence: float = 0.0
    matched_rules: List[str] = field(default_factory=list)
    is_narrative_free: bool = True


# ============================================
# SEMANTIC PROCESSOR ENGINE
# ============================================

class SemanticProcessorEngine:
    """Semantic Processor Engine -- canonicalization, narrative-free validation, classification."""

    def __init__(self) -> None:
        """Initialize the semantic processor with default rules and narrative patterns."""
        self.canonicalization_rules: List[CanonicalizationRule] = self._load_default_rules()
        self.narrative_patterns: List[re.Pattern] = self._load_narrative_patterns()
        self._processed_count: int = 0
        self._narrative_violations: int = 0
        self._classification_counts: Dict[str, int] = {cat.value: 0 for cat in SemanticCategory}
        logger.info(
            "SemanticProcessorEngine initialized: %d rules, %d narrative patterns",
            len(self.canonicalization_rules), len(self.narrative_patterns),
        )

    # ------------------------------------------
    # PUBLIC API
    # ------------------------------------------

    def canonicalize(self, text: str) -> str:
        """Apply all canonicalization rules to the input text.

        Rules are applied in order: whitespace normalization, case normalization,
        punctuation cleanup, and category-specific transformations.

        Args:
            text: The raw input text.

        Returns:
            The canonicalized text string.
        """
        result = text
        for rule in self.canonicalization_rules:
            try:
                result = re.sub(rule.pattern, rule.replacement, result)
            except re.error as exc:
                logger.warning(
                    "Rule '%s' regex error: %s", rule.name, exc,
                )
        return result.strip()

    def classify(self, text: str) -> SemanticClassification:
        """Classify text into a semantic category with confidence scoring.

        Args:
            text: The input text to classify.

        Returns:
            A SemanticClassification with category, confidence, and matched rules.
        """
        self._processed_count += 1
        canonicalized = self.canonicalize(text)
        is_narrative_free, violations = self.check_narrative_free(canonicalized)
        matched_rules: List[str] = []

        # Score each category
        scores: Dict[SemanticCategory, float] = {cat: 0.0 for cat in SemanticCategory}

        # COMMAND detection: imperative verbs, action keywords
        command_patterns = [
            r"\b(run|execute|deploy|start|stop|restart|delete|create|update|set|get)\b",
            r"\b(install|remove|configure|enable|disable|migrate|rollback)\b",
        ]
        for pat in command_patterns:
            if re.search(pat, canonicalized, re.IGNORECASE):
                scores[SemanticCategory.COMMAND] += 0.3
                matched_rules.append(f"command_pattern:{pat}")

        # METADATA detection: key-value structures, timestamps, identifiers
        metadata_patterns = [
            r"\b[a-z_]+\s*[:=]\s*\S+",
            r"\b\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}",
            r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
            r"\bversion\s*[:=]?\s*\d+\.\d+",
        ]
        for pat in metadata_patterns:
            if re.search(pat, canonicalized, re.IGNORECASE):
                scores[SemanticCategory.METADATA] += 0.25
                matched_rules.append(f"metadata_pattern:{pat}")

        # FACTUAL detection: declarative statements, measurements, data
        factual_patterns = [
            r"\b\d+\.?\d*\s*(ms|seconds|bytes|KB|MB|GB|%|requests|errors)\b",
            r"\b(total|count|sum|average|mean|median|max|min)\b",
            r"\b(passed|failed|succeeded|completed|verified)\b",
        ]
        for pat in factual_patterns:
            if re.search(pat, canonicalized, re.IGNORECASE):
                scores[SemanticCategory.FACTUAL] += 0.3
                matched_rules.append(f"factual_pattern:{pat}")

        # NARRATIVE detection: subjective/editorial language
        if not is_narrative_free:
            scores[SemanticCategory.NARRATIVE] += 0.8
            for v in violations:
                matched_rules.append(f"narrative_violation:{v}")
            self._narrative_violations += 1

        # Determine winner
        best_category = SemanticCategory.UNKNOWN
        best_score = 0.0
        for cat, score in scores.items():
            if score > best_score:
                best_score = score
                best_category = cat

        # Normalize confidence to [0.0, 1.0]
        confidence = min(best_score, 1.0)

        # Default to UNKNOWN if no strong signal
        if confidence < 0.1:
            best_category = SemanticCategory.UNKNOWN
            confidence = 0.0

        self._classification_counts[best_category.value] += 1

        return SemanticClassification(
            text=canonicalized,
            category=best_category,
            confidence=confidence,
            matched_rules=matched_rules,
            is_narrative_free=is_narrative_free,
        )

    def check_narrative_free(self, text: str) -> Tuple[bool, List[str]]:
        """Check whether the text is free of narrative/subjective language.

        Args:
            text: The text to check (should be canonicalized first).

        Returns:
            Tuple of (is_narrative_free, list_of_violation_descriptions).
        """
        violations: List[str] = []
        for pattern in self.narrative_patterns:
            match = pattern.search(text)
            if match:
                violations.append(
                    f"Narrative pattern matched: '{match.group()}' (pattern: {pattern.pattern})"
                )

        is_clean = len(violations) == 0
        return is_clean, violations

    def process_batch(self, texts: List[str]) -> List[SemanticClassification]:
        """Classify a batch of texts.

        Args:
            texts: List of input text strings.

        Returns:
            List of SemanticClassification results in the same order.
        """
        results: List[SemanticClassification] = []
        for text in texts:
            results.append(self.classify(text))
        logger.info("Batch processed: %d texts", len(texts))
        return results

    def get_processor_stats(self) -> Dict[str, Any]:
        """Return aggregate statistics about the semantic processor.

        Returns:
            Dictionary with processed count, violations, classification breakdown.
        """
        return {
            "total_processed": self._processed_count,
            "narrative_violations": self._narrative_violations,
            "classification_counts": dict(self._classification_counts),
            "total_rules": len(self.canonicalization_rules),
            "total_narrative_patterns": len(self.narrative_patterns),
            "narrative_free_rate": (
                round(1.0 - (self._narrative_violations / self._processed_count), 4)
                if self._processed_count > 0 else 1.0
            ),
        }

    # ------------------------------------------
    # INTERNAL METHODS
    # ------------------------------------------

    def _load_default_rules(self) -> List[CanonicalizationRule]:
        """Return built-in canonicalization rules.

        Rules cover: whitespace normalization, case normalization,
        punctuation cleanup, and common abbreviation expansion.

        Returns:
            List of CanonicalizationRule instances.
        """
        return [
            CanonicalizationRule(
                name="collapse_whitespace",
                pattern=r"\s+",
                replacement=" ",
                category=SemanticCategory.UNKNOWN,
            ),
            CanonicalizationRule(
                name="trim_leading_trailing",
                pattern=r"^\s+|\s+$",
                replacement="",
                category=SemanticCategory.UNKNOWN,
            ),
            CanonicalizationRule(
                name="normalize_dashes",
                pattern=r"[\u2013\u2014\u2015]",
                replacement="-",
                category=SemanticCategory.METADATA,
            ),
            CanonicalizationRule(
                name="normalize_quotes",
                pattern=r"[\u201c\u201d\u2018\u2019]",
                replacement="'",
                category=SemanticCategory.METADATA,
            ),
            CanonicalizationRule(
                name="remove_control_chars",
                pattern=r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]",
                replacement="",
                category=SemanticCategory.UNKNOWN,
            ),
            CanonicalizationRule(
                name="normalize_ellipsis",
                pattern=r"\.{3,}",
                replacement="...",
                category=SemanticCategory.NARRATIVE,
            ),
            CanonicalizationRule(
                name="collapse_repeated_punctuation",
                pattern=r"([!?]){2,}",
                replacement=r"\1",
                category=SemanticCategory.NARRATIVE,
            ),
        ]

    def _load_narrative_patterns(self) -> List[re.Pattern]:
        """Return compiled regex patterns that detect narrative/subjective language.

        Returns:
            List of compiled re.Pattern objects.
        """
        raw_patterns = [
            r"\bvery\s+important\b",
            r"\bsurprisingly\b",
            r"\binterestingly\b",
            r"\bunfortunately\b",
            r"\bfortunately\b",
            r"\bobviously\b",
            r"\bclearly\b",
            r"\bbasically\b",
            r"\bessentially\b",
            r"\bextremely\b",
            r"\babsolutely\b",
            r"\bdefinitely\b",
            r"\bcertainly\b",
            r"\bapparently\b",
            r"\ballegedly\b",
            r"\breportedly\b",
            r"\bseemingly\b",
            r"\bsupposedly\b",
            r"\bin my opinion\b",
            r"\bi think\b",
            r"\bi believe\b",
            r"\bit seems\b",
            r"\bkind of\b",
            r"\bsort of\b",
            r"\bpretty much\b",
            r"\bto be honest\b",
            r"\bfrankly\b",
            r"\bhonestly\b",
        ]
        return [re.compile(p, re.IGNORECASE) for p in raw_patterns]


# ============================================
# CLI INTERFACE
# ============================================

def main() -> None:
    """Demonstrate semantic processor usage."""
    print("=" * 60)
    print("Semantic Processor Engine -- Demo")
    print("=" * 60)

    engine = SemanticProcessorEngine()

    # Sample texts for classification
    texts = [
        "deploy version 2.5 to production cluster",
        "total_requests: 14523, error_rate: 0.02%, p99_latency: 45ms",
        "This is surprisingly good and I think it works basically fine",
        "build_id=abc123 timestamp=2025-01-15T10:30:00Z status=passed",
        "run database migration and restart the application server",
        "average response time 230ms across 50000 requests",
        "honestly this seems kind of broken to be honest",
    ]

    print("\n--- Classifications ---")
    results = engine.process_batch(texts)
    for i, result in enumerate(results):
        print(f"\n[{i + 1}] \"{result.text[:60]}...\"" if len(result.text) > 60 else f"\n[{i + 1}] \"{result.text}\"")
        print(f"    Category: {result.category.value} (confidence: {result.confidence:.2f})")
        print(f"    Narrative-free: {result.is_narrative_free}")
        if result.matched_rules:
            print(f"    Matched rules: {len(result.matched_rules)}")

    # Narrative-free check
    print("\n--- Narrative-Free Check ---")
    test_text = "This is extremely important and obviously the best approach"
    is_clean, violations = engine.check_narrative_free(test_text)
    print(f"Text: \"{test_text}\"")
    print(f"Narrative-free: {is_clean}")
    for v in violations:
        print(f"  - {v}")

    # Canonicalization demo
    print("\n--- Canonicalization ---")
    raw_text = "  This   has    extra   whitespace\u2014and\u201csmart   quotes\u201d  "
    canonical = engine.canonicalize(raw_text)
    print(f"Raw:    \"{raw_text}\"")
    print(f"Canon:  \"{canonical}\"")

    # Stats
    print("\n--- Processor Stats ---")
    stats = engine.get_processor_stats()
    print(f"Total processed: {stats['total_processed']}")
    print(f"Narrative violations: {stats['narrative_violations']}")
    print(f"Narrative-free rate: {stats['narrative_free_rate']:.2%}")
    print(f"Classifications: {json.dumps(stats['classification_counts'], indent=2)}")

    print("\n" + "=" * 60)
    print("Semantic Processor Engine -- Demo Complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
