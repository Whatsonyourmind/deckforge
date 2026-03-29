"""Intent parser -- stage 1 of the content generation pipeline.

Extracts structured ParsedIntent from a natural language prompt using the LLM.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.content.models import ParsedIntent
from deckforge.content.prompts.intent import INTENT_SYSTEM_PROMPT, INTENT_USER_TEMPLATE

if TYPE_CHECKING:
    from deckforge.ir.metadata import GenerationOptions
    from deckforge.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class IntentParser:
    """Parse a natural language prompt into a structured ParsedIntent.

    Uses the LLMRouter to call complete_structured() with the ParsedIntent
    Pydantic model as the response_model, ensuring validated output.
    """

    def __init__(self, router: LLMRouter) -> None:
        self._router = router

    async def parse(
        self,
        prompt: str,
        generation_options: GenerationOptions | None = None,
    ) -> ParsedIntent:
        """Extract intent from a presentation prompt.

        Args:
            prompt: Natural language presentation request.
            generation_options: Optional generation options to override defaults.

        Returns:
            Validated ParsedIntent with purpose, audience, tone, etc.
        """
        gen_opts_str = str(generation_options.model_dump()) if generation_options else "None"

        messages = [
            {"role": "system", "content": INTENT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": INTENT_USER_TEMPLATE.format(
                    prompt=prompt,
                    generation_options=gen_opts_str,
                ),
            },
        ]

        result = await self._router.complete_structured(
            messages,
            response_model=ParsedIntent,
            temperature=0.3,
        )

        # Override target_slide_count if generation_options specifies it
        if generation_options and generation_options.target_slide_count is not None:
            target = generation_options.target_slide_count
            if isinstance(target, list):
                target = target[0]  # Use first value from range
            result = result.model_copy(update={"target_slide_count": target})

        logger.info(
            "Parsed intent: purpose=%s, audience=%s, slides=%d",
            result.purpose.value,
            result.audience.value,
            result.target_slide_count,
        )
        return result
