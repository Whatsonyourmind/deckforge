"""Universal slide type models — 23 slide types for general presentations."""

from __future__ import annotations

from typing import Literal

from deckforge.ir.slides.base import BaseSlide


class TitleSlide(BaseSlide):
    slide_type: Literal["title_slide"] = "title_slide"


class AgendaSlide(BaseSlide):
    slide_type: Literal["agenda"] = "agenda"


class SectionDividerSlide(BaseSlide):
    slide_type: Literal["section_divider"] = "section_divider"


class KeyMessageSlide(BaseSlide):
    slide_type: Literal["key_message"] = "key_message"


class BulletPointsSlide(BaseSlide):
    slide_type: Literal["bullet_points"] = "bullet_points"


class TwoColumnTextSlide(BaseSlide):
    slide_type: Literal["two_column_text"] = "two_column_text"


class ComparisonSlide(BaseSlide):
    slide_type: Literal["comparison"] = "comparison"


class TimelineSlide(BaseSlide):
    slide_type: Literal["timeline"] = "timeline"
    timeline_direction: Literal["horizontal", "vertical"] = "horizontal"


class ProcessFlowSlide(BaseSlide):
    slide_type: Literal["process_flow"] = "process_flow"
    flow_direction: Literal["horizontal", "vertical", "circular"] = "horizontal"


class OrgChartSlide(BaseSlide):
    slide_type: Literal["org_chart"] = "org_chart"


class TeamSlide(BaseSlide):
    slide_type: Literal["team_slide"] = "team_slide"


class QuoteSlide(BaseSlide):
    slide_type: Literal["quote_slide"] = "quote_slide"


class ImageWithCaptionSlide(BaseSlide):
    slide_type: Literal["image_with_caption"] = "image_with_caption"


class IconGridSlide(BaseSlide):
    slide_type: Literal["icon_grid"] = "icon_grid"
    columns: int = 3


class StatsCalloutSlide(BaseSlide):
    slide_type: Literal["stats_callout"] = "stats_callout"


class TableSlideSlide(BaseSlide):
    slide_type: Literal["table_slide"] = "table_slide"


class ChartSlideSlide(BaseSlide):
    slide_type: Literal["chart_slide"] = "chart_slide"


class MatrixSlide(BaseSlide):
    slide_type: Literal["matrix"] = "matrix"


class FunnelSlide(BaseSlide):
    slide_type: Literal["funnel"] = "funnel"


class MapSlide(BaseSlide):
    slide_type: Literal["map_slide"] = "map_slide"


class ThankYouSlide(BaseSlide):
    slide_type: Literal["thank_you"] = "thank_you"


class AppendixSlide(BaseSlide):
    slide_type: Literal["appendix"] = "appendix"


class QAndASlide(BaseSlide):
    slide_type: Literal["q_and_a"] = "q_and_a"
