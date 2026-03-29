"""Finance slide type models — 9 slide types for financial presentations."""

from __future__ import annotations

from typing import Literal

from deckforge.ir.slides.base import BaseSlide


class DcfSummarySlide(BaseSlide):
    slide_type: Literal["dcf_summary"] = "dcf_summary"
    discount_rate_range: list[float] | None = None
    terminal_growth_range: list[float] | None = None


class CompTableSlide(BaseSlide):
    slide_type: Literal["comp_table"] = "comp_table"
    highlight_column: str | None = None
    sort_by: str | None = None


class WaterfallChartSlide(BaseSlide):
    slide_type: Literal["waterfall_chart"] = "waterfall_chart"
    show_running_total: bool = True


class DealOverviewSlide(BaseSlide):
    slide_type: Literal["deal_overview"] = "deal_overview"


class ReturnsAnalysisSlide(BaseSlide):
    slide_type: Literal["returns_analysis"] = "returns_analysis"


class CapitalStructureSlide(BaseSlide):
    slide_type: Literal["capital_structure"] = "capital_structure"


class MarketLandscapeSlide(BaseSlide):
    slide_type: Literal["market_landscape"] = "market_landscape"


class RiskMatrixSlide(BaseSlide):
    slide_type: Literal["risk_matrix"] = "risk_matrix"
    axes_labels: dict | None = None


class InvestmentThesisSlide(BaseSlide):
    slide_type: Literal["investment_thesis"] = "investment_thesis"
