"""Tests for IR metadata, generation_options, and brand_kit models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestPresentationMetadata:
    def test_minimal_metadata(self):
        from deckforge.ir.metadata import PresentationMetadata

        m = PresentationMetadata(title="Test")
        assert m.title == "Test"
        assert m.language == "en"
        assert m.confidentiality.value == "internal"

    def test_full_metadata(self):
        from deckforge.ir.metadata import PresentationMetadata

        m = PresentationMetadata(
            title="Board Deck",
            subtitle="Q4 Review",
            author="CEO",
            company="Acme Corp",
            date="2025-12-15",
            language="en",
            purpose="board_meeting",
            audience="board",
            confidentiality="confidential",
        )
        assert m.purpose.value == "board_meeting"
        assert m.audience.value == "board"
        assert m.confidentiality.value == "confidential"

    def test_metadata_missing_title_raises(self):
        from deckforge.ir.metadata import PresentationMetadata

        with pytest.raises(ValidationError):
            PresentationMetadata()

    def test_all_purpose_values(self):
        from deckforge.ir.metadata import PresentationMetadata

        purposes = [
            "board_meeting", "investor_update", "sales_pitch", "training",
            "project_update", "strategy", "research", "deal_memo",
            "ic_presentation", "quarterly_review", "all_hands", "keynote",
        ]
        for p in purposes:
            m = PresentationMetadata(title="Test", purpose=p)
            assert m.purpose.value == p

    def test_all_audience_values(self):
        from deckforge.ir.metadata import PresentationMetadata

        audiences = ["c_suite", "board", "investors", "team", "clients", "public"]
        for a in audiences:
            m = PresentationMetadata(title="Test", audience=a)
            assert m.audience.value == a


class TestGenerationOptions:
    def test_defaults(self):
        from deckforge.ir.metadata import GenerationOptions

        g = GenerationOptions()
        assert g.density.value == "balanced"
        assert g.chart_style.value == "minimal"
        assert g.emphasis.value == "visual"
        assert g.quality_target.value == "presentation_ready"
        assert g.target_slide_count is None

    def test_with_integer_slide_count(self):
        from deckforge.ir.metadata import GenerationOptions

        g = GenerationOptions(target_slide_count=15)
        assert g.target_slide_count == 15

    def test_with_range_slide_count(self):
        from deckforge.ir.metadata import GenerationOptions

        g = GenerationOptions(target_slide_count=[10, 20])
        assert g.target_slide_count == [10, 20]

    def test_all_density_values(self):
        from deckforge.ir.metadata import GenerationOptions

        for d in ["sparse", "balanced", "dense"]:
            g = GenerationOptions(density=d)
            assert g.density.value == d

    def test_all_chart_style_values(self):
        from deckforge.ir.metadata import GenerationOptions

        for cs in ["minimal", "detailed", "annotated"]:
            g = GenerationOptions(chart_style=cs)
            assert g.chart_style.value == cs

    def test_all_quality_target_values(self):
        from deckforge.ir.metadata import GenerationOptions

        for qt in ["draft", "presentation_ready", "board_ready"]:
            g = GenerationOptions(quality_target=qt)
            assert g.quality_target.value == qt


class TestBrandKit:
    def test_empty_brand_kit(self):
        from deckforge.ir.brand_kit import BrandKit

        bk = BrandKit()
        assert bk.colors is None
        assert bk.fonts is None
        assert bk.logo is None
        assert bk.footer is None
        assert bk.tone is None

    def test_brand_colors(self):
        from deckforge.ir.brand_kit import BrandColors

        c = BrandColors(primary="#003366", secondary="#666")
        assert c.primary == "#003366"
        assert c.accent == []

    def test_brand_colors_missing_primary_raises(self):
        from deckforge.ir.brand_kit import BrandColors

        with pytest.raises(ValidationError):
            BrandColors()

    def test_brand_fonts(self):
        from deckforge.ir.brand_kit import BrandFonts

        f = BrandFonts(heading="Inter", body="Open Sans")
        assert f.heading == "Inter"
        assert f.mono is None

    def test_logo_config(self):
        from deckforge.ir.brand_kit import LogoConfig

        logo = LogoConfig(url="https://example.com/logo.png")
        assert logo.placement == "top_left"
        assert logo.max_width is None

    def test_footer_config(self):
        from deckforge.ir.brand_kit import FooterConfig

        footer = FooterConfig(text="Confidential")
        assert footer.include_page_numbers is True
        assert footer.include_date is False
        assert footer.include_logo is False

    def test_full_brand_kit(self):
        from deckforge.ir.brand_kit import BrandKit

        bk = BrandKit(
            colors={"primary": "#000"},
            fonts={"heading": "Inter"},
            logo={"url": "https://example.com/logo.svg", "placement": "top_right"},
            footer={"text": "Private", "include_page_numbers": True},
            tone="professional",
        )
        assert bk.tone.value == "professional"
        assert bk.colors.primary == "#000"

    def test_all_tone_values(self):
        from deckforge.ir.brand_kit import BrandKit

        for tone in ["formal", "professional", "conversational", "bold"]:
            bk = BrandKit(tone=tone)
            assert bk.tone.value == tone
