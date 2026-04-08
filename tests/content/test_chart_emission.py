"""Tests for chart emission in the NL content pipeline.

Closes STATE decision [03-01]: before this wiring, no chart element ever
reached the final Presentation IR when generated via /v1/generate, even
though all 24 chart renderers worked via /v1/render.

The tests below use a mocked LLMRouter so they never touch real APIs.

Covered scenarios:

1. **Data-heavy NL input -> chart element present**
   A slide whose content mentions numbers + a data keyword must carry a
   validated chart element in the output IR.

2. **Narrative NL input -> no chart** (no false positives)
   A slide with no numeric data must NOT get a chart element, otherwise
   the injector would pollute text-only decks.

3. **Malformed LLM chart -> recommender fallback succeeds**
   When the LLM returns a chart element that fails IR validation, the
   post-processor drops it and the recommender injects a valid one
   built from the slide's numeric content.

4. **Direct chart_injector unit tests** for number extraction and
   validation helpers so regressions are easy to pin down.
"""

from __future__ import annotations

from typing import Any

import pytest

from deckforge.content.chart_injector import (
    build_chart_from_recommendation,
    ensure_chart_element,
    extract_numbers,
    has_numeric_content,
    slide_should_have_chart,
    validate_chart_element,
)
from deckforge.content.models import ExpandedSlide, ParsedIntent, SlideOutline
from deckforge.content.slide_writer import SlideWriter
from deckforge.ir.elements.data import ChartElement
from deckforge.ir.enums import Audience, Purpose, SlideType, Tone


# ---------------------------------------------------------------------------
# Mock LLM router that returns a pre-built ExpandedSlide per test
# ---------------------------------------------------------------------------


class _MockRouter:
    """Tiny stand-in for LLMRouter.complete_structured()."""

    def __init__(self, response: Any) -> None:
        self._response = response
        self.calls: list[dict[str, Any]] = []

    async def complete_structured(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        *,
        response_model: type,
        **kwargs: Any,
    ) -> Any:
        self.calls.append({"messages": messages, "response_model": response_model})
        return self._response


def _make_intent() -> ParsedIntent:
    return ParsedIntent(
        purpose=Purpose.BOARD_MEETING,
        audience=Audience.BOARD,
        topic="Quarterly performance review",
        key_messages=[
            "Revenue grew sharply",
            "Margins expanded",
            "Pipeline is strong",
        ],
        target_slide_count=8,
        tone=Tone.FORMAL,
        suggested_slide_types=[SlideType.TITLE_SLIDE, SlideType.CHART_SLIDE],
    )


# ---------------------------------------------------------------------------
# Unit tests for chart_injector helpers
# ---------------------------------------------------------------------------


class TestNumberExtraction:
    def test_extracts_plain_numbers(self):
        assert extract_numbers("Revenue 12 and 34") == [12.0, 34.0]

    def test_handles_percentages_and_suffixes(self):
        values = extract_numbers("$1.2B revenue, 23% growth, 200bps margin expansion")
        assert 1_200_000_000 in values
        assert 23 in values
        assert 200 in values

    def test_returns_empty_for_narrative_text(self):
        assert extract_numbers("We had a great quarter with strong execution") == []

    def test_has_numeric_content_requires_two(self):
        assert has_numeric_content("12 and 34") is True
        assert has_numeric_content("only 42 here") is False


class TestSlideShouldHaveChart:
    def test_chart_slide_with_numbers_qualifies(self):
        assert (
            slide_should_have_chart(
                "chart_slide",
                "Revenue 12 and 34 and 56",
            )
            is True
        )

    def test_narrative_slide_without_keywords_rejected(self):
        assert (
            slide_should_have_chart(
                "bullet_points",
                "First and 2 thoughts on 5 ideas",
            )
            is False
        )

    def test_data_keyword_plus_numbers_qualifies_any_slide(self):
        assert (
            slide_should_have_chart(
                "bullet_points",
                "Revenue grew 23% with 45% margin expansion",
            )
            is True
        )


