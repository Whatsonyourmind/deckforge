"""Tests for Presentation model, cross-field validation, and JSON round-trip."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError


class TestPresentationModel:
    def test_minimal_presentation(self):
        from deckforge.ir.presentation import Presentation

        p = Presentation(
            metadata={"title": "Test Deck"},
            slides=[{"slide_type": "title_slide", "elements": []}],
        )
        assert p.metadata.title == "Test Deck"
        assert p.schema_version == "1.0"
        assert p.theme == "executive-dark"
        assert len(p.slides) == 1

    def test_presentation_with_theme(self):
        from deckforge.ir.presentation import Presentation

        p = Presentation(
            metadata={"title": "Styled Deck"},
            theme="consulting-classic",
            slides=[{"slide_type": "title_slide", "elements": []}],
        )
        assert p.theme == "consulting-classic"

    def test_presentation_with_generation_options(self):
        from deckforge.ir.presentation import Presentation

        p = Presentation(
            metadata={"title": "Gen Options Test"},
            slides=[{"slide_type": "title_slide", "elements": []}],
            generation_options={
                "target_slide_count": 10,
                "density": "dense",
                "chart_style": "annotated",
                "emphasis": "data",
                "quality_target": "board_ready",
            },
        )
        assert p.generation_options.density.value == "dense"
        assert p.generation_options.chart_style.value == "annotated"
        assert p.generation_options.emphasis.value == "data"
        assert p.generation_options.quality_target.value == "board_ready"

    def test_presentation_with_brand_kit(self):
        from deckforge.ir.presentation import Presentation

        p = Presentation(
            metadata={"title": "Branded Deck"},
            slides=[{"slide_type": "title_slide", "elements": []}],
            brand_kit={
                "colors": {"primary": "#003366", "secondary": "#666666"},
                "fonts": {"heading": "Inter", "body": "Open Sans"},
                "logo": {"url": "https://example.com/logo.png", "placement": "top_right"},
                "footer": {"text": "Confidential", "include_page_numbers": True},
                "tone": "formal",
            },
        )
        assert p.brand_kit.colors.primary == "#003366"
        assert p.brand_kit.fonts.heading == "Inter"
        assert p.brand_kit.logo.placement == "top_right"
        assert p.brand_kit.footer.include_page_numbers is True
        assert p.brand_kit.tone.value == "formal"

    def test_schema_version_defaults(self):
        from deckforge.ir.presentation import Presentation

        p = Presentation(
            metadata={"title": "V Test"},
            slides=[{"slide_type": "title_slide", "elements": []}],
        )
        assert p.schema_version == "1.0"

    def test_empty_slides_raises(self):
        from deckforge.ir.presentation import Presentation

        with pytest.raises(ValidationError):
            Presentation(
                metadata={"title": "Empty"},
                slides=[],
            )

    def test_missing_metadata_title_raises(self):
        from deckforge.ir.presentation import Presentation

        with pytest.raises(ValidationError):
            Presentation(
                metadata={},
                slides=[{"slide_type": "title_slide", "elements": []}],
            )

    def test_json_round_trip(self):
        from deckforge.ir.presentation import Presentation

        data = {
            "metadata": {
                "title": "Round Trip Test",
                "purpose": "board_meeting",
                "audience": "board",
                "confidentiality": "confidential",
            },
            "brand_kit": {
                "colors": {"primary": "#000000"},
                "tone": "formal",
            },
            "theme": "executive-dark",
            "slides": [
                {
                    "slide_type": "title_slide",
                    "elements": [
                        {"type": "heading", "content": {"text": "Welcome", "level": "h1"}}
                    ],
                },
                {
                    "slide_type": "chart_slide",
                    "elements": [
                        {
                            "type": "chart",
                            "chart_data": {
                                "chart_type": "bar",
                                "categories": ["Q1", "Q2"],
                                "series": [{"name": "Rev", "values": [100, 200]}],
                            },
                        }
                    ],
                },
                {
                    "slide_type": "dcf_summary",
                    "elements": [],
                    "discount_rate_range": [8.0, 12.0],
                },
            ],
            "generation_options": {
                "target_slide_count": 15,
                "density": "balanced",
                "chart_style": "minimal",
                "quality_target": "presentation_ready",
            },
        }

        # Parse from dict
        p = Presentation.model_validate(data)
        assert p.metadata.title == "Round Trip Test"
        assert len(p.slides) == 3

        # Serialize to JSON and back
        json_str = p.model_dump_json()
        p2 = Presentation.model_validate_json(json_str)
        assert p2.metadata.title == "Round Trip Test"
        assert len(p2.slides) == 3
        assert p2.slides[0].slide_type == "title_slide"
        assert p2.slides[2].slide_type == "dcf_summary"

    def test_model_json_schema_generates(self):
        from deckforge.ir.presentation import Presentation

        schema = Presentation.model_json_schema()
        assert isinstance(schema, dict)
        assert "title" in schema or "properties" in schema

    def test_full_presentation_with_all_options(self):
        """Integration test: full IR with mixed slide types and all options."""
        from deckforge.ir.presentation import Presentation

        p = Presentation(
            schema_version="1.0",
            metadata={
                "title": "Q4 Board Deck",
                "subtitle": "2025 Review",
                "author": "CFO",
                "company": "Acme Corp",
                "date": "2025-12-15",
                "language": "en",
                "purpose": "board_meeting",
                "audience": "board",
                "confidentiality": "confidential",
            },
            brand_kit={
                "colors": {
                    "primary": "#1a1a2e",
                    "secondary": "#16213e",
                    "accent": ["#0f3460", "#e94560"],
                    "background": "#ffffff",
                    "text": "#1a1a2e",
                    "muted": "#9e9e9e",
                },
                "fonts": {
                    "heading": "Inter",
                    "body": "Open Sans",
                    "mono": "JetBrains Mono",
                    "caption": "Inter",
                },
                "logo": {
                    "url": "https://example.com/logo.svg",
                    "placement": "top_left",
                    "max_width": 120.0,
                    "max_height": 40.0,
                },
                "footer": {
                    "text": "Strictly Confidential",
                    "include_page_numbers": True,
                    "include_date": True,
                    "include_logo": True,
                },
                "tone": "formal",
            },
            theme="finance-institutional",
            slides=[
                {"slide_type": "title_slide", "elements": [
                    {"type": "heading", "content": {"text": "Q4 2025 Board Deck"}},
                ]},
                {"slide_type": "agenda", "elements": [
                    {"type": "bullet_list", "content": {"items": ["Financials", "Strategy", "Q&A"]}},
                ]},
                {"slide_type": "chart_slide", "elements": [
                    {"type": "chart", "chart_data": {
                        "chart_type": "bar",
                        "categories": ["Q1", "Q2", "Q3", "Q4"],
                        "series": [{"name": "Revenue", "values": [100, 120, 135, 150]}],
                    }},
                ]},
                {"slide_type": "comp_table", "elements": [
                    {"type": "table", "content": {
                        "headers": ["Company", "EV/EBITDA", "P/E"],
                        "rows": [["Peer A", 12.5, 18.2], ["Peer B", 14.1, 20.5]],
                    }},
                ], "highlight_column": "EV/EBITDA"},
                {"slide_type": "thank_you", "elements": []},
            ],
            generation_options={
                "target_slide_count": 20,
                "density": "balanced",
                "chart_style": "detailed",
                "emphasis": "data",
                "quality_target": "board_ready",
            },
        )

        assert len(p.slides) == 5
        assert p.metadata.purpose.value == "board_meeting"
        assert p.brand_kit.colors.accent == ["#0f3460", "#e94560"]
