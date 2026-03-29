"""LayoutEngine — orchestrates measure -> constrain -> solve -> verify -> adapt."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deckforge.layout.grid import GridSystem
from deckforge.layout.overflow import AdaptiveOverflowHandler
from deckforge.layout.patterns import PATTERN_REGISTRY, get_pattern
from deckforge.layout.solver import SlideLayoutSolver
from deckforge.layout.types import BoundingBox, LayoutResult, ResolvedPosition

if TYPE_CHECKING:
    from deckforge.ir.brand_kit import BrandKit
    from deckforge.ir.elements.base import Position
    from deckforge.ir.presentation import Presentation
    from deckforge.ir.slides.base import BaseSlide
    from deckforge.layout.text_measurer import TextMeasurer
    from deckforge.themes.registry import ThemeRegistry
    from deckforge.themes.types import ResolvedTheme, SlideMaster

logger = logging.getLogger(__name__)


# Mapping from element type to region name
_ELEMENT_TO_REGION: dict[str, str] = {
    "heading": "title",
    "subheading": "subtitle",
    "bullet_list": "bullets",
    "numbered_list": "bullets",
    "body_text": "content",
    "footnote": "footnote",
    "chart": "chart_area",
    "table": "table_area",
    "image": "image_area",
    "kpi_card": "stat_cards",
    "metric_group": "stat_cards",
}


class LayoutEngine:
    """Orchestrates the layout pipeline for slides and presentations.

    Pipeline per slide:
        1. Select pattern from PATTERN_REGISTRY
        2. Get SlideMaster from theme
        3. Measure all text elements
        4. Create regions and constraints
        5. Solve constraints
        6. Check overflow and run adaptive cascade if needed
        7. Apply positions to slide elements

    Args:
        text_measurer: TextMeasurer for measuring text dimensions.
        theme_registry: ThemeRegistry for resolving themes.
    """

    def __init__(self, text_measurer: Any, theme_registry: Any) -> None:
        self._measurer = text_measurer
        self._theme_registry = theme_registry

    def layout_slide(
        self,
        slide: Any,
        theme: Any,
        grid: GridSystem | None = None,
    ) -> LayoutResult:
        """Layout a single slide using the appropriate pattern.

        Args:
            slide: BaseSlide to layout.
            theme: ResolvedTheme with spacing, typography.
            grid: Optional GridSystem; created from theme.spacing if None.

        Returns:
            LayoutResult with resolved positions for each region.
        """
        if grid is None:
            grid = self._create_grid(theme)

        # 1. Select pattern
        slide_type = slide.slide_type
        if hasattr(slide_type, "value"):
            slide_type = slide_type.value

        pattern = get_pattern(slide_type)

        # 2. Get slide master
        master = theme.slide_masters.get(slide_type) or theme.slide_masters.get("default")

        # 3. Measure elements
        measurements = self._measure_elements(slide, theme, master, grid)

        # 4. Create regions and constraints
        regions = pattern.create_regions()
        constraints = pattern.create_constraints(regions, grid, measurements, theme)

        # 5. Solve
        solver = SlideLayoutSolver()
        solver.add_constraints(constraints)
        positions = solver.solve(regions)

        # 6. Handle infeasible or overflow
        if positions is None:
            logger.warning("Infeasible constraints for slide type %s, triggering overflow", slide_type)
            # Create fallback positions and run overflow handler
            overflow_handler = AdaptiveOverflowHandler(self._measurer)
            fallback_positions = self._fallback_positions(regions, grid)
            result = overflow_handler.handle(
                slide, fallback_positions, measurements, theme, grid, pattern
            )
            self._apply_positions(result.slide, result.positions)
            return result

        # Check for overflow
        overflow_handler = AdaptiveOverflowHandler(self._measurer)
        overflow_regions = overflow_handler.detect_overflow(positions, measurements)

        if overflow_regions:
            result = overflow_handler.handle(
                slide, positions, measurements, theme, grid, pattern
            )
            self._apply_positions(result.slide, result.positions)
            return result

        # 7. No overflow — apply positions and return
        self._apply_positions(slide, positions)
        return LayoutResult(slide=slide, positions=positions, overflow=False)

    def layout_presentation(
        self,
        presentation: Any,
        brand_kit: Any | None = None,
    ) -> list[LayoutResult]:
        """Layout all slides in a presentation.

        Args:
            presentation: Presentation with slides and theme.
            brand_kit: Optional BrandKit overlay.

        Returns:
            List of LayoutResult, one per slide (split slides flattened).
        """
        # Resolve theme
        bk = brand_kit or getattr(presentation, "brand_kit", None)
        theme = self._theme_registry.get_theme(presentation.theme, bk)

        # Create grid from theme
        grid = self._create_grid(theme)

        results: list[LayoutResult] = []
        for slide in presentation.slides:
            result = self.layout_slide(slide, theme, grid)
            results.append(result)

            # Flatten split slides
            if result.split_slides:
                for split_slide in result.split_slides[1:]:  # Skip first (it's the original)
                    split_result = self.layout_slide(split_slide, theme, grid)
                    results.append(split_result)

        return results

    def _create_grid(self, theme: Any) -> GridSystem:
        """Create a GridSystem from theme spacing."""
        spacing = theme.spacing
        return GridSystem(
            margin_left=spacing.margin_left,
            margin_right=spacing.margin_right,
            margin_top=spacing.margin_top,
            margin_bottom=spacing.margin_bottom,
            gutter=spacing.gutter,
        )

    def _measure_elements(
        self,
        slide: Any,
        theme: Any,
        master: Any | None,
        grid: GridSystem,
    ) -> dict[str, BoundingBox]:
        """Measure all text elements on a slide, returning region->BoundingBox map.

        Maps elements to regions by type and measures using theme/master font settings.
        """
        measurements: dict[str, BoundingBox] = {}

        for elem in slide.elements:
            etype = getattr(elem, "type", None)
            if etype is None:
                continue

            # Determine region name
            region_name = _ELEMENT_TO_REGION.get(etype)
            if region_name is None:
                continue

            # Skip if already measured (first element wins for each region)
            if region_name in measurements:
                continue

            # Get font settings from slide master
            font_family, font_size = self._get_font_settings(
                region_name, master, theme
            )

            content = getattr(elem, "content", None)
            if content is None:
                continue

            # Measure based on content type
            if hasattr(content, "items"):
                # Bullet list or numbered list
                measurements[region_name] = self._measurer.measure_bullet_list(
                    content.items,
                    font_family,
                    font_size,
                    max_width_inches=grid.content_width,
                )
            elif hasattr(content, "text"):
                measurements[region_name] = self._measurer.measure_text(
                    content.text,
                    font_family,
                    font_size,
                    max_width_inches=grid.content_width,
                )
            else:
                # Non-text elements (chart, table, image) get default size
                measurements[region_name] = BoundingBox(
                    width_inches=grid.content_width,
                    height_inches=4.0,
                )

        return measurements

    def _get_font_settings(
        self,
        region_name: str,
        master: Any | None,
        theme: Any,
    ) -> tuple[str, int]:
        """Get font family and size for a region.

        Checks slide master first, falls back to theme typography defaults.
        """
        if master is not None:
            style = master.regions.get(region_name)
            if style is not None:
                family = style.font_family or theme.typography.heading_family
                size = style.font_size or theme.typography.scale.get("body", 18)
                return family, size

        # Fallback to theme defaults
        region_to_scale: dict[str, str] = {
            "title": "h2",
            "subtitle": "subtitle",
            "bullets": "body",
            "content": "body",
            "footnote": "footnote",
            "chart_area": "body",
            "table_area": "body",
            "image_area": "body",
            "stat_cards": "body",
        }
        scale_key = region_to_scale.get(region_name, "body")

        if scale_key.startswith("h"):
            family = theme.typography.heading_family
        else:
            family = theme.typography.body_family

        size = theme.typography.scale.get(scale_key, 18)
        return family, size

    def _apply_positions(
        self,
        slide: Any,
        positions: dict[str, ResolvedPosition],
    ) -> None:
        """Apply resolved positions to slide elements as Position objects."""
        from deckforge.ir.elements.base import Position

        for elem in slide.elements:
            etype = getattr(elem, "type", None)
            if etype is None:
                continue

            region_name = _ELEMENT_TO_REGION.get(etype)
            if region_name is None:
                continue

            pos = positions.get(region_name)
            if pos is None:
                continue

            elem.position = Position(
                x=pos.x,
                y=pos.y,
                width=pos.width,
                height=pos.height,
            )

    def _fallback_positions(
        self,
        regions: list[Any],
        grid: GridSystem,
    ) -> dict[str, ResolvedPosition]:
        """Create fallback positions when constraints are infeasible.

        Distributes regions evenly in the content area.
        """
        n = len(regions)
        if n == 0:
            return {}

        region_height = grid.content_height / n
        result: dict[str, ResolvedPosition] = {}

        for i, region in enumerate(regions):
            result[region.name] = ResolvedPosition(
                x=grid.content_left,
                y=grid.content_top + i * region_height,
                width=grid.content_width,
                height=region_height,
            )

        return result
