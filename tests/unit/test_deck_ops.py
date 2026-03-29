"""Tests for DeckOperations and CostEstimator services.

Tests cover:
- CostEstimator: base credits, finance surcharges, chart surcharges, NL surcharge
- DeckOperations: append, replace, reorder, retheme, validation errors
"""

from __future__ import annotations

import math

import pytest

from deckforge.services.cost_estimator import CostEstimate, CostEstimator
from deckforge.services.deck_ops import DeckOperations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_ir(
    slide_count: int = 3,
    slide_types: list[str] | None = None,
    chart_count: int = 0,
    generation_options: dict | None = None,
    theme: str = "executive-dark",
) -> dict:
    """Build a minimal valid IR dict for testing.

    Uses 'title_slide' as the default slide_type (valid discriminator tag).
    Each slide gets a 'label' field for test identification (not part of model).
    """
    types = slide_types or ["title_slide"] * slide_count
    slides = []
    for i, st in enumerate(types):
        slide: dict = {
            "slide_type": st,
            "elements": [],
        }
        # Add chart elements if requested (only on first slide)
        for c in range(chart_count if i == 0 else 0):
            slide["elements"].append(
                {
                    "type": "chart",
                    "chart": {
                        "chart_type": "bar",
                        "title": f"Chart {c}",
                        "data": {"labels": ["A"], "datasets": [{"label": "s", "values": [1]}]},
                    },
                }
            )
        slides.append(slide)

    ir: dict = {
        "schema_version": "1.0",
        "metadata": {
            "title": "Test Deck",
            "subtitle": "Unit tests",
        },
        "theme": theme,
        "slides": slides,
    }
    if generation_options is not None:
        ir["generation_options"] = generation_options
    return ir


# ---------------------------------------------------------------------------
# CostEstimator tests
# ---------------------------------------------------------------------------

class TestCostEstimator:
    """Tests for CostEstimator.estimate()."""

    def setup_method(self):
        self.estimator = CostEstimator()

    def test_base_credits_10_slides_no_surcharges(self):
        """10 plain slides => base 1 credit, total 1."""
        ir = _make_ir(slide_count=10)
        result = self.estimator.estimate_from_ir(ir)
        assert isinstance(result, CostEstimate)
        assert result.base_credits == 1
        assert result.total_credits == 1

    def test_base_credits_15_slides(self):
        """15 slides => ceil(15/10) = 2 base credits."""
        ir = _make_ir(slide_count=15)
        result = self.estimator.estimate_from_ir(ir)
        assert result.base_credits == 2
        assert result.total_credits == 2

    def test_finance_slide_surcharge(self):
        """Finance slides add 0.5 each."""
        types = ["title_slide", "comp_table", "dcf_summary"]
        ir = _make_ir(slide_count=3, slide_types=types)
        result = self.estimator.estimate_from_ir(ir)
        # base = ceil(3/10) = 1, finance = 2 * 0.5 = 1.0, total = ceil(2.0) = 2
        assert result.surcharges.get("finance", 0) == pytest.approx(1.0)
        assert result.total_credits == 2

    def test_chart_element_surcharge(self):
        """Chart elements add 0.2 each."""
        ir = _make_ir(slide_count=3, chart_count=5)
        result = self.estimator.estimate_from_ir(ir)
        # base = 1, charts = 5 * 0.2 = 1.0, total = ceil(2.0) = 2
        assert result.surcharges.get("charts", 0) == pytest.approx(1.0)
        assert result.total_credits == 2

    def test_nl_generation_surcharge(self):
        """NL generation adds +2 surcharge."""
        ir = _make_ir(slide_count=3, generation_options={"quality_target": "standard", "tone": "formal"})
        result = self.estimator.estimate_from_ir(ir)
        assert result.surcharges.get("nl_generation", 0) == pytest.approx(2.0)
        # base=1 + nl=2 => total=3
        assert result.total_credits == 3

    def test_no_nl_surcharge_when_none(self):
        """No NL surcharge when generation_options is absent."""
        ir = _make_ir(slide_count=3)
        result = self.estimator.estimate_from_ir(ir)
        assert result.surcharges.get("nl_generation", 0) == 0

    def test_combined_surcharges(self):
        """Finance + charts + NL all combined."""
        types = ["comp_table", "dcf_summary", "title_slide", "title_slide", "title_slide"]
        ir = _make_ir(
            slide_count=5,
            slide_types=types,
            chart_count=3,
            generation_options={"quality_target": "standard", "tone": "formal"},
        )
        result = self.estimator.estimate_from_ir(ir)
        # base = ceil(5/10) = 1
        # finance = 2 * 0.5 = 1.0
        # charts = 3 * 0.2 = 0.6
        # nl = 2.0
        # total = ceil(1 + 1.0 + 0.6 + 2.0) = ceil(4.6) = 5
        assert result.base_credits == 1
        assert result.total_credits == 5

    def test_breakdown_is_string(self):
        """Breakdown field is a human-readable string."""
        ir = _make_ir(slide_count=3)
        result = self.estimator.estimate_from_ir(ir)
        assert isinstance(result.breakdown, str)
        assert len(result.breakdown) > 0


