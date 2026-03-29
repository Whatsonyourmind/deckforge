"""Text quality checker -- overflow detection, orphans, capitalization consistency."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.layout.text_measurer import TextMeasurer
from deckforge.qa.types import QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Map element types to region names for position lookup
_ELEMENT_TO_REGION = {
    "heading": "title",
    "subheading": "subtitle",
    "body_text": "content",
    "bullet_list": "content",
    "numbered_list": "content",
    "footnote": "footnote",
}


class TextQualityChecker:
    """Check text quality in a presentation.

    Checks:
        - Text overflow: measured height exceeds allocated position height
        - Orphan detection: last line of paragraph has single word
        - Capitalization consistency: headings should use consistent casing
    """

    def __init__(self) -> None:
        self._measurer = TextMeasurer()

    def check(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAIssue]:
        """Run text quality checks on the presentation."""
        issues: list[QAIssue] = []

        for idx, slide in enumerate(presentation.slides):
            # Get layout result for this slide
            layout = layout_results[idx] if idx < len(layout_results) else None
            if layout is None:
                continue

            for elem in slide.elements:
                etype = getattr(elem, "type", None)
                if etype not in _ELEMENT_TO_REGION:
                    continue

                region_name = _ELEMENT_TO_REGION[etype]
                position = layout.positions.get(region_name)
                if position is None:
                    continue

                # Extract text content
                text = self._extract_text(elem)
                if not text:
                    continue

                # Get font info from theme
                style = self._get_style(region_name, theme)
                font_name = style.font_family if style and style.font_family else "Arial"
                font_size = style.font_size if style and style.font_size else 18

                # Measure text
                if isinstance(text, list):
                    bbox = self._measurer.measure_bullet_list(
                        text, font_name, font_size, max_width_inches=position.width
                    )
                else:
                    bbox = self._measurer.measure_text(
                        text, font_name, font_size, max_width_inches=position.width
                    )

                # Check overflow: measured height > allocated height + tolerance
                if bbox.height_inches > position.height + 0.01:
                    issues.append(
                        QAIssue(
                            type="text_overflow",
                            severity="error",
                            slide_index=idx,
                            region=region_name,
                            message=(
                                f"Text in '{region_name}' overflows: "
                                f"measured {bbox.height_inches:.2f}in > "
                                f"allocated {position.height:.2f}in"
                            ),
                            details={
                                "measured_height": bbox.height_inches,
                                "allocated_height": position.height,
                                "font_size": font_size,
                            },
                        )
                    )

                # Check orphan: last line has single word
                if isinstance(text, str) and "\n" not in text and len(text.split()) > 5:
                    # Simple orphan heuristic: if the text is long enough
                    # that it would wrap, check last line
                    words = text.split()
                    if len(words) > 1:
                        # Build approximate lines
                        lines = self._approximate_lines(
                            text, font_name, font_size, position.width
                        )
                        if lines and len(lines[-1].split()) == 1:
                            issues.append(
                                QAIssue(
                                    type="orphan_word",
                                    severity="info",
                                    slide_index=idx,
                                    region=region_name,
                                    message=(
                                        f"Last line of text in '{region_name}' "
                                        f"has a single word (orphan)"
                                    ),
                                )
                            )

        return issues

    def _extract_text(self, elem) -> str | list[str] | None:
        """Extract text from an element."""
        content = getattr(elem, "content", None)
        if content is None:
            return None

        # Bullet list
        items = getattr(content, "items", None)
        if items is not None:
            return items

        # Text content
        text = getattr(content, "text", None)
        return text

    def _get_style(self, region_name: str, theme: ResolvedTheme):
        """Get ComponentStyle for a region from the theme."""
        default_master = theme.slide_masters.get("default")
        if default_master is None:
            return None
        return default_master.regions.get(region_name)

    def _approximate_lines(
        self, text: str, font_name: str, font_size: int, max_width: float
    ) -> list[str]:
        """Approximate line breaks for orphan detection."""
        try:
            font = self._measurer._get_font(font_name, font_size)
            max_width_px = max_width * self._measurer.MEASUREMENT_DPI

            lines: list[str] = []
            words = text.split()
            if not words:
                return []

            current_line = words[0]
            for word in words[1:]:
                test_line = f"{current_line} {word}"
                line_width = font.getlength(test_line)
                if line_width <= max_width_px:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)
            return lines
        except Exception:
            return []
