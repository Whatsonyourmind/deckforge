"""Element renderer registry -- maps ElementType values to renderer instances."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.ir.elements.base import Position
from deckforge.ir.enums import ElementType
from deckforge.rendering.element_renderers.base import BaseElementRenderer
from deckforge.rendering.element_renderers.data_viz import (
    GaugeRenderer,
    KpiCardRenderer,
    MetricGroupRenderer,
    ProgressBarRenderer,
    SparklineRenderer,
)
from deckforge.rendering.element_renderers.image import ImageRenderer
from deckforge.rendering.element_renderers.shape import (
    DividerRenderer,
    LogoRenderer,
    ShapeRenderer,
    SpacerRenderer,
)
from deckforge.rendering.element_renderers.table import TableRenderer
from deckforge.rendering.element_renderers.text import (
    BulletListRenderer,
    CalloutBoxRenderer,
    NumberedListRenderer,
    PullQuoteRenderer,
    TextRenderer,
)

if TYPE_CHECKING:
    from pptx.slide import Slide

    from deckforge.ir.elements.base import BaseElement
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


class _NoOpRenderer(BaseElementRenderer):
    """No-op renderer for layout-only or handled-elsewhere elements."""

    def render(self, slide: Slide, element: BaseElement, position: Position, theme: ResolvedTheme) -> None:  # type: ignore[override]
        logger.debug("No-op render for element type: %s", getattr(element, "type", "unknown"))


_text_renderer = TextRenderer()
_bullet_renderer = BulletListRenderer()
_numbered_renderer = NumberedListRenderer()
_callout_renderer = CalloutBoxRenderer()
_quote_renderer = PullQuoteRenderer()
_table_renderer = TableRenderer()
_image_renderer = ImageRenderer()
_shape_renderer = ShapeRenderer()
_divider_renderer = DividerRenderer()
_spacer_renderer = SpacerRenderer()
_logo_renderer = LogoRenderer()
_kpi_renderer = KpiCardRenderer()
_metric_group_renderer = MetricGroupRenderer()
_progress_renderer = ProgressBarRenderer()
_gauge_renderer = GaugeRenderer()
_sparkline_renderer = SparklineRenderer()
_noop = _NoOpRenderer()


ELEMENT_RENDERERS: dict[str, BaseElementRenderer] = {
    # Text
    ElementType.HEADING.value: _text_renderer,
    ElementType.SUBHEADING.value: _text_renderer,
    ElementType.BODY_TEXT.value: _text_renderer,
    ElementType.BULLET_LIST.value: _bullet_renderer,
    ElementType.NUMBERED_LIST.value: _numbered_renderer,
    ElementType.CALLOUT_BOX.value: _callout_renderer,
    ElementType.PULL_QUOTE.value: _quote_renderer,
    ElementType.FOOTNOTE.value: _text_renderer,
    ElementType.LABEL.value: _text_renderer,
    # Data
    ElementType.TABLE.value: _table_renderer,
    ElementType.CHART.value: _noop,  # Chart renderer is in separate module (03-02)
    ElementType.KPI_CARD.value: _kpi_renderer,
    ElementType.METRIC_GROUP.value: _metric_group_renderer,
    ElementType.PROGRESS_BAR.value: _progress_renderer,
    ElementType.GAUGE.value: _gauge_renderer,
    ElementType.SPARKLINE.value: _sparkline_renderer,
    # Visual
    ElementType.IMAGE.value: _image_renderer,
    ElementType.ICON.value: _noop,  # Icon rendering requires icon set assets
    ElementType.SHAPE.value: _shape_renderer,
    ElementType.DIVIDER.value: _divider_renderer,
    ElementType.SPACER.value: _spacer_renderer,
    ElementType.LOGO.value: _logo_renderer,
    ElementType.BACKGROUND.value: _noop,  # Background handled at slide level by PptxRenderer
    # Layout (structural only, not rendered)
    ElementType.CONTAINER.value: _noop,
    ElementType.COLUMN.value: _noop,
    ElementType.ROW.value: _noop,
    ElementType.GRID_CELL.value: _noop,
}


def render_element(
    slide: Slide,
    element: BaseElement,
    position: Position,
    theme: ResolvedTheme,
) -> None:
    """Render an element onto a slide using the appropriate renderer.

    Args:
        slide: python-pptx Slide object.
        element: IR element to render.
        position: Resolved position for the element.
        theme: Resolved theme for styling.
    """
    element_type = element.type
    if hasattr(element_type, "value"):
        element_type = element_type.value

    renderer = ELEMENT_RENDERERS.get(element_type)
    if renderer is None:
        logger.warning("No renderer registered for element type: %s", element_type)
        return

    renderer.render(slide, element, position, theme)


__all__ = [
    "ELEMENT_RENDERERS",
    "BaseElementRenderer",
    "render_element",
]
