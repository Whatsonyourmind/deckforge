"""Visual quality checker — WCAG contrast, font size floors, alignment consistency."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deckforge.qa.types import QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme


class VisualQualityChecker:
    """Check visual quality in a presentation."""

    def check(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAIssue]:
        raise NotImplementedError
