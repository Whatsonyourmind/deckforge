"""Cross-slide refiner -- stage 4 of the content generation pipeline.

Reviews all slides together for terminology consistency, redundancy
elimination, and narrative coherence.
"""

from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING

from deckforge.content.models import ExpandedSlide, ParsedIntent, RefinedPresentation
from deckforge.content.prompts.refine import REFINE_SYSTEM_PROMPT, REFINE_USER_TEMPLATE

if TYPE_CHECKING:
    from deckforge.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class CrossSlideRefiner:
    """Refine all slides together for cross-slide consistency.

    Sends the entire slide set to the LLM in one call to check for
    terminology consistency, redundancy, tense agreement, and flow.
    """

    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    async def refine(
        self,
        slides: list[ExpandedSlide],
        intent: ParsedIntent,
    ) -> RefinedPresentation:
        """Refine a set of expanded slides for consistency and impact.

        Args:
            slides: All expanded slides from the SlideWriter.
            intent: The presentation intent for context.

        Returns:
            RefinedPresentation with refined slides and a log of changes.
        """
        slides_json = json.dumps(
            [s.model_dump() for s in slides],
            indent=2,
        )

        messages = [
            {"role": "system", "content": REFINE_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": REFINE_USER_TEMPLATE.format(
                    topic=intent.topic,
                    audience=intent.audience.value,
                    tone=intent.tone.value,
                    purpose=intent.purpose.value,
                    slides_json=slides_json,
                ),
            },
        ]

        refined = await self._router.complete_structured(
            messages,
            response_model=RefinedPresentation,
            temperature=0.2,
        )

        logger.info(
            "Refinement complete: %d changes made across %d slides",
            len(refined.changes_made),
            len(refined.slides),
        )
        return refined