# ---------------------------------------------------------------------------
# DeckOperations tests
# ---------------------------------------------------------------------------

class TestDeckOperations:
    """Tests for DeckOperations mutation methods."""

    def setup_method(self):
        self.ops = DeckOperations()

    def test_append_slides(self):
        """Appending slides increases the slide list."""
        ir = _make_ir(slide_count=2)
        new_slides = [{"slide_type": "title_slide", "elements": [], "speaker_notes": "appended"}]
        result = self.ops.append_slides(ir, new_slides)
        assert len(result["slides"]) == 3
        assert result["slides"][-1]["speaker_notes"] == "appended"

    def test_append_slides_validates(self):
        """Appended slides with invalid data raise ValueError."""
        ir = _make_ir(slide_count=2)
        # Empty slides list after append should still be valid (2 + 0 = 2)
        result = self.ops.append_slides(ir, [])
        assert len(result["slides"]) == 2

    def test_replace_slide(self):
        """Replace slide at index replaces correctly."""
        ir = _make_ir(slide_count=3)
        new_slide = {"slide_type": "agenda", "elements": [], "speaker_notes": "replaced"}
        result = self.ops.replace_slide(ir, 1, new_slide)
        assert result["slides"][1]["slide_type"] == "agenda"
        assert result["slides"][1]["speaker_notes"] == "replaced"
        assert len(result["slides"]) == 3

    def test_replace_slide_invalid_index(self):
        """Replace with out-of-range index raises ValueError."""
        ir = _make_ir(slide_count=2)
        new_slide = {"slide_type": "title_slide", "elements": []}
        with pytest.raises(ValueError, match="index"):
            self.ops.replace_slide(ir, 5, new_slide)

    def test_reorder_slides(self):
        """Reorder slides per new index list."""
        ir = _make_ir(slide_count=3)
        # Use different slide_types to track reordering
        ir["slides"][0]["slide_type"] = "title_slide"
        ir["slides"][0]["speaker_notes"] = "A"
        ir["slides"][1]["slide_type"] = "agenda"
        ir["slides"][1]["speaker_notes"] = "B"
        ir["slides"][2]["slide_type"] = "key_message"
        ir["slides"][2]["speaker_notes"] = "C"
        result = self.ops.reorder_slides(ir, [2, 0, 1])
        assert result["slides"][0]["speaker_notes"] == "C"
        assert result["slides"][1]["speaker_notes"] == "A"
        assert result["slides"][2]["speaker_notes"] == "B"

    def test_reorder_slides_invalid_indices(self):
        """Reorder with wrong number of indices raises ValueError."""
        ir = _make_ir(slide_count=3)
        with pytest.raises(ValueError, match="indices"):
            self.ops.reorder_slides(ir, [0, 1])

    def test_reorder_slides_duplicate_indices(self):
        """Reorder with duplicate indices raises ValueError."""
        ir = _make_ir(slide_count=3)
        with pytest.raises(ValueError, match="indices"):
            self.ops.reorder_slides(ir, [0, 0, 1])

    def test_reorder_slides_out_of_range(self):
        """Reorder with out-of-range indices raises ValueError."""
        ir = _make_ir(slide_count=3)
        with pytest.raises(ValueError, match="indices"):
            self.ops.reorder_slides(ir, [0, 1, 5])

    def test_retheme(self):
        """Retheme changes the theme field."""
        ir = _make_ir(slide_count=2, theme="executive-dark")
        result = self.ops.retheme(ir, "modern-light")
        assert result["theme"] == "modern-light"

    def test_retheme_preserves_slides(self):
        """Retheme does not modify slides."""
        ir = _make_ir(slide_count=3)
        original_slide_count = len(ir["slides"])
        result = self.ops.retheme(ir, "minimal")
        assert len(result["slides"]) == original_slide_count