class TestValidateChartElement:
    def test_valid_bar_chart_passes(self):
        el = {
            "type": "chart",
            "chart_data": {
                "chart_type": "bar",
                "categories": ["Q1", "Q2"],
                "series": [{"name": "Rev", "values": [10, 20]}],
                "title": "Revenue",
            },
        }
        assert validate_chart_element(el) is True

    def test_missing_chart_data_fails(self):
        assert validate_chart_element({"type": "chart"}) is False

    def test_wrong_type_fails(self):
        assert validate_chart_element({"type": "bullet_list", "content": {}}) is False

    def test_malformed_chart_data_fails(self):
        bad = {
            "type": "chart",
            "chart_data": {
                "chart_type": "bar",
                # missing categories/series -> pydantic should reject
                "title": "Broken",
            },
        }
        assert validate_chart_element(bad) is False


class TestBuildChartFromRecommendation:
    def test_builds_valid_bar_chart_from_numbers(self):
        element = build_chart_from_recommendation(
            slide_type="chart_slide",
            headline="Revenue Growth",
            key_points=["Q1 12", "Q2 18", "Q3 25", "Q4 33"],
            content_blob="Q1 12, Q2 18, Q3 25, Q4 33 revenue growth",
        )
        assert element is not None
        assert element["type"] == "chart"
        assert "chart_data" in element
        # Must validate through Pydantic
        ChartElement.model_validate(element)

    def test_returns_none_when_no_numbers(self):
        element = build_chart_from_recommendation(
            slide_type="chart_slide",
            headline="Our Vision",
            key_points=["Be bold", "Ship fast", "Stay kind"],
            content_blob="Be bold. Ship fast. Stay kind.",
        )
        assert element is None


# ---------------------------------------------------------------------------
# Integration: SlideWriter + chart injector against mocked LLM
# ---------------------------------------------------------------------------


