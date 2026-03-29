"""Finance slide renderer registry -- maps finance slide_type to renderer instances."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.rendering.slide_renderers.base import BaseFinanceSlideRenderer
from deckforge.rendering.slide_renderers.capital_structure import CapitalStructureRenderer
from deckforge.rendering.slide_renderers.comp_table import CompTableRenderer
from deckforge.rendering.slide_renderers.dcf_summary import DcfSummaryRenderer
from deckforge.rendering.slide_renderers.deal_overview import DealOverviewRenderer
from deckforge.rendering.slide_renderers.investment_thesis import InvestmentThesisRenderer
from deckforge.rendering.slide_renderers.market_landscape import MarketLandscapeRenderer
from deckforge.rendering.slide_renderers.returns_analysis import ReturnsAnalysisRenderer
from deckforge.rendering.slide_renderers.risk_matrix import RiskMatrixRenderer
from deckforge.rendering.slide_renderers.waterfall_slide import WaterfallSlideRenderer

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.slides.base import BaseSlide
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# ── Registry ──────────────────────────────────────────────────────────────────

FINANCE_SLIDE_RENDERERS: dict[str, BaseFinanceSlideRenderer] = {
    "comp_table": CompTableRenderer(),
    "dcf_summary": DcfSummaryRenderer(),
    "waterfall_chart": WaterfallSlideRenderer(),
    "deal_overview": DealOverviewRenderer(),
    "returns_analysis": ReturnsAnalysisRenderer(),
    "capital_structure": CapitalStructureRenderer(),
    "market_landscape": MarketLandscapeRenderer(),
    "investment_thesis": InvestmentThesisRenderer(),
    "risk_matrix": RiskMatrixRenderer(),
}


def render_finance_slide(
    slide: Slide,
    ir_slide: BaseSlide,
    theme: ResolvedTheme,
) -> bool:
    """Dispatch a finance slide to the appropriate renderer.

    Args:
        slide: python-pptx Slide object.
        ir_slide: IR slide model.
        theme: Resolved theme.

    Returns:
        True if a finance renderer handled the slide, False otherwise.
    """
    slide_type = ir_slide.slide_type
    if hasattr(slide_type, "value"):
        slide_type = slide_type.value

    renderer = FINANCE_SLIDE_RENDERERS.get(slide_type)
    if renderer is not None:
        renderer.render(slide, ir_slide, theme)
        return True
    return False


__all__ = [
    "FINANCE_SLIDE_RENDERERS",
    "BaseFinanceSlideRenderer",
    "render_finance_slide",
]
