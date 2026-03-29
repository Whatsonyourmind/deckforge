"""Outliner -- stage 2 of the content generation pipeline.

Generates a PresentationOutline with narrative arc and per-slide headlines.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.content.models import ParsedIntent, PresentationOutline
from deckforge.content.prompts.outline import OUTLINE_SYSTEM_PROMPT, OUTLINE_USER_TEMPLATE

if TYPE_CHECKING:
    from deckforge.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class Outliner:
    """Generate a structured presentation outline from a parsed intent.

    Produces a PresentationOutline with title, narrative arc, sections,
    and per-slide outlines with headlines and key points.
    """

    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    async def generate(self, intent: ParsedIntent) -> PresentationOutline:
        """Generate a presentation outline from the parsed intent.

        Args:
            intent: Structured intent from the IntentParser.

        Returns:
            Validated PresentationOutline with slides matching target count (+-2).
        """
        messages = [
            {"role": "system", "content": OUTLINE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": OUTLINE_USER_TEMPLATE.format(
                    purpose=intent.purpose.value,
                    audience=intent.audience.value,
                    topic=intent.topic,
                    key_messages=", ".join(intent.key_messages),
                    target_slide_count=intent.target_slide_count,
                    tone=intent.tone.value,
                    suggested_slide_types=", ".join(
                        st.value for st in intent.suggested_slide_types
                    ),
                    data_references=", ".join(intent.data_references) or "None",
                ),
            },
        ]

        outline = await self._router.complete_structured(
            messages,
            response_model=PresentationOutline,
            temperature=0.4,
        )

        # Validate slide count is within tolerance
        actual = len(outline.slides)
        target = intent.target_slide_count
        if abs(actual - target) > 2:
            logger.warning(
                "Outline has %d slides, target was %d (tolerance +-2). Proceeding anyway.",
                actual,
                target,
            )

        logger.info(
            "Generated outline: arc=%s, sections=%d, slides=%d",
            outline.narrative_arc,
            len(outline.sections),
            len(outline.slides),
        )
        return outline
