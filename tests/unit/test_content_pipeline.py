"""Tests for the 4-stage content generation pipeline.

Tests each stage independently (IntentParser, Outliner, SlideWriter,
CrossSlideRefiner) and the full ContentPipeline end-to-end.

Uses a MockLLMRouter that returns pre-built responses -- no real API calls.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import BaseModel

from deckforge.ir.enums import Audience, Purpose, SlideType, Tone


# ---------------------------------------------------------------------------
# Mock LLMRouter that returns controlled responses per response_model
# ---------------------------------------------------------------------------


class MockLLMRouter:
    """Mock that routes complete_structured() calls based on response_model."""

    def __init__(self, responses: dict[type, BaseModel | None] | None = None):
        self._responses = responses or {}
        self.calls: list[dict] = []

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        response_model: type[BaseModel],
        **kwargs: Any,
    ) -> BaseModel:
        self.calls.append(
            {"messages": messages, "model": model, "response_model": response_model}
        )
        if response_model in self._responses:
            return self._responses[response_model]
        raise ValueError(f"No mock response configured for {response_model}")


# ===========================================================================
# Model validation tests
# ===========================================================================


class TestParsedIntentModel:
    """ParsedIntent model validates with all required fields."""

    def test_valid_parsed_intent(self):
        from deckforge.content.models import ParsedIntent

        intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Financial Review",
            key_messages=["Revenue grew 15%", "EBITDA margin expanded", "Strong pipeline"],
            target_slide_count=10,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE, SlideType.CHART_SLIDE],
        )
        assert intent.purpose == Purpose.BOARD_MEETING
        assert intent.audience == Audience.BOARD
        assert len(intent.key_messages) == 3
        assert intent.target_slide_count == 10

    def test_key_messages_min_constraint(self):
        from deckforge.content.models import ParsedIntent

        with pytest.raises(Exception):
            ParsedIntent(
                purpose=Purpose.BOARD_MEETING,
                audience=Audience.BOARD,
                topic="Q4 Review",
                key_messages=["Only one"],  # min 3
                target_slide_count=10,
                tone=Tone.FORMAL,
                suggested_slide_types=[SlideType.TITLE_SLIDE],
            )

    def test_target_slide_count_bounds(self):
        from deckforge.content.models import ParsedIntent

        with pytest.raises(Exception):
            ParsedIntent(
                purpose=Purpose.BOARD_MEETING,
                audience=Audience.BOARD,
                topic="Q4 Review",
                key_messages=["msg1", "msg2", "msg3"],
                target_slide_count=50,  # max 30
                tone=Tone.FORMAL,
                suggested_slide_types=[SlideType.TITLE_SLIDE],
            )


class TestPresentationOutlineModel:
    """PresentationOutline model validates with title, narrative_arc, sections, slides."""

    def test_valid_outline(self):
        from deckforge.content.models import PresentationOutline, SlideOutline

        outline = PresentationOutline(
            title="Q4 Board Review",
            narrative_arc="pyramid",
            sections=["Introduction", "Financial Results", "Outlook"],
            slides=[
                SlideOutline(
                    position=1,
                    slide_type=SlideType.TITLE_SLIDE,
                    headline="Q4 Exceeded All Targets",
                    key_points=["Revenue growth", "Margin expansion"],
                    narrative_role="opening",
                ),
                SlideOutline(
                    position=2,
                    slide_type=SlideType.CHART_SLIDE,
                    headline="Revenue Grew 23% YoY",
                    key_points=["Organic growth", "Acquisition contribution"],
                    narrative_role="evidence",
                ),
            ],
        )
        assert outline.narrative_arc == "pyramid"
        assert len(outline.slides) == 2


class TestSlideOutlineWordLimit:
    """SlideOutline validates headline length (<=8 words via validator)."""

    def test_headline_within_limit(self):
        from deckforge.content.models import SlideOutline

        slide = SlideOutline(
            position=1,
            slide_type=SlideType.TITLE_SLIDE,
            headline="Revenue Grew 23% YoY",
            key_points=["Point A", "Point B"],
            narrative_role="opening",
        )
        assert slide.headline == "Revenue Grew 23% YoY"

    def test_headline_exceeds_limit_raises(self):
        from deckforge.content.models import SlideOutline

        with pytest.raises(Exception):
            SlideOutline(
                position=1,
                slide_type=SlideType.TITLE_SLIDE,
                headline="This headline has way too many words to fit the constraint",
                key_points=["Point A", "Point B"],
                narrative_role="opening",
            )


# ===========================================================================
# IntentParser tests
# ===========================================================================


class TestIntentParser:
    """IntentParser.parse() calls LLMRouter.complete_structured() with ParsedIntent response_model."""

    @pytest.mark.asyncio
    async def test_parse_returns_parsed_intent(self):
        from deckforge.content.intent_parser import IntentParser
        from deckforge.content.models import ParsedIntent

        mock_intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Financial Review",
            key_messages=["Revenue grew 15%", "EBITDA margin expanded", "Strong pipeline"],
            target_slide_count=10,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE, SlideType.CHART_SLIDE],
        )
        router = MockLLMRouter(responses={ParsedIntent: mock_intent})
        parser = IntentParser(router)

        result = await parser.parse("Create a board presentation about Q4 financial results")
        assert isinstance(result, ParsedIntent)
        assert result.purpose == Purpose.BOARD_MEETING
        assert len(router.calls) == 1
        assert router.calls[0]["response_model"] is ParsedIntent

    @pytest.mark.asyncio
    async def test_parse_overrides_slide_count_from_generation_options(self):
        from deckforge.content.intent_parser import IntentParser
        from deckforge.content.models import ParsedIntent
        from deckforge.ir.metadata import GenerationOptions

        mock_intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Review",
            key_messages=["msg1", "msg2", "msg3"],
            target_slide_count=10,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE],
        )
        router = MockLLMRouter(responses={ParsedIntent: mock_intent})
        parser = IntentParser(router)

        gen_opts = GenerationOptions(target_slide_count=5)
        result = await parser.parse("Create a board deck", generation_options=gen_opts)
        assert result.target_slide_count == 5


# ===========================================================================
# Outliner tests
# ===========================================================================


class TestOutliner:
    """Outliner.generate() calls LLMRouter.complete_structured() with PresentationOutline."""

    @pytest.mark.asyncio
    async def test_generate_returns_outline(self):
        from deckforge.content.models import ParsedIntent, PresentationOutline, SlideOutline
        from deckforge.content.outliner import Outliner

        mock_outline = PresentationOutline(
            title="Q4 Board Review",
            narrative_arc="pyramid",
            sections=["Intro", "Results", "Outlook"],
            slides=[
                SlideOutline(
                    position=i,
                    slide_type=SlideType.BULLET_POINTS,
                    headline=f"Slide {i} Headline",
                    key_points=["Point A", "Point B"],
                    narrative_role="evidence",
                )
                for i in range(1, 11)
            ],
        )
        router = MockLLMRouter(responses={PresentationOutline: mock_outline})
        outliner = Outliner(router)

        intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Financial Review",
            key_messages=["Revenue grew 15%", "EBITDA expanded", "Strong pipeline"],
            target_slide_count=10,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE],
        )
        result = await outliner.generate(intent)
        assert isinstance(result, PresentationOutline)
        assert len(result.slides) == 10
        assert router.calls[0]["response_model"] is PresentationOutline


# ===========================================================================
# SlideWriter tests
# ===========================================================================


class TestSlideWriter:
    """SlideWriter.expand() returns a dict matching IR slide structure."""

    @pytest.mark.asyncio
    async def test_expand_returns_expanded_slide(self):
        from deckforge.content.models import ExpandedSlide, ParsedIntent, SlideOutline
        from deckforge.content.slide_writer import SlideWriter

        mock_expanded = ExpandedSlide(
            slide_type="bullet_points",
            title="Revenue Up 23%",
            elements=[
                {"type": "heading", "content": {"text": "Revenue Up 23%", "level": "h1"}},
                {
                    "type": "bullet_list",
                    "content": {"items": ["Organic growth drove gains", "Acquisition added 5%"], "style": "disc"},
                },
            ],
            speaker_notes="Emphasize organic growth first.",
            layout_hint="full",
        )
        router = MockLLMRouter(responses={ExpandedSlide: mock_expanded})
        writer = SlideWriter(router)

        slide_outline = SlideOutline(
            position=1,
            slide_type=SlideType.BULLET_POINTS,
            headline="Revenue Up 23%",
            key_points=["Organic growth", "Acquisition contribution"],
            narrative_role="evidence",
        )
        intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Review",
            key_messages=["msg1", "msg2", "msg3"],
            target_slide_count=10,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE],
        )

        result = await writer.expand(slide_outline, intent)
        assert isinstance(result, ExpandedSlide)
        assert result.title == "Revenue Up 23%"
        assert len(result.elements) == 2
        assert result.speaker_notes is not None
        assert result.layout_hint is not None


# ===========================================================================
# CrossSlideRefiner tests
# ===========================================================================


class TestCrossSlideRefiner:
    """CrossSlideRefiner.refine() returns refined slides list (same length, potentially modified)."""

    @pytest.mark.asyncio
    async def test_refine_returns_refined_presentation(self):
        from deckforge.content.models import (
            ExpandedSlide,
            ParsedIntent,
            RefinedPresentation,
        )
        from deckforge.content.refiner import CrossSlideRefiner

        slides = [
            ExpandedSlide(
                slide_type="bullet_points",
                title="Revenue Up 23%",
                elements=[
                    {"type": "heading", "content": {"text": "Revenue Up 23%", "level": "h1"}},
                ],
                speaker_notes="Focus on growth.",
                layout_hint="full",
            ),
            ExpandedSlide(
                slide_type="chart_slide",
                title="EBITDA Margin Expanded",
                elements=[
                    {"type": "heading", "content": {"text": "EBITDA Margin Expanded", "level": "h1"}},
                ],
                speaker_notes="Margin story.",
                layout_hint="full",
            ),
        ]
        mock_refined = RefinedPresentation(
            slides=slides,
            changes_made=["Unified terminology: 'revenue' -> 'net revenue'"],
        )
        router = MockLLMRouter(responses={RefinedPresentation: mock_refined})
        refiner = CrossSlideRefiner(router)

        intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Review",
            key_messages=["msg1", "msg2", "msg3"],
            target_slide_count=10,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE],
        )

        result = await refiner.refine(slides, intent)
        assert isinstance(result, RefinedPresentation)
        assert len(result.slides) == 2
        assert len(result.changes_made) >= 1


# ===========================================================================
# ContentPipeline end-to-end tests
# ===========================================================================


class TestContentPipeline:
    """ContentPipeline.run() orchestrates all 4 stages and returns Presentation IR dict."""

    def _make_mock_router(self):
        """Build a MockLLMRouter with responses for all 4 stages."""
        from deckforge.content.models import (
            ExpandedSlide,
            ParsedIntent,
            PresentationOutline,
            RefinedPresentation,
            SlideOutline,
        )

        mock_intent = ParsedIntent(
            purpose=Purpose.BOARD_MEETING,
            audience=Audience.BOARD,
            topic="Q4 Financial Review",
            key_messages=["Revenue grew 15%", "EBITDA margin expanded", "Strong pipeline"],
            target_slide_count=3,
            tone=Tone.FORMAL,
            suggested_slide_types=[SlideType.TITLE_SLIDE, SlideType.BULLET_POINTS, SlideType.THANK_YOU],
        )

        mock_outline = PresentationOutline(
            title="Q4 Board Review",
            narrative_arc="pyramid",
            sections=["Introduction", "Results", "Close"],
            slides=[
                SlideOutline(
                    position=1,
                    slide_type=SlideType.TITLE_SLIDE,
                    headline="Q4 Exceeded Targets",
                    key_points=["Strong quarter", "All KPIs met"],
                    narrative_role="opening",
                ),
                SlideOutline(
                    position=2,
                    slide_type=SlideType.BULLET_POINTS,
                    headline="Revenue Grew 15%",
                    key_points=["Organic growth strong", "New markets opened"],
                    narrative_role="evidence",
                ),
                SlideOutline(
                    position=3,
                    slide_type=SlideType.THANK_YOU,
                    headline="Questions and Discussion",
                    key_points=["Q&A session", "Contact info"],
                    narrative_role="conclusion",
                ),
            ],
        )

        title_expanded = ExpandedSlide(
            slide_type="title_slide",
            title="Q4 Exceeded Targets",
            elements=[
                {"type": "heading", "content": {"text": "Q4 Exceeded Targets", "level": "h1"}},
                {"type": "subheading", "content": {"text": "Board Meeting Presentation"}},
            ],
            speaker_notes="Welcome everyone to the Q4 review.",
            layout_hint="centered",
        )
        bullet_expanded = ExpandedSlide(
            slide_type="bullet_points",
            title="Revenue Grew 15%",
            elements=[
                {"type": "heading", "content": {"text": "Revenue Grew 15%", "level": "h1"}},
                {
                    "type": "bullet_list",
                    "content": {
                        "items": ["Organic growth strong", "New markets opened"],
                        "style": "disc",
                    },
                },
            ],
            speaker_notes="Focus on organic growth first.",
            layout_hint="full",
        )
        thankyou_expanded = ExpandedSlide(
            slide_type="thank_you",
            title="Questions and Discussion",
            elements=[
                {"type": "heading", "content": {"text": "Questions and Discussion", "level": "h1"}},
            ],
            speaker_notes="Open the floor for questions.",
            layout_hint="centered",
        )

        # The writer is called per-slide, so we need to return different results
        # We'll handle this by making the mock return based on call order
        expanded_slides = [title_expanded, bullet_expanded, thankyou_expanded]

        mock_refined = RefinedPresentation(
            slides=expanded_slides,
            changes_made=["Consistent capitalization applied"],
        )

        return mock_intent, mock_outline, expanded_slides, mock_refined

    @pytest.mark.asyncio
    async def test_pipeline_run_returns_presentation_dict(self):
        from deckforge.content.models import (
            ExpandedSlide,
            ParsedIntent,
            PresentationOutline,
            RefinedPresentation,
        )
        from deckforge.content.pipeline import ContentPipeline

        mock_intent, mock_outline, expanded_slides, mock_refined = self._make_mock_router()

        # Build a router that handles calls sequentially
        call_idx = {"expand": 0}

        class SequentialMockRouter:
            def __init__(self):
                self.calls = []

            async def complete_structured(self, messages, model=None, *, response_model, **kwargs):
                self.calls.append(response_model)
                if response_model is ParsedIntent:
                    return mock_intent
                elif response_model is PresentationOutline:
                    return mock_outline
                elif response_model is ExpandedSlide:
                    idx = call_idx["expand"]
                    call_idx["expand"] += 1
                    return expanded_slides[idx]
                elif response_model is RefinedPresentation:
                    return mock_refined
                raise ValueError(f"Unexpected model: {response_model}")

        router = SequentialMockRouter()
        pipeline = ContentPipeline(router)

        result = await pipeline.run("Create a board presentation about Q4 financial results")

        # Should be a dict that passes Presentation.model_validate
        assert isinstance(result, dict)
        assert result["schema_version"] == "1.0"
        assert "metadata" in result
        assert "slides" in result
        assert len(result["slides"]) == 3

    @pytest.mark.asyncio
    async def test_pipeline_invokes_progress_callback(self):
        from deckforge.content.models import (
            ExpandedSlide,
            ParsedIntent,
            PresentationOutline,
            RefinedPresentation,
        )
        from deckforge.content.pipeline import ContentPipeline

        mock_intent, mock_outline, expanded_slides, mock_refined = self._make_mock_router()

        call_idx = {"expand": 0}

        class SequentialMockRouter:
            async def complete_structured(self, messages, model=None, *, response_model, **kwargs):
                if response_model is ParsedIntent:
                    return mock_intent
                elif response_model is PresentationOutline:
                    return mock_outline
                elif response_model is ExpandedSlide:
                    idx = call_idx["expand"]
                    call_idx["expand"] += 1
                    return expanded_slides[idx]
                elif response_model is RefinedPresentation:
                    return mock_refined
                raise ValueError(f"Unexpected: {response_model}")

        router = SequentialMockRouter()
        pipeline = ContentPipeline(router)

        progress_events = []

        async def track_progress(stage: str, progress: float):
            progress_events.append((stage, progress))

        await pipeline.run(
            "Create a board deck",
            progress_callback=track_progress,
        )

        # Should have progress events for each stage
        stages = [e[0] for e in progress_events]
        assert "parsing" in stages
        assert "outlining" in stages
        assert "writing" in stages
        assert "refining" in stages

    @pytest.mark.asyncio
    async def test_pipeline_output_passes_presentation_validate(self):
        """Pipeline output is valid Presentation IR that passes Presentation.model_validate()."""
        from deckforge.content.models import (
            ExpandedSlide,
            ParsedIntent,
            PresentationOutline,
            RefinedPresentation,
        )
        from deckforge.content.pipeline import ContentPipeline
        from deckforge.ir import Presentation

        mock_intent, mock_outline, expanded_slides, mock_refined = self._make_mock_router()

        call_idx = {"expand": 0}

        class SequentialMockRouter:
            async def complete_structured(self, messages, model=None, *, response_model, **kwargs):
                if response_model is ParsedIntent:
                    return mock_intent
                elif response_model is PresentationOutline:
                    return mock_outline
                elif response_model is ExpandedSlide:
                    idx = call_idx["expand"]
                    call_idx["expand"] += 1
                    return expanded_slides[idx]
                elif response_model is RefinedPresentation:
                    return mock_refined
                raise ValueError(f"Unexpected: {response_model}")

        router = SequentialMockRouter()
        pipeline = ContentPipeline(router)

        result = await pipeline.run("Create a board deck")

        # This must not raise
        presentation = Presentation.model_validate(result)
        assert len(presentation.slides) == 3
        assert presentation.metadata.title == "Q4 Board Review"


# ===========================================================================
# Prompt template smoke tests
# ===========================================================================


class TestPromptTemplates:
    """Prompt templates are non-empty strings."""

    def test_intent_prompts_exist(self):
        from deckforge.content.prompts.intent import INTENT_SYSTEM_PROMPT, INTENT_USER_TEMPLATE

        assert len(INTENT_SYSTEM_PROMPT) > 50
        assert "{prompt}" in INTENT_USER_TEMPLATE

    def test_outline_prompts_exist(self):
        from deckforge.content.prompts.outline import OUTLINE_SYSTEM_PROMPT, OUTLINE_USER_TEMPLATE

        assert len(OUTLINE_SYSTEM_PROMPT) > 50
        assert "{" in OUTLINE_USER_TEMPLATE

    def test_expand_prompts_exist(self):
        from deckforge.content.prompts.expand import EXPAND_SYSTEM_PROMPT, EXPAND_USER_TEMPLATE

        assert len(EXPAND_SYSTEM_PROMPT) > 50
        assert "{" in EXPAND_USER_TEMPLATE

    def test_refine_prompts_exist(self):
        from deckforge.content.prompts.refine import REFINE_SYSTEM_PROMPT, REFINE_USER_TEMPLATE

        assert len(REFINE_SYSTEM_PROMPT) > 50
        assert "{" in REFINE_USER_TEMPLATE
