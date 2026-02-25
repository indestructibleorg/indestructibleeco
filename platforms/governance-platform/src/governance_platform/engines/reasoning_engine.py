"""ReasoningEngine — dual-path retrieval with arbitration.

Performs internal retrieval (knowledge base), external retrieval (simulated),
then arbitrates between them based on confidence scores to produce a final answer.
"""

from __future__ import annotations

import hashlib
import time
from typing import Any

from platform_shared.protocols.engine import Engine, EngineStatus

from governance_platform.domain.entities import ReasoningQuery, ReasoningResult
from governance_platform.domain.events import ReasoningCompleted
from governance_platform.domain.exceptions import ReasoningError
from governance_platform.domain.value_objects import ArbitrationDecision, ReasoningConfidence


# -- Simulated knowledge bases -------------------------------------------------

_INTERNAL_KB: dict[str, tuple[str, float]] = {
    "deployment": (
        "All deployments must pass quality gates and policy checks before proceeding to production.",
        0.92,
    ),
    "security": (
        "Security policies require encryption at rest, TLS 1.3 in transit, and least-privilege access.",
        0.88,
    ),
    "compliance": (
        "Compliance audits run on a quarterly cycle; all platforms must maintain FULL compliance level.",
        0.90,
    ),
    "governance": (
        "The governance platform enforces policies, quality gates, and tracks compliance across all platforms.",
        0.95,
    ),
    "rollback": (
        "Rollback procedures require approval from two governance stakeholders and a post-mortem within 48h.",
        0.85,
    ),
}

_EXTERNAL_KB: dict[str, tuple[str, float]] = {
    "deployment": (
        "Industry best practices recommend blue-green deployments with automated canary analysis.",
        0.78,
    ),
    "security": (
        "OWASP Top 10 and CIS benchmarks form the baseline for security policy compliance.",
        0.82,
    ),
    "compliance": (
        "SOC2 Type II and ISO 27001 are the most commonly required compliance frameworks.",
        0.80,
    ),
    "governance": (
        "IT governance frameworks like COBIT and ITIL provide structured governance processes.",
        0.75,
    ),
    "incident": (
        "Incident response best practices include automated detection, triage, and blameless post-mortems.",
        0.84,
    ),
}


def _keyword_match(question: str, kb: dict[str, tuple[str, float]]) -> tuple[str, float]:
    """Simple keyword-based retrieval: find best matching entry in a knowledge base."""
    question_lower = question.lower()
    best_answer = ""
    best_confidence = 0.0

    for keyword, (answer, confidence) in kb.items():
        if keyword in question_lower:
            if confidence > best_confidence:
                best_answer = answer
                best_confidence = confidence

    return best_answer, best_confidence


