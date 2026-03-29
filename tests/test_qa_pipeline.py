"""Tests for QA pipeline: 5 checkers, auto-fix engine, and executive readiness scorer."""

from __future__ import annotations

import math

import pytest

from deckforge.ir.brand_kit import BrandKit, BrandColors, BrandFonts, LogoConfig
from deckforge.ir.elements.data import (
    ChartElement,
    TableContent,
    TableElement,
)
from deckforge.ir.elements.text import (
    BodyTextContent,
    BodyTextElement,
    BulletListContent,
    BulletListElement,
    HeadingContent,
    HeadingElement,
    SubheadingContent,
    SubheadingElement,
)
from deckforge.ir.enums import SlideType
from deckforge.ir.charts.types import PieChartData, BarChartData, ChartDataSeries
from deckforge.ir.metadata import PresentationMetadata
from deckforge.ir.presentation import Presentation
from deckforge.ir.slides.universal import BulletPointsSlide, ChartSlideSlide, TitleSlide
from deckforge.layout.types import LayoutResult, ResolvedPosition
from deckforge.themes.types import (
    ComponentStyle,
    ResolvedTheme,
    SlideMaster,
    ThemeColors,
    ThemeSpacing,
    ThemeTypography,
)

from deckforge.qa.types import QAIssue, QAFix, QACategory, QAReport
from deckforge.qa.checkers.structural import StructuralChecker
from deckforge.qa.checkers.text import TextQualityChecker
from deckforge.qa.checkers.visual import VisualQualityChecker
from deckforge.qa.checkers.data import DataIntegrityChecker
from deckforge.qa.checkers.brand import BrandComplianceChecker
from deckforge.qa.autofix import AutoFixEngine
from deckforge.qa.scorer import ExecutiveReadinessScorer


# ── Fixtures ─────────────────────────────────────────────────────────────────


def _make_theme(**overrides) -> ResolvedTheme:
    """Create a minimal ResolvedTheme for testing."""
    defaults = dict(
        name="test-theme",
        description="Test theme",
        colors=ThemeColors(
            primary="#003366",
            secondary="#336699",
            accent="#FF6600",
            background="#FFFFFF",
            surface="#F5F5F5",
            text_primary="#1A1A1A",
            text_secondary="#666666",
            text_muted="#999999",
            positive="#28A745",
            negative="#DC3545",
            warning="#FFC107",
        ),
        typography=ThemeTypography(
            heading_family="Arial",
            body_family="Calibri",
            mono_family="Consolas",
        ),
        spacing=ThemeSpacing(
            margin_top=0.5,
            margin_bottom=0.5,
            margin_left=0.75,
            margin_right=0.75,
            gutter=0.3,
            element_gap=0.2,
            section_gap=0.5,
        ),
        slide_masters={
            "default": SlideMaster(
                background="#FFFFFF",
                regions={
                    "title": ComponentStyle(
                        font_family="Arial",
                        font_size=36,
                        color="#1A1A1A",
                    ),
                    "content": ComponentStyle(
                        font_family="Calibri",
                        font_size=18,
                        color="#1A1A1A",
                    ),
                },
            )
        },
    )
    defaults.update(overrides)
    return ResolvedTheme(**defaults)


def _make_presentation(slides, **kwargs) -> Presentation:
    """Create a minimal Presentation for testing."""
    meta_kwargs = {"title": "Test Deck"}
    meta_kwargs.update(kwargs.pop("metadata", {}))
    return Presentation(
        metadata=PresentationMetadata(**meta_kwargs),
        slides=slides,
        **kwargs,
    )


def _make_bullet_slide(elements=None) -> BulletPointsSlide:
    """Create a BulletPointsSlide for testing."""
    return BulletPointsSlide(elements=elements or [])


def _make_chart_slide(elements=None) -> ChartSlideSlide:
    """Create a ChartSlideSlide for testing."""
    return ChartSlideSlide(elements=elements or [])


def _make_layout_result(slide, positions=None) -> LayoutResult:
    """Create a LayoutResult for testing."""
    return LayoutResult(slide=slide, positions=positions or {})


# ── Structural Checker ───────────────────────────────────────────────────────


class TestStructuralChecker:
    def test_flags_missing_title(self):
        """Slide with no heading element flagged as missing_title."""
        checker = StructuralChecker()
        slide = _make_bullet_slide(
            elements=[
                BulletListElement(content=BulletListContent(items=["Point 1", "Point 2"])),
            ],
        )
        pres = _make_presentation([slide])
        theme = _make_theme()
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "missing_title" in types

    def test_flags_empty_slide(self):
        """Slide with zero elements flagged as empty_slide."""
        checker = StructuralChecker()
        slide = _make_bullet_slide(elements=[])
        pres = _make_presentation([slide])
        theme = _make_theme()
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "empty_slide" in types

    def test_passes_slide_with_heading(self):
        """Slide with a heading element should NOT be flagged."""
        checker = StructuralChecker()
        slide = _make_bullet_slide(
            elements=[
                HeadingElement(content=HeadingContent(text="My Title")),
                BulletListElement(content=BulletListContent(items=["A"])),
            ],
        )
        pres = _make_presentation([slide])
        theme = _make_theme()
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "missing_title" not in types
        assert "empty_slide" not in types


