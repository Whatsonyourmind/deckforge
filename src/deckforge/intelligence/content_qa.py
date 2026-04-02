"""Convergence-based content QA — uses OraClaw's ICM convergence scoring
to validate AI-generated content across multiple LLM providers.

When multiple LLMs agree on content quality, convergence is high and the
content is trusted. When LLMs disagree, the content is flagged for
revision or the highest-confidence provider's output is used.
"""

from __future__ import annotations

import logging
from typing import Any

from deckforge.intelligence.client import get_oraclaw

logger = logging.getLogger(__name__)


class ConvergenceQA:
    """Multi-LLM content quality assessment via convergence scoring.

    Usage:
        qa = ConvergenceQA()
        result = await qa.score_content(
            scores={"claude": 0.85, "openai": 0.82, "gemini": 0.78},
            confidences={"claude": 0.9, "openai": 0.85, "gemini": 0.7},
        )
        if result and result["convergence_score"] > 0.7:
            # Content is trustworthy — models agree
        else:
            # Low convergence — consider regenerating
    """

    async def score_content(
        self,
        scores: dict[str, float],
        confidences: dict[str, float] | None = None,
    ) -> dict[str, Any] | None:
        """Score content quality using multi-model convergence.

        Args:
            scores: Quality scores from each LLM provider (0.0-1.0).
                Example: {"claude": 0.85, "openai": 0.82, "gemini": 0.78}
            confidences: Optional confidence levels per provider (0.0-1.0).

        Returns:
            Dict with convergence_score, agreement level, recommendation,
            or None if OraClaw is unavailable.
        """
        client = get_oraclaw()
        if client is None:
            return None

        # Build sources for OraClaw convergence endpoint
        sources = []
        for provider_id, score in scores.items():
            source: dict[str, Any] = {
                "id": provider_id,
                "name": provider_id,
                "probability": score,
            }
            if confidences and provider_id in confidences:
                source["confidence"] = confidences[provider_id]
            sources.append(source)

        result = await client.convergence_score(sources=sources)

        if result is None:
            return None

        # Extract convergence metrics and add recommendation
        convergence_score = result.get("icm", result.get("score", 0.0))
        enhanced = {
            "convergence_score": convergence_score,
            "raw_result": result,
            "sources_count": len(scores),
            "recommendation": _recommend(convergence_score),
        }

        logger.info(
            "Content convergence: %.3f across %d providers -> %s",
            convergence_score, len(scores), enhanced["recommendation"],
        )

        return enhanced

    async def score_slide_content(
        self,
        slide_scores: list[dict[str, float]],
    ) -> list[dict[str, Any] | None]:
        """Score multiple slides' content in sequence.

        Args:
            slide_scores: List of per-slide score dicts from multiple providers.

        Returns:
            List of convergence results, one per slide.
        """
        results = []
        for scores in slide_scores:
            result = await self.score_content(scores)
            results.append(result)
        return results


def _recommend(convergence_score: float) -> str:
    """Map convergence score to an actionable recommendation."""
    if convergence_score >= 0.8:
        return "accept"
    if convergence_score >= 0.6:
        return "accept_with_review"
    if convergence_score >= 0.4:
        return "revise"
    return "regenerate"
