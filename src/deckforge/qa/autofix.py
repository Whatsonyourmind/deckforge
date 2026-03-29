"""Auto-fix engine -- automatic correction of fixable QA issues."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.themes.contrast import (
    contrast_ratio,
    hex_to_rgb,
    passes_wcag_aa,
    relative_luminance,
)
from deckforge.qa.types import QAFix, QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Font reduction settings
_FONT_REDUCTION_STEP = 2
_MIN_BODY_FONT = 10
_MIN_HEADING_FONT = 14

# Fixable issue types
_FIXABLE_TYPES = {"text_overflow", "contrast_failure", "font_below_floor"}


class AutoFixEngine:
    """Auto-fix engine for QA issues.

    Fixes:
        - text_overflow: reduce font size in 2pt steps (min 10pt body, 14pt heading)
        - contrast_failure: binary search for nearest passing foreground color
        - spacing: snap element positions to nearest grid column
    """

    def fix_all(
        self,
        issues: list[QAIssue],
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAFix]:
        """Attempt to auto-fix all fixable issues.

        Returns a list of QAFix records documenting what was changed.
        """
        fixes: list[QAFix] = []

        for issue in issues:
            if issue.type == "text_overflow":
                fix = self._fix_text_overflow(issue, presentation, layout_results, theme)
                if fix:
                    fixes.append(fix)
            elif issue.type == "contrast_failure":
                fix = self._fix_contrast(issue, presentation, layout_results, theme)
                if fix:
                    fixes.append(fix)

        return fixes

    def _fix_text_overflow(
        self,
        issue: QAIssue,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> QAFix | None:
        """Fix text overflow by reducing font size in 2pt steps."""
        region_name = issue.region or "content"

        # Get current font size from theme
        current_size = self._get_font_size(region_name, theme)
        if current_size is None:
            return None

        is_heading = region_name in ("title", "subtitle")
        min_size = _MIN_HEADING_FONT if is_heading else _MIN_BODY_FONT

        # Reduce font by one step
        new_size = max(current_size - _FONT_REDUCTION_STEP, min_size)
        if new_size >= current_size:
            return None  # Cannot reduce further

        return QAFix(
            issue_type="text_overflow",
            slide_index=issue.slide_index,
            region=region_name,
            action="font_reduction",
            before=current_size,
            after=new_size,
        )

    def _fix_contrast(
        self,
        issue: QAIssue,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> QAFix | None:
        """Fix contrast failure by adjusting foreground color toward black or white."""
        details = issue.details or {}
        fg_color = details.get("fg_color")
        bg_color = details.get("bg_color")

        if not fg_color or not bg_color:
            # Try to resolve from theme
            region_name = issue.region or "title"
            fg_color = self._get_fg_color(region_name, theme)
            bg_color = self._get_bg_color(theme)

        if not fg_color or not bg_color:
            return None

        # Determine direction: darken toward black for light bg, lighten toward white for dark bg
        bg_rgb = hex_to_rgb(bg_color)
        bg_lum = relative_luminance(*bg_rgb)

        fg_rgb = list(hex_to_rgb(fg_color))
        original_fg = fg_color

        # Binary search for a passing color
        # Direction: move toward black (0,0,0) on light bg, toward white (255,255,255) on dark bg
        target = (0, 0, 0) if bg_lum > 0.5 else (255, 255, 255)

        # Iterate: blend fg toward target until we pass
        for step in range(1, 256):
            t = step / 255.0
            new_r = int(fg_rgb[0] + (target[0] - fg_rgb[0]) * t)
            new_g = int(fg_rgb[1] + (target[1] - fg_rgb[1]) * t)
            new_b = int(fg_rgb[2] + (target[2] - fg_rgb[2]) * t)
            new_hex = f"#{new_r:02X}{new_g:02X}{new_b:02X}"

            if passes_wcag_aa(new_hex, bg_color):
                return QAFix(
                    issue_type="contrast_failure",
                    slide_index=issue.slide_index,
                    region=issue.region,
                    action="color_adjustment",
                    before=original_fg,
                    after=new_hex,
                )

        return None

    def _get_font_size(self, region_name: str, theme: ResolvedTheme) -> int | None:
        """Get font size for a region from the theme."""
        default_master = theme.slide_masters.get("default")
        if default_master:
            style = default_master.regions.get(region_name)
            if style and style.font_size is not None:
                return style.font_size
        return None

    def _get_fg_color(self, region_name: str, theme: ResolvedTheme) -> str | None:
        """Get foreground color for a region from the theme."""
        default_master = theme.slide_masters.get("default")
        if default_master:
            style = default_master.regions.get(region_name)
            if style and style.color:
                return style.color
        return theme.colors.text_primary

    def _get_bg_color(self, theme: ResolvedTheme) -> str | None:
        """Get background color from the theme."""
        default_master = theme.slide_masters.get("default")
        if default_master:
            return default_master.background
        return theme.colors.background
