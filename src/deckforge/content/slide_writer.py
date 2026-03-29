"""Slide writer -- stage 3 of the content generation pipeline.

Expands each SlideOutline into a full IR-compatible ExpandedSlide.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.content.models import ExpandedSlide, ParsedIntent, SlideOutline
from deckforge.content.prompts.expand import EXPAND_SYSTEM_PROMPT, EXPAND_USER_TEMPLATE

if TYPE_CHECKING:
    from deckforge.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class SlideWriter:
    """Expand a slide outline into a full IR-compatible slide with elements.

    Takes each SlideOutline and produces an ExpandedSlide containing
    headings, bullets, speaker notes, and layout hints.
    """

    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    async def expand(
        self,
        slide_outline: SlideOutline,
        intent: ParsedIntent,
    ) -> ExpandedSlide:
        """Expand a single slide outline into full IR elements.

        Args:
            slide_outline: The outline for this slide.
            intent: The presentation intent for context.

        Returns:
            ExpandedSlide with elements, speaker_notes, and layout_hint.
        """
        messages = [
            {"role": "system", "content": EXPAND_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": EXPAND_USER_TEMPLATE.format(
                    position=slide_outline.position,
                    slide_type=slide_outline.slide_type.value,
                    headline=slide_outline.headline,
                    key_points=", ".join(slide_outline.key_points),
                    narrative_role=slide_outline.narrative_role,
                    data_needs=", ".join(slide_outline.data_needs or []) or "None",
                    topic=intent.topic,
                    audience=intent.audience.value,
                    tone=intent.tone.value,
                    purpose=intent.purpose.value,
                ),
            },
        ]

        expanded = await self._router.complete_structured(
            messages,
            response_model=ExpandedSlide,
            temperature=0.5,
        )

        logger.debug(
            "Expanded slide %d: type=%s, elements=%d",
            slide_outline.position,
            expanded.slide_type,
            len(expanded.elements),
        )
        return expanded
