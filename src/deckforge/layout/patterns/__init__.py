"""Layout patterns — maps SlideType to layout region/constraint generators.

PATTERN_REGISTRY maps every SlideType value string to a BaseLayoutPattern
subclass. Use get_pattern() to instantiate the correct pattern for a slide.
"""

from __future__ import annotations

from deckforge.layout.patterns.base import BaseLayoutPattern
from deckforge.layout.patterns.bullets import BulletPointsPattern
from deckforge.layout.patterns.chart import ChartSlidePattern
from deckforge.layout.patterns.generic import GenericPattern
from deckforge.layout.patterns.image import ImageWithCaptionPattern
from deckforge.layout.patterns.section import SectionDividerPattern
from deckforge.layout.patterns.stats import StatsCalloutPattern
from deckforge.layout.patterns.table import TableSlidePattern
from deckforge.layout.patterns.title import TitleSlidePattern
from deckforge.layout.patterns.two_column import TwoColumnPattern

# Maps every SlideType.value -> pattern class (32 entries)
PATTERN_REGISTRY: dict[str, type[BaseLayoutPattern]] = {
    # Dedicated patterns
    "title_slide": TitleSlidePattern,
    "bullet_points": BulletPointsPattern,
    "two_column_text": TwoColumnPattern,
    "comparison": TwoColumnPattern,
    "chart_slide": ChartSlidePattern,
    "table_slide": TableSlidePattern,
    "section_divider": SectionDividerPattern,
    "key_message": SectionDividerPattern,
    "image_with_caption": ImageWithCaptionPattern,
    "stats_callout": StatsCalloutPattern,
    "quote_slide": SectionDividerPattern,
    # Generic fallback for remaining universal types
    "agenda": GenericPattern,
    "timeline": GenericPattern,
    "process_flow": GenericPattern,
    "org_chart": GenericPattern,
    "team_slide": GenericPattern,
    "icon_grid": GenericPattern,
    "matrix": GenericPattern,
    "funnel": GenericPattern,
    "map_slide": GenericPattern,
    "thank_you": GenericPattern,
    "appendix": GenericPattern,
    "q_and_a": GenericPattern,
    # Finance vertical (9 types)
    "dcf_summary": GenericPattern,
    "comp_table": GenericPattern,
    "waterfall_chart": GenericPattern,
    "deal_overview": GenericPattern,
    "returns_analysis": GenericPattern,
    "capital_structure": GenericPattern,
    "market_landscape": GenericPattern,
    "risk_matrix": GenericPattern,
    "investment_thesis": GenericPattern,
}


def get_pattern(slide_type: str) -> BaseLayoutPattern:
    """Instantiate the correct layout pattern for a given slide type.

    Args:
        slide_type: SlideType value string (e.g., "bullet_points").

    Returns:
        Instance of the appropriate BaseLayoutPattern subclass.

    Raises:
        KeyError: If slide_type is not in PATTERN_REGISTRY.
    """
    pattern_cls = PATTERN_REGISTRY[slide_type]
    return pattern_cls()


__all__ = [
    "BaseLayoutPattern",
    "BulletPointsPattern",
    "ChartSlidePattern",
    "GenericPattern",
    "ImageWithCaptionPattern",
    "PATTERN_REGISTRY",
    "SectionDividerPattern",
    "StatsCalloutPattern",
    "TableSlidePattern",
    "TitleSlidePattern",
    "TwoColumnPattern",
    "get_pattern",
]
