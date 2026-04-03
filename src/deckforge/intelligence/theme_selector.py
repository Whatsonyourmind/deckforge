"""Bandit-based theme selection — uses OraClaw's Multi-Armed Bandit
to learn which themes produce the highest quality presentations for
a given context (audience, purpose, industry).

Falls back to the user-specified theme when OraClaw is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any

from deckforge.intelligence.client import get_oraclaw

logger = logging.getLogger(__name__)

# Context feature encoding for contextual bandit
_AUDIENCE_FEATURES = {
    "board": [1.0, 0.0, 0.0, 0.0, 0.0],
    "investors": [0.0, 1.0, 0.0, 0.0, 0.0],
    "technical": [0.0, 0.0, 1.0, 0.0, 0.0],
    "clients": [0.0, 0.0, 0.0, 1.0, 0.0],
    "general": [0.0, 0.0, 0.0, 0.0, 1.0],
}

_PURPOSE_FEATURES = {
    "pitch": [1.0, 0.0, 0.0, 0.0],
    "report": [0.0, 1.0, 0.0, 0.0],
    "strategy": [0.0, 0.0, 1.0, 0.0],
    "education": [0.0, 0.0, 0.0, 1.0],
}

_FORMALITY_FEATURES = {
    "formal": [1.0, 0.0],
    "casual": [0.0, 1.0],
}

# Theme IDs (the 15 DeckForge themes)
_THEME_IDS = [
    "arctic-clean", "bold-impact", "classic-serif", "corporate-blue",
    "executive-dark", "finance-pro", "forest-green", "minimal-light",
    "modern-gradient", "monochrome", "ocean-depth", "soft-pastel",
    "sunset-warm", "tech-neon", "warm-earth",
]

# Sensible defaults when bandit has no history
_DEFAULT_THEME_MAP = {
    "board": "executive-dark",
    "investors": "corporate-blue",
    "technical": "tech-neon",
    "clients": "modern-gradient",
    "general": "minimal-light",
}


class BanditThemeSelector:
    """Selects the optimal theme using OraClaw's contextual bandit.

    Usage:
        selector = BanditThemeSelector()
        theme_id = await selector.select(
            audience="investors",
            purpose="pitch",
            formality="formal",
            user_theme="corporate-blue",  # user's explicit choice
        )
    """

    async def select(
        self,
        audience: str = "general",
        purpose: str = "report",
        formality: str = "formal",
        user_theme: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:
        """Select the best theme for the given context.

        If OraClaw is available, uses adaptive selection.
        Otherwise returns user_theme or a sensible default.

        Args:
            audience: Target audience type.
            purpose: Presentation purpose.
            formality: Formal or casual.
            user_theme: User's explicitly requested theme (takes priority
                if OraClaw is unavailable).
            history: Past theme performance data for learning.

        Returns:
            Theme ID string (e.g., "executive-dark").
        """
        client = get_oraclaw()
        if client is None:
            return user_theme or _DEFAULT_THEME_MAP.get(audience, "corporate-blue")

        # Build context feature vector
        context = (
            _AUDIENCE_FEATURES.get(audience, _AUDIENCE_FEATURES["general"])
            + _PURPOSE_FEATURES.get(purpose, _PURPOSE_FEATURES["report"])
            + _FORMALITY_FEATURES.get(formality, _FORMALITY_FEATURES["formal"])
        )

        # Build arms from available themes
        arms = [{"id": tid, "name": tid} for tid in _THEME_IDS]

        result = await client.contextual_bandit_select(
            arms=arms,
            context=context,
            history=history,
            alpha=0.8,
        )

        if result and "selected" in result:
            selected_id = result["selected"]["id"]
            logger.info(
                "OraClaw selected theme '%s' (expected_reward=%.3f, confidence=%.3f)",
                selected_id,
                result.get("expectedReward", 0),
                result.get("confidenceWidth", 0),
            )
            return selected_id

        # Fallback
        return user_theme or _DEFAULT_THEME_MAP.get(audience, "corporate-blue")

    async def record_reward(
        self,
        theme_id: str,
        quality_score: float,
        audience: str = "general",
        purpose: str = "report",
        formality: str = "formal",
    ) -> None:
        """Record a quality score for a theme selection to improve future choices.

        Called after QA pipeline scores the rendered presentation.

        Args:
            theme_id: The theme that was used.
            quality_score: QA pipeline score (0.0 to 1.0).
            audience: Context that was used for selection.
            purpose: Context that was used for selection.
            formality: Context that was used for selection.
        """
        # This would update the bandit's history for future selections.
        # For now, the history is passed per-request. In v0.2, we'll
        # persist theme performance data in the database.
        logger.debug(
            "Theme reward recorded: %s scored %.3f for %s/%s/%s",
            theme_id, quality_score, audience, purpose, formality,
        )