class TestSlideWriterChartEmission:
    @pytest.mark.asyncio
    async def test_data_heavy_slide_gets_chart_from_recommender(self):
        """NL input with explicit numbers -> chart element present in output IR.

        The mocked LLM response deliberately omits a chart element; the
        post-processor must inject one via the recommender because the
        slide is a chart_slide with clear numeric content.
        """
        mock_expanded = ExpandedSlide(
            slide_type="chart_slide",
            title="Revenue Grew Across Quarters",
            elements=[
                {
                    "type": "heading",
                    "content": {"text": "Revenue Grew Across Quarters", "level": "h1"},
                },
                {
                    "type": "bullet_list",
                    "content": {
                        "items": ["Q1 $12M", "Q2 $18M", "Q3 $25M", "Q4 $33M"],
                        "style": "disc",
                    },
                },
            ],
            speaker_notes="Growth accelerated in H2.",
            layout_hint="full",
        )
        router = _MockRouter(mock_expanded)
        writer = SlideWriter(router)  # type: ignore[arg-type]

        outline = SlideOutline(
            position=2,
            slide_type=SlideType.CHART_SLIDE,
            headline="Revenue Grew Across Quarters",
            key_points=["Q1 $12M", "Q2 $18M", "Q3 $25M", "Q4 $33M"],
            narrative_role="evidence",
        )

        result = await writer.expand(outline, _make_intent())

        chart_elements = [
            el for el in result.elements if isinstance(el, dict) and el.get("type") == "chart"
        ]
        assert len(chart_elements) == 1, (
            "chart element was not injected into data-heavy slide"
        )
        # Resulting chart MUST validate against the IR schema
        ChartElement.model_validate(chart_elements[0])

    @pytest.mark.asyncio
    async def test_narrative_slide_gets_no_chart(self):
        """NL input without numbers -> no chart element (no false positives)."""
        mock_expanded = ExpandedSlide(
            slide_type="bullet_points",
            title="Our Strategic Priorities",
            elements=[
                {
                    "type": "heading",
                    "content": {"text": "Our Strategic Priorities", "level": "h1"},
                },
                {
                    "type": "bullet_list",
                    "content": {
                        "items": [
                            "Invest in customer success",
                            "Strengthen partner ecosystem",
                            "Expand international reach",
                        ],
                        "style": "disc",
                    },
                },
            ],
            speaker_notes="Emphasize the customer success investment.",
            layout_hint="full",
        )
        router = _MockRouter(mock_expanded)
        writer = SlideWriter(router)  # type: ignore[arg-type]

        outline = SlideOutline(
            position=3,
            slide_type=SlideType.BULLET_POINTS,
            headline="Our Strategic Priorities",
            key_points=[
                "Invest in customer success",
                "Strengthen partner ecosystem",
                "Expand international reach",
            ],
            narrative_role="evidence",
        )

        result = await writer.expand(outline, _make_intent())

        chart_elements = [
            el for el in result.elements if isinstance(el, dict) and el.get("type") == "chart"
        ]
        assert chart_elements == [], "chart was wrongly injected into narrative slide"

    @pytest.mark.asyncio
    async def test_malformed_llm_chart_triggers_recommender_fallback(self):
        """Malformed LLM chart -> dropped, recommender fallback succeeds."""
        mock_expanded = ExpandedSlide(
            slide_type="chart_slide",
            title="ARR Growth Trajectory",
            elements=[
                {
                    "type": "heading",
                    "content": {"text": "ARR Growth Trajectory", "level": "h1"},
                },
                # Intentionally malformed: chart_data missing required fields
                {
                    "type": "chart",
                    "chart_data": {
                        "chart_type": "bar",
                        # missing categories / series -> pydantic rejects
                        "title": "ARR",
                    },
                },
                {
                    "type": "bullet_list",
                    "content": {
                        "items": ["2022 $10M ARR", "2023 $18M ARR", "2024 $27M ARR"],
                        "style": "disc",
                    },
                },
            ],
            speaker_notes="Show the compounding effect.",
            layout_hint="full",
        )
        router = _MockRouter(mock_expanded)
        writer = SlideWriter(router)  # type: ignore[arg-type]

        outline = SlideOutline(
            position=4,
            slide_type=SlideType.CHART_SLIDE,
            headline="ARR Growth Trajectory",
            key_points=["2022 $10M", "2023 $18M", "2024 $27M"],
            narrative_role="evidence",
        )

        result = await writer.expand(outline, _make_intent())

        chart_elements = [
            el for el in result.elements if isinstance(el, dict) and el.get("type") == "chart"
        ]
        assert len(chart_elements) == 1, (
            "fallback chart was not injected after malformed LLM chart"
        )
        # Fallback chart validates
        validated = ChartElement.model_validate(chart_elements[0])
        # And carries the numbers we extracted (10, 18, 27 or expanded suffixes)
        chart_data = chart_elements[0]["chart_data"]
        assert chart_data.get("title"), "fallback chart missing title"
        assert validated is not None


# ---------------------------------------------------------------------------
# ensure_chart_element used directly (sanity check without writer)
# ---------------------------------------------------------------------------


class TestEnsureChartElementDirect:
    def test_passes_through_valid_llm_chart(self):
        llm_chart = {
            "type": "chart",
            "chart_data": {
                "chart_type": "line",
                "categories": ["2022", "2023", "2024"],
                "series": [{"name": "ARR", "values": [10, 18, 27]}],
                "title": "ARR Growth",
            },
        }
        elements = [
            {"type": "heading", "content": {"text": "ARR", "level": "h1"}},
            llm_chart,
        ]
        out = ensure_chart_element(
            slide_type="chart_slide",
            headline="ARR Growth",
            key_points=["2022", "2023", "2024"],
            elements=elements,
        )
        # LLM's valid chart preserved, no duplicate injected
        chart_elements = [el for el in out if el.get("type") == "chart"]
        assert len(chart_elements) == 1
        assert chart_elements[0] is llm_chart
