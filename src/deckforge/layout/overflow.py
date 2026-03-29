"""Adaptive overflow handler — font reduction, reflow, and slide splitting."""

from __future__ import annotations

import copy
import logging
from typing import TYPE_CHECKING, Any

from deckforge.layout.types import BoundingBox, LayoutResult, ResolvedPosition

if TYPE_CHECKING:
    from deckforge.layout.grid import GridSystem
    from deckforge.layout.patterns.base import BaseLayoutPattern
    from deckforge.layout.solver import SlideLayoutSolver
    from deckforge.layout.text_measurer import TextMeasurer
    from deckforge.themes.types import ComponentStyle, ResolvedTheme

logger = logging.getLogger(__name__)


class AdaptiveOverflowHandler:
    """Handles text overflow via a 3-step adaptive cascade.

    Steps:
        1. Font reduction: Reduce font size by step (min 10pt body / 14pt heading).
        2. Reflow: Re-measure with narrower width for more aggressive wrapping.
        3. Split: Divide content across multiple continuation slides.

    Args:
        measurer: TextMeasurer instance for re-measurement after font changes.
        min_body_font: Minimum body font size in points.
        min_heading_font: Minimum heading font size in points.
        font_reduction_step: Points to reduce per iteration.
        max_iterations: Maximum font reduction iterations.
    """

    def __init__(
        self,
        measurer: Any,
        min_body_font: int = 10,
        min_heading_font: int = 14,
        font_reduction_step: int = 2,
        max_iterations: int = 5,
    ) -> None:
        self._measurer = measurer
        self.min_body_font = min_body_font
        self.min_heading_font = min_heading_font
        self.font_reduction_step = font_reduction_step
        self.max_iterations = max_iterations

    def detect_overflow(
        self,
        positions: dict[str, ResolvedPosition],
        measurements: dict[str, BoundingBox],
    ) -> list[str]:
        """Detect which regions have measured height exceeding allocated height.

        Args:
            positions: Solved positions for each region.
            measurements: Measured BoundingBox for each region.

        Returns:
            List of region names where overflow is detected.
        """
        overflow_regions: list[str] = []
        for name, pos in positions.items():
            meas = measurements.get(name)
            if meas is None:
                continue
            if meas.height_inches > pos.height + 0.01:  # Small tolerance
                overflow_regions.append(name)
        return overflow_regions

    def handle(
        self,
        slide: Any,
        positions: dict[str, ResolvedPosition],
        measurements: dict[str, BoundingBox],
        theme: Any,
        grid: Any,
        pattern: BaseLayoutPattern,
    ) -> LayoutResult:
        """Run the adaptive overflow cascade.

        Args:
            slide: The BaseSlide that overflowed.
            positions: Current solved positions.
            measurements: Current measurements.
            theme: ResolvedTheme for font/spacing info.
            grid: GridSystem for layout geometry.
            pattern: The layout pattern for this slide type.

        Returns:
            LayoutResult with overflow=True and possibly split_slides.
        """
        from deckforge.layout.solver import SlideLayoutSolver

        overflow_regions = self.detect_overflow(positions, measurements)
        if not overflow_regions:
            return LayoutResult(slide=slide, positions=positions, overflow=False)

        # Step 1: Font reduction
        current_measurements = dict(measurements)
        current_positions = dict(positions)

        for iteration in range(self.max_iterations):
            overflow_regions = self.detect_overflow(current_positions, current_measurements)
            if not overflow_regions:
                return LayoutResult(
                    slide=slide, positions=current_positions, overflow=False
                )

            # Try reducing font for overflow regions
            any_reduced = False
            for region_name in overflow_regions:
                style = self._get_region_style(region_name, theme)
                if style is None or style.font_size is None:
                    continue

                is_heading = region_name in ("title", "subtitle")
                min_size = self.min_heading_font if is_heading else self.min_body_font

                if style.font_size <= min_size:
                    continue

                new_style = self._reduce_font_in_style(
                    style, self.font_reduction_step, min_size
                )
                if new_style.font_size < style.font_size:
                    any_reduced = True
                    # Re-measure with reduced font
                    new_meas = self._remeasure_region(
                        slide, region_name, new_style, grid
                    )
                    if new_meas is not None:
                        current_measurements[region_name] = new_meas

            if not any_reduced:
                break

            # Re-solve with new measurements
            regions = pattern.create_regions()
            constraints = pattern.create_constraints(
                regions, grid, current_measurements, theme
            )
            solver = SlideLayoutSolver()
            solver.add_constraints(constraints)
            result = solver.solve(regions)
            if result is not None:
                current_positions = result

        # Step 2: Reflow (re-measure with narrower width)
        overflow_regions = self.detect_overflow(current_positions, current_measurements)
        if overflow_regions:
            for region_name in overflow_regions:
                pos = current_positions.get(region_name)
                if pos is None:
                    continue
                narrower_width = pos.width * 0.9
                new_meas = self._remeasure_region_with_width(
                    slide, region_name, theme, narrower_width
                )
                if new_meas is not None:
                    current_measurements[region_name] = new_meas

            regions = pattern.create_regions()
            constraints = pattern.create_constraints(
                regions, grid, current_measurements, theme
            )
            solver = SlideLayoutSolver()
            solver.add_constraints(constraints)
            result = solver.solve(regions)
            if result is not None:
                current_positions = result

        # Step 3: Split if still overflowing
        overflow_regions = self.detect_overflow(current_positions, current_measurements)
        if overflow_regions:
            split_region = overflow_regions[0]
            split_slides = self._split_slide(slide, split_region)
            return LayoutResult(
                slide=slide,
                positions=current_positions,
                overflow=True,
                split_slides=split_slides,
            )

        return LayoutResult(
            slide=slide, positions=current_positions, overflow=True
        )

    def _reduce_font_in_style(
        self,
        style: Any,
        reduction: int,
        min_size: int,
    ) -> Any:
        """Return a new ComponentStyle with reduced font_size, clamped to min_size.

        Args:
            style: ComponentStyle with font_size.
            reduction: Points to subtract.
            min_size: Minimum allowed font size.

        Returns:
            New ComponentStyle with reduced font_size.
        """
        from deckforge.themes.types import ComponentStyle

        current_size = style.font_size or 18
        new_size = max(current_size - reduction, min_size)

        return ComponentStyle(
            font_family=style.font_family,
            font_size=new_size,
            font_weight=style.font_weight,
            color=style.color,
            alignment=style.alignment,
            background=style.background,
            bullet_color=style.bullet_color,
            indent=style.indent,
            columns=style.columns,
            min_height=style.min_height,
        )

    def _get_region_style(self, region_name: str, theme: Any) -> Any | None:
        """Get the ComponentStyle for a region from the theme's default slide master."""
        default_master = theme.slide_masters.get("default")
        if default_master is None:
            return None
        return default_master.regions.get(region_name)

    def _remeasure_region(
        self,
        slide: Any,
        region_name: str,
        style: Any,
        grid: Any,
    ) -> BoundingBox | None:
        """Re-measure a region's content with a new style (font size)."""
        text = self._extract_region_text(slide, region_name)
        if text is None:
            return None

        font_name = style.font_family or "Arial"
        font_size = style.font_size or 18

        if isinstance(text, list):
            return self._measurer.measure_bullet_list(
                text, font_name, font_size, max_width_inches=grid.content_width
            )
        return self._measurer.measure_text(
            text, font_name, font_size, max_width_inches=grid.content_width
        )

    def _remeasure_region_with_width(
        self,
        slide: Any,
        region_name: str,
        theme: Any,
        max_width: float,
    ) -> BoundingBox | None:
        """Re-measure a region with a narrower max_width for aggressive reflow."""
        text = self._extract_region_text(slide, region_name)
        if text is None:
            return None

        style = self._get_region_style(region_name, theme)
        font_name = style.font_family if style and style.font_family else "Arial"
        font_size = style.font_size if style and style.font_size else 18

        if isinstance(text, list):
            return self._measurer.measure_bullet_list(
                text, font_name, font_size, max_width_inches=max_width
            )
        return self._measurer.measure_text(
            text, font_name, font_size, max_width_inches=max_width
        )

    def _extract_region_text(self, slide: Any, region_name: str) -> str | list[str] | None:
        """Extract text content from a slide for a given region name."""
        for elem in slide.elements:
            etype = getattr(elem, "type", None)
            content = getattr(elem, "content", None)
            if content is None:
                continue

            if region_name in ("title",) and etype in ("heading",):
                return getattr(content, "text", None)
            if region_name in ("subtitle",) and etype in ("subheading",):
                return getattr(content, "text", None)
            if region_name in ("bullets",) and etype in ("bullet_list",):
                return getattr(content, "items", None)
            if region_name in ("content",) and etype in ("body_text", "bullet_list"):
                items = getattr(content, "items", None)
                if items is not None:
                    return items
                return getattr(content, "text", None)
            if region_name in ("footnote",) and etype in ("footnote",):
                return getattr(content, "text", None)

        return None

    def _split_slide(self, slide: Any, overflow_region: str) -> list[Any]:
        """Split a slide into multiple continuation slides.

        For bullet_list content, divides items across slides.
        For body_text, splits at roughly the midpoint.

        Args:
            slide: The overflowing slide.
            overflow_region: The region that overflowed.

        Returns:
            List of slides (including the original, modified).
        """
        from deckforge.ir.elements.text import (
            BulletListContent,
            BulletListElement,
            HeadingContent,
            HeadingElement,
        )

        # Find bullet list elements for splitting
        bullet_elem = None
        heading_elem = None
        other_elements = []

        for elem in slide.elements:
            etype = getattr(elem, "type", None)
            if etype == "bullet_list" and bullet_elem is None:
                bullet_elem = elem
            elif etype == "heading" and heading_elem is None:
                heading_elem = elem
            else:
                other_elements.append(elem)

        if bullet_elem is not None and hasattr(bullet_elem.content, "items"):
            items = bullet_elem.content.items
            mid = len(items) // 2
            if mid < 1:
                mid = 1

            first_items = items[:mid]
            second_items = items[mid:]

            # First slide: original title + first half of items
            first_slide = slide.model_copy(deep=True)
            first_slide.elements = []
            if heading_elem is not None:
                first_slide.elements.append(heading_elem.model_copy(deep=True))
            first_slide.elements.append(
                BulletListElement(content=BulletListContent(
                    items=first_items, style=bullet_elem.content.style
                ))
            )

            # Continuation slide: title with "(cont.)" + second half
            cont_title_text = "Continued"
            if heading_elem is not None:
                cont_title_text = heading_elem.content.text + " (cont.)"

            cont_slide = slide.model_copy(deep=True)
            cont_slide.elements = [
                HeadingElement(content=HeadingContent(text=cont_title_text)),
                BulletListElement(content=BulletListContent(
                    items=second_items, style=bullet_elem.content.style
                )),
            ]

            return [first_slide, cont_slide]

        # Fallback: return original slide as-is (cannot split non-bullet content easily)
        return [slide]
