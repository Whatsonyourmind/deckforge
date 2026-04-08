"""Slide writer -- stage 3 of the content generation pipeline.

Expands each SlideOutline into a full IR-compatible ExpandedSlide.

Chart emission (closes STATE decision [03-01]):
After the LLM returns an ExpandedSlide, :func:`ensure_chart_element` is
applied to (a) validate any LLM-produced chart elements against the IR
schema and drop malformed ones, and (b) inject a recommender-derived
chart element when the slide is data-heavy but no valid chart was
emitted. This wires all 24 chart renderers into the NL pipeline that
previously only reached them via the direct ``/v1/render`` path.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.content.chart_injector import ensure_chart_element
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

        # Post-process: validate LLM-emitted chart elements and, when the
        # slide is data-heavy but missing a valid chart, inject one using
        # the chart recommender. Closes P1 bug from STATE decision [03-01].
        expanded = expanded.model_copy(
            update={
                "elements": ensure_chart_element(
                    slide_type=expanded.slide_type,
                    headline=expanded.title,
                    key_points=slide_outline.key_points,
                    elements=list(expanded.elements),
                )
            }
        )

        chart_count = sum(
            1 for el in expanded.elements if isinstance(el, dict) and el.get("type") == "chart"
        )

        logger.debug(
            "Expanded slide %d: type=%s, elements=%d, charts=%d",
            slide_outline.position,
            expanded.slide_type,
            len(expanded.elements),
            chart_count,
        )
        return expanded