# ── Text Quality Checker ─────────────────────────────────────────────────────


class TestTextQualityChecker:
    def test_flags_text_overflow(self):
        """Text whose measured height exceeds its allocated position height is flagged."""
        checker = TextQualityChecker()
        slide = _make_bullet_slide(
            elements=[
                HeadingElement(content=HeadingContent(text="Title")),
                BodyTextElement(
                    content=BodyTextContent(
                        text="This is a very long text " * 50
                    )
                ),
            ],
        )
        # Allocate a tiny position that will surely overflow
        positions = {
            "title": ResolvedPosition(x=0.75, y=0.5, width=8.5, height=1.0),
            "content": ResolvedPosition(x=0.75, y=1.5, width=8.5, height=0.5),
        }
        layout = LayoutResult(slide=slide, positions=positions)
        pres = _make_presentation([slide])
        theme = _make_theme()

        issues = checker.check(pres, [layout], theme)
        types = [i.type for i in issues]
        assert "text_overflow" in types


# ── Visual Quality Checker ───────────────────────────────────────────────────


class TestVisualQualityChecker:
    def test_flags_low_contrast(self):
        """Color pair below 4.5:1 contrast flagged as contrast_failure."""
        checker = VisualQualityChecker()
        # Light gray text on white background = very low contrast
        theme = _make_theme(
            slide_masters={
                "default": SlideMaster(
                    background="#FFFFFF",
                    regions={
                        "title": ComponentStyle(
                            font_family="Arial",
                            font_size=36,
                            color="#CCCCCC",  # Light gray on white = low contrast
                        ),
                        "content": ComponentStyle(
                            font_family="Calibri",
                            font_size=18,
                            color="#1A1A1A",
                        ),
                    },
                )
            },
        )
        slide = _make_bullet_slide(
            elements=[HeadingElement(content=HeadingContent(text="Title"))],
        )
        pres = _make_presentation([slide])
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "contrast_failure" in types

    def test_passes_high_contrast(self):
        """Color pair above 4.5:1 contrast should not be flagged."""
        checker = VisualQualityChecker()
        # Dark text on white = high contrast
        theme = _make_theme()  # default has #1A1A1A on #FFFFFF
        slide = _make_bullet_slide(
            elements=[HeadingElement(content=HeadingContent(text="Title"))],
        )
        pres = _make_presentation([slide])
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "contrast_failure" not in types

    def test_flags_font_below_floor(self):
        """Font size below 10pt flagged as font_below_floor."""
        checker = VisualQualityChecker()
        theme = _make_theme(
            slide_masters={
                "default": SlideMaster(
                    background="#FFFFFF",
                    regions={
                        "title": ComponentStyle(
                            font_family="Arial",
                            font_size=36,
                            color="#1A1A1A",
                        ),
                        "content": ComponentStyle(
                            font_family="Calibri",
                            font_size=8,  # Below 10pt floor
                            color="#1A1A1A",
                        ),
                    },
                )
            },
        )
        slide = _make_bullet_slide(
            elements=[
                HeadingElement(content=HeadingContent(text="Title")),
                BodyTextElement(content=BodyTextContent(text="Body")),
            ],
        )
        pres = _make_presentation([slide])
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "font_below_floor" in types


# ── Data Integrity Checker ───────────────────────────────────────────────────


class TestDataIntegrityChecker:
    def test_flags_percentage_sum_wrong(self):
        """Pie chart values that don't sum near 100 flagged."""
        checker = DataIntegrityChecker()
        slide = _make_chart_slide(
            elements=[
                HeadingElement(content=HeadingContent(text="Market Share")),
                ChartElement(
                    chart_data=PieChartData(
                        labels=["A", "B", "C"],
                        values=[30, 30, 30],  # Sums to 90, not 100
                    ),
                ),
            ],
        )
        pres = _make_presentation([slide])
        theme = _make_theme()
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "percentage_sum_wrong" in types

    def test_passes_correct_percentages(self):
        """Pie chart values summing to 100 should not be flagged."""
        checker = DataIntegrityChecker()
        slide = _make_chart_slide(
            elements=[
                HeadingElement(content=HeadingContent(text="Market Share")),
                ChartElement(
                    chart_data=PieChartData(
                        labels=["A", "B", "C"],
                        values=[33, 33, 34],  # Sums to 100
                    ),
                ),
            ],
        )
        pres = _make_presentation([slide])
        theme = _make_theme()
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "percentage_sum_wrong" not in types


# ── Brand Compliance Checker ─────────────────────────────────────────────────


