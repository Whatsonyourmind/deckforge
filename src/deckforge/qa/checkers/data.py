"""Data integrity checker — chart data validation, table totals, percentage sums."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deckforge.qa.types import QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme


class DataIntegrityChecker:
    """Check data integrity in a presentation."""

    def check(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAIssue]:
        raise NotImplementedError
