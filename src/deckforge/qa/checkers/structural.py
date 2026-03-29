"""Structural checker -- validates slide structure (titles, empty slides, narrative flow)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.ir.enums import SlideType
from deckforge.qa.types import QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Slide types that should open a presentation
_OPENER_TYPES = {SlideType.TITLE_SLIDE, SlideType.SECTION_DIVIDER}

# Heading element types that count as "having a title"
_HEADING_ELEMENT_TYPES = {"heading", "subheading"}


class StructuralChecker:
    """Check structural integrity of a presentation.

    Checks:
        - Every slide has at least one heading element (missing_title)
        - No slides with zero elements (empty_slide)
        - First slide should be title or section_header type (no_opener)
        - Narrative flow: slide_type sequence is reasonable (no_narrative_flow)
    """

    def check(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAIssue]:
        """Run structural checks on the presentation."""
        issues: list[QAIssue] = []

        for idx, slide in enumerate(presentation.slides):
            # Check empty slides
            if not slide.elements:
                issues.append(
                    QAIssue(
                        type="empty_slide",
                        severity="error",
                        slide_index=idx,
                        region=None,
                        message=f"Slide {idx + 1} has no elements",
                    )
                )
                continue  # No further checks on empty slides

            # Check for missing title (heading element)
            has_heading = any(
                getattr(elem, "type", None) in _HEADING_ELEMENT_TYPES
                for elem in slide.elements
            )
            if not has_heading:
                issues.append(
                    QAIssue(
                        type="missing_title",
                        severity="warning",
                        slide_index=idx,
                        region=None,
                        message=f"Slide {idx + 1} has no heading element",
                    )
                )

        # Check first slide is an opener type
        if presentation.slides:
            first_slide = presentation.slides[0]
            if first_slide.slide_type not in _OPENER_TYPES:
                issues.append(
                    QAIssue(
                        type="no_opener",
                        severity="info",
                        slide_index=0,
                        region=None,
                        message="First slide is not a title or section divider slide",
                    )
                )

        # Check narrative flow: detect consecutive same-type slides
        if len(presentation.slides) >= 3:
            for i in range(len(presentation.slides) - 2):
                if (
                    presentation.slides[i].slide_type
                    == presentation.slides[i + 1].slide_type
                    == presentation.slides[i + 2].slide_type
                ):
                    issues.append(
                        QAIssue(
                            type="no_narrative_flow",
                            severity="info",
                            slide_index=i,
                            region=None,
                            message=(
                                f"Slides {i + 1}-{i + 3} are all "
                                f"{presentation.slides[i].slide_type} type"
                            ),
                        )
                    )

        return issues
