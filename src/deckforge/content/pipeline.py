"""Content generation pipeline -- orchestrates all 4 stages.

Chains IntentParser -> Outliner -> SlideWriter -> CrossSlideRefiner
to transform a natural language prompt into a valid Presentation IR dict.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from deckforge.content.intent_parser import IntentParser
from deckforge.content.models import ExpandedSlide
from deckforge.content.outliner import Outliner
from deckforge.content.refiner import CrossSlideRefiner
from deckforge.content.slide_writer import SlideWriter

if TYPE_CHECKING:
    from deckforge.ir.metadata import GenerationOptions
    from deckforge.llm.router import LLMRouter

logger = logging.getLogger(__name__)


class ContentPipeline:
    """Orchestrate the 4-stage content generation pipeline.

    Stages:
    1. IntentParser: NL prompt -> ParsedIntent
    2. Outliner: ParsedIntent -> PresentationOutline
    3. SlideWriter: SlideOutline -> ExpandedSlide (per slide)
    4. CrossSlideRefiner: All slides -> RefinedPresentation

    The final output is a dict that passes Presentation.model_validate().
    """

    def __init__(self, router: LLMRouter) -> None:
        self._router = router
        self._intent_parser = IntentParser(router)
        self._outliner = Outliner(router)
        self._slide_writer = SlideWriter(router)
        self._refiner = CrossSlideRefiner(router)

    async def run(
        self,
        prompt: str,
        generation_options: GenerationOptions | None = None,
        progress_callback: Callable[..., Any] | None = None,
    ) -> dict:
        """Run the full content generation pipeline.

        Args:
            prompt: Natural language presentation request.
            generation_options: Optional generation options.
            progress_callback: Async callable(stage, progress) for reporting.

        Returns:
            Dict that passes Presentation.model_validate().
        """
        # Stage 1: Parse intent
        if progress_callback:
            await progress_callback("parsing", 0.15)

        intent = await self._intent_parser.parse(prompt, generation_options)

        # Stage 2: Generate outline
        if progress_callback:
            await progress_callback("outlining", 0.35)

        outline = await self._outliner.generate(intent)

        # Stage 3: Expand each slide
        if progress_callback:
            await progress_callback("writing", 0.40)

        expanded_slides: list[ExpandedSlide] = []
        total_slides = len(outline.slides)
        for i, slide_outline in enumerate(outline.slides):
            expanded = await self._slide_writer.expand(slide_outline, intent)
            expanded_slides.append(expanded)

            if progress_callback:
                # Progress from 0.40 to 0.85 across all slides
                slide_progress = 0.40 + (0.45 * (i + 1) / total_slides)
                await progress_callback("writing", round(slide_progress, 2))

        # Stage 4: Cross-slide refinement
        if progress_callback:
            await progress_callback("refining", 0.90)

        refined = await self._refiner.refine(expanded_slides, intent)

        # Build the final Presentation IR dict
        ir_dict = self._build_presentation_ir(outline, refined, intent)

        # Stage 5 (optional): OraClaw intelligence enrichment
        ir_dict = await self._apply_intelligence(ir_dict, intent)

        # Validate the output
        from deckforge.ir import Presentation

        Presentation.model_validate(ir_dict)

        logger.info(
            "Pipeline complete: %d slides, %d refinement changes",
            len(refined.slides),
            len(refined.changes_made),
        )

        return ir_dict

    async def _apply_intelligence(self, ir_dict: dict, intent: Any) -> dict:
        """Apply OraClaw intelligence enrichments if available.

        Enriches finance slides with Monte Carlo projections and selects
        optimal theme via contextual bandit. No-op when OraClaw is disabled.
        """
        try:
            from deckforge.intelligence.pipeline_hooks import (
                enrich_finance_slide,
                is_intelligence_enabled,
                select_intelligent_theme,
            )

            if not is_intelligence_enabled():
                return ir_dict

            # Intelligent theme selection when theme is "auto"
            current_theme = ir_dict.get("theme", "corporate-blue")
            metadata = ir_dict.get("metadata", {})
            ir_dict["theme"] = await select_intelligent_theme(current_theme, metadata)

            # Enrich finance slides with Monte Carlo data
            finance_types = {
                "dcf_summary", "returns_analysis", "sensitivity_table",
                "capital_structure", "deal_overview",
            }
            for slide in ir_dict.get("slides", []):
                if slide.get("slide_type") in finance_types:
                    slide["elements"] = await enrich_finance_slide(
                        slide["slide_type"],
                        slide.get("elements", []),
                    )

        except Exception:
            logger.warning("Intelligence enrichment failed, using defaults", exc_info=True)

        return ir_dict

    def _build_presentation_ir(
        self,
        outline: Any,
        refined: Any,
        intent: Any,
    ) -> dict:
        """Build a Presentation IR dict from pipeline outputs.

        Maps the refined ExpandedSlides into the IR slide format that
        the Presentation model expects.
        """
        slides = []
        for expanded in refined.slides:
            slide_dict: dict[str, Any] = {
                "slide_type": expanded.slide_type,
                "elements": expanded.elements,
            }
            if expanded.speaker_notes:
                slide_dict["speaker_notes"] = expanded.speaker_notes
            if expanded.layout_hint:
                slide_dict["layout_hint"] = expanded.layout_hint
            slides.append(slide_dict)

        return {
            "schema_version": "1.0",
            "metadata": {
                "title": outline.title,
                "purpose": intent.purpose.value,
                "audience": intent.audience.value,
            },
            "slides": slides,
        }