class TestBrandComplianceChecker:
    def test_flags_unapproved_font(self):
        """Font not in theme typography flagged as unapproved_font."""
        checker = BrandComplianceChecker()
        theme = _make_theme()  # heading_family=Arial, body_family=Calibri
        slide = _make_bullet_slide(
            elements=[
                HeadingElement(
                    content=HeadingContent(text="Title"),
                    style_overrides={"font_family": "Comic Sans MS"},
                ),
            ],
        )
        pres = _make_presentation([slide])
        layouts = [_make_layout_result(slide)]

        issues = checker.check(pres, layouts, theme)
        types = [i.type for i in issues]
        assert "unapproved_font" in types


# ── Auto-Fix Engine ──────────────────────────────────────────────────────────


class TestAutoFixEngine:
    def test_fixes_text_overflow_with_font_reduction(self):
        """AutoFixEngine reduces font for text_overflow, returns QAFix."""
        engine = AutoFixEngine()
        issue = QAIssue(
            type="text_overflow",
            severity="error",
            slide_index=0,
            region="content",
            message="Text overflows bounding box",
        )
        slide = _make_bullet_slide(
            elements=[
                HeadingElement(content=HeadingContent(text="Title")),
                BodyTextElement(content=BodyTextContent(text="Long text " * 30)),
            ],
        )
        pres = _make_presentation([slide])
        theme = _make_theme()
        layouts = [
            LayoutResult(
                slide=slide,
                positions={
                    "title": ResolvedPosition(x=0.75, y=0.5, width=8.5, height=1.0),
                    "content": ResolvedPosition(x=0.75, y=1.5, width=8.5, height=0.5),
                },
            )
        ]

        fixes = engine.fix_all([issue], pres, layouts, theme)
        assert len(fixes) >= 1
        fix = fixes[0]
        assert fix.issue_type == "text_overflow"
        assert fix.action == "font_reduction"
        assert isinstance(fix.before, (int, float))
        assert isinstance(fix.after, (int, float))
        assert fix.after < fix.before

    def test_fixes_contrast_failure(self):
        """AutoFixEngine adjusts color for contrast_failure, new color passes WCAG AA."""
        engine = AutoFixEngine()
        issue = QAIssue(
            type="contrast_failure",
            severity="error",
            slide_index=0,
            region="title",
            message="Contrast ratio below 4.5:1",
            details={"fg_color": "#CCCCCC", "bg_color": "#FFFFFF"},
        )
        slide = _make_bullet_slide(
            elements=[HeadingElement(content=HeadingContent(text="Title"))],
        )
        pres = _make_presentation([slide])
        theme = _make_theme(
            slide_masters={
                "default": SlideMaster(
                    background="#FFFFFF",
                    regions={
                        "title": ComponentStyle(
                            font_family="Arial", font_size=36, color="#CCCCCC",
                        ),
                    },
                )
            },
        )
        layouts = [_make_layout_result(slide)]

        fixes = engine.fix_all([issue], pres, layouts, theme)
        assert len(fixes) >= 1
        fix = [f for f in fixes if f.issue_type == "contrast_failure"][0]
        assert fix.action == "color_adjustment"

        # Verify the new color passes WCAG AA
        from deckforge.themes.contrast import passes_wcag_aa
        assert passes_wcag_aa(fix.after, "#FFFFFF")


# ── Executive Readiness Scorer ───────────────────────────────────────────────


class TestExecutiveReadinessScorer:
    def test_perfect_score_for_zero_issues(self):
        """Deck with zero issues scores 100."""
        scorer = ExecutiveReadinessScorer()
        report = scorer.score([], [])
        assert report.score == 100
        assert report.grade == "Executive Ready"

    def test_deducts_per_issue_type(self):
        """Each issue type deducts points, minimum 0 per category."""
        scorer = ExecutiveReadinessScorer()
        issues = [
            QAIssue(
                type="missing_title",
                severity="error",
                slide_index=0,
                region=None,
                message="Missing title",
            ),
            QAIssue(
                type="empty_slide",
                severity="error",
                slide_index=1,
                region=None,
                message="Empty slide",
            ),
        ]
        report = scorer.score(issues, [])
        assert report.score < 100
        assert report.score >= 0

    def test_returns_per_category_breakdown(self):
        """Report includes per-category breakdown with names and scores."""
        scorer = ExecutiveReadinessScorer()
        report = scorer.score([], [])
        assert len(report.categories) == 5
        for cat in report.categories:
            assert hasattr(cat, "name")
            assert hasattr(cat, "max_score")
            assert hasattr(cat, "score")
            assert cat.max_score == 20
            assert cat.score == 20  # Perfect score

    def test_minimum_zero_per_category(self):
        """Category score never goes below 0 even with many issues."""
        scorer = ExecutiveReadinessScorer()
        # Flood with structural issues
        issues = [
            QAIssue(
                type="missing_title",
                severity="error",
                slide_index=i,
                region=None,
                message="Missing title",
            )
            for i in range(50)
        ]
        report = scorer.score(issues, [])
        for cat in report.categories:
            assert cat.score >= 0
        assert report.score >= 0