class ReasoningEngine:
    """Dual-path reasoning engine with internal/external retrieval and arbitration.

    Implements the shared Engine protocol for lifecycle integration.
    """

    def __init__(
        self,
        internal_kb: dict[str, tuple[str, float]] | None = None,
        external_kb: dict[str, tuple[str, float]] | None = None,
        confidence_threshold: float = 0.5,
    ) -> None:
        self._status = EngineStatus.IDLE
        self._internal_kb = internal_kb if internal_kb is not None else dict(_INTERNAL_KB)
        self._external_kb = external_kb if external_kb is not None else dict(_EXTERNAL_KB)
        self._confidence_threshold = confidence_threshold
        self._history: list[ReasoningCompleted] = []

    # -- Engine protocol -------------------------------------------------------

    @property
    def name(self) -> str:
        return "reasoning-engine"

    @property
    def status(self) -> EngineStatus:
        return self._status

    async def start(self) -> None:
        self._status = EngineStatus.RUNNING

    async def stop(self) -> None:
        self._status = EngineStatus.STOPPED

    async def execute(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Engine protocol entry point — expects {question} or {query}."""
        question = payload.get("question", "")
        sources = payload.get("sources", [])
        context = payload.get("context", {})
        result = await self.query(question, sources=sources, context=context)
        return {
            "query_id": result.query_id,
            "answer": result.answer,
            "decision": result.decision,
            "internal_answer": result.internal_answer,
            "internal_confidence": result.internal_confidence,
            "external_answer": result.external_answer,
            "external_confidence": result.external_confidence,
            "trail": result.trail,
        }

    # -- Core API --------------------------------------------------------------

    async def query(
        self,
        question: str,
        *,
        sources: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> ReasoningResult:
        """Run dual-path retrieval + arbitration for a question.

        1. Internal retrieval (knowledge base lookup)
        2. External retrieval (simulated external source)
        3. Arbitration (pick best source based on confidence)
        4. Return answer with full decision trail
        """
        query_id = f"rq-{hashlib.sha256(question.encode()).hexdigest()[:12]}"
        trail: list[str] = []

        # Step 1: Internal retrieval
        trail.append(f"[internal] Searching internal knowledge base for: {question!r}")
        internal_answer, internal_conf = _keyword_match(question, self._internal_kb)
        internal_confidence = ReasoningConfidence(internal_conf)
        if internal_answer:
            trail.append(
                f"[internal] Found answer with confidence {internal_confidence.value:.2f}"
            )
        else:
            trail.append("[internal] No matching knowledge found")

        # Step 2: External retrieval
        trail.append(f"[external] Searching external knowledge base for: {question!r}")
        external_answer, external_conf = _keyword_match(question, self._external_kb)
        external_confidence = ReasoningConfidence(external_conf)
        if external_answer:
            trail.append(
                f"[external] Found answer with confidence {external_confidence.value:.2f}"
            )
        else:
            trail.append("[external] No matching knowledge found")

        # Step 3: Arbitration
        trail.append("[arbitration] Comparing internal vs external sources")
        decision, final_answer = self._arbitrate(
            internal_answer,
            internal_confidence,
            external_answer,
            external_confidence,
            trail,
        )

        result = ReasoningResult(
            query_id=query_id,
            answer=final_answer,
            decision=decision.value,
            internal_answer=internal_answer,
            internal_confidence=internal_confidence.value,
            external_answer=external_answer,
            external_confidence=external_confidence.value,
            trail=trail,
        )

        # Record event
        self._history.append(
            ReasoningCompleted(
                query_id=query_id,
                question=question,
                decision=decision.value,
                confidence=max(internal_confidence.value, external_confidence.value),
                source_used=decision.value,
            )
        )

        return result

    def _arbitrate(
        self,
        internal_answer: str,
        internal_conf: ReasoningConfidence,
        external_answer: str,
        external_conf: ReasoningConfidence,
        trail: list[str],
    ) -> tuple[ArbitrationDecision, str]:
        """Pick the best source based on confidence. Returns (decision, final_answer)."""
        has_internal = bool(internal_answer) and internal_conf.value >= self._confidence_threshold
        has_external = bool(external_answer) and external_conf.value >= self._confidence_threshold

        if has_internal and has_external:
            # Both sources available — check if one is clearly better
            diff = abs(internal_conf.value - external_conf.value)
            if diff < 0.1:
                # Close enough: combine them (HYBRID)
                trail.append(
                    f"[arbitration] Both sources have similar confidence "
                    f"(internal={internal_conf.value:.2f}, external={external_conf.value:.2f}). "
                    f"Using HYBRID approach."
                )
                combined = f"{internal_answer} Additionally, {external_answer.lower()}"
                return ArbitrationDecision.HYBRID, combined
            elif internal_conf > external_conf:
                trail.append(
                    f"[arbitration] Internal source wins "
                    f"({internal_conf.value:.2f} > {external_conf.value:.2f})"
                )
                return ArbitrationDecision.INTERNAL, internal_answer
            else:
                trail.append(
                    f"[arbitration] External source wins "
                    f"({external_conf.value:.2f} > {internal_conf.value:.2f})"
                )
                return ArbitrationDecision.EXTERNAL, external_answer
        elif has_internal:
            trail.append("[arbitration] Only internal source available and confident enough")
            return ArbitrationDecision.INTERNAL, internal_answer
        elif has_external:
            trail.append("[arbitration] Only external source available and confident enough")
            return ArbitrationDecision.EXTERNAL, external_answer
        else:
            trail.append(
                "[arbitration] No source met the confidence threshold. REJECT."
            )
            return ArbitrationDecision.REJECT, "Unable to provide a confident answer for this query."

    @property
    def reasoning_history(self) -> list[ReasoningCompleted]:
        return list(self._history)

    def add_internal_knowledge(self, keyword: str, answer: str, confidence: float) -> None:
        """Add or update an entry in the internal knowledge base."""
        self._internal_kb[keyword] = (answer, confidence)

    def add_external_knowledge(self, keyword: str, answer: str, confidence: float) -> None:
        """Add or update an entry in the external knowledge base."""
        self._external_kb[keyword] = (answer, confidence)
