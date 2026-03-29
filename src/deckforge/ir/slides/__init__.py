"""Slides module — composes SlideUnion as discriminated union on 'slide_type' field."""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from deckforge.ir.slides.finance import (
    CapitalStructureSlide,
    CompTableSlide,
    DcfSummarySlide,
    DealOverviewSlide,
    InvestmentThesisSlide,
    MarketLandscapeSlide,
    ReturnsAnalysisSlide,
    RiskMatrixSlide,
    WaterfallChartSlide,
)
from deckforge.ir.slides.universal import (
    AgendaSlide,
    AppendixSlide,
    BulletPointsSlide,
    ChartSlideSlide,
    ComparisonSlide,
    FunnelSlide,
    IconGridSlide,
    ImageWithCaptionSlide,
    KeyMessageSlide,
    MapSlide,
    MatrixSlide,
    OrgChartSlide,
    ProcessFlowSlide,
    QAndASlide,
    QuoteSlide,
    SectionDividerSlide,
    StatsCalloutSlide,
    TableSlideSlide,
    TeamSlide,
    ThankYouSlide,
    TimelineSlide,
    TitleSlide,
    TwoColumnTextSlide,
)

SlideUnion = Annotated[
    Union[
        # Universal (23)
        TitleSlide,
        AgendaSlide,
        SectionDividerSlide,
        KeyMessageSlide,
        BulletPointsSlide,
        TwoColumnTextSlide,
        ComparisonSlide,
        TimelineSlide,
        ProcessFlowSlide,
        OrgChartSlide,
        TeamSlide,
        QuoteSlide,
        ImageWithCaptionSlide,
        IconGridSlide,
        StatsCalloutSlide,
        TableSlideSlide,
        ChartSlideSlide,
        MatrixSlide,
        FunnelSlide,
        MapSlide,
        ThankYouSlide,
        AppendixSlide,
        QAndASlide,
        # Finance (9)
        DcfSummarySlide,
        CompTableSlide,
        WaterfallChartSlide,
        DealOverviewSlide,
        ReturnsAnalysisSlide,
        CapitalStructureSlide,
        MarketLandscapeSlide,
        RiskMatrixSlide,
        InvestmentThesisSlide,
    ],
    Field(discriminator="slide_type"),
]

# Import ElementUnion to resolve forward references in BaseSlide.elements
from deckforge.ir.elements import ElementUnion  # noqa: F401
from deckforge.ir.slides.base import BaseSlide

# Rebuild all slide models to resolve the ElementUnion forward reference
BaseSlide.model_rebuild()
TitleSlide.model_rebuild()
AgendaSlide.model_rebuild()
SectionDividerSlide.model_rebuild()
KeyMessageSlide.model_rebuild()
BulletPointsSlide.model_rebuild()
TwoColumnTextSlide.model_rebuild()
ComparisonSlide.model_rebuild()
TimelineSlide.model_rebuild()
ProcessFlowSlide.model_rebuild()
OrgChartSlide.model_rebuild()
TeamSlide.model_rebuild()
QuoteSlide.model_rebuild()
ImageWithCaptionSlide.model_rebuild()
IconGridSlide.model_rebuild()
StatsCalloutSlide.model_rebuild()
TableSlideSlide.model_rebuild()
ChartSlideSlide.model_rebuild()
MatrixSlide.model_rebuild()
FunnelSlide.model_rebuild()
MapSlide.model_rebuild()
ThankYouSlide.model_rebuild()
AppendixSlide.model_rebuild()
QAndASlide.model_rebuild()
DcfSummarySlide.model_rebuild()
CompTableSlide.model_rebuild()
WaterfallChartSlide.model_rebuild()
DealOverviewSlide.model_rebuild()
ReturnsAnalysisSlide.model_rebuild()
CapitalStructureSlide.model_rebuild()
MarketLandscapeSlide.model_rebuild()
RiskMatrixSlide.model_rebuild()
InvestmentThesisSlide.model_rebuild()

__all__ = [
    "SlideUnion",
    # Universal
    "TitleSlide",
    "AgendaSlide",
    "SectionDividerSlide",
    "KeyMessageSlide",
    "BulletPointsSlide",
    "TwoColumnTextSlide",
    "ComparisonSlide",
    "TimelineSlide",
    "ProcessFlowSlide",
    "OrgChartSlide",
    "TeamSlide",
    "QuoteSlide",
    "ImageWithCaptionSlide",
    "IconGridSlide",
    "StatsCalloutSlide",
    "TableSlideSlide",
    "ChartSlideSlide",
    "MatrixSlide",
    "FunnelSlide",
    "MapSlide",
    "ThankYouSlide",
    "AppendixSlide",
    "QAndASlide",
    # Finance
    "DcfSummarySlide",
    "CompTableSlide",
    "WaterfallChartSlide",
    "DealOverviewSlide",
    "ReturnsAnalysisSlide",
    "CapitalStructureSlide",
    "MarketLandscapeSlide",
    "RiskMatrixSlide",
    "InvestmentThesisSlide",
]
