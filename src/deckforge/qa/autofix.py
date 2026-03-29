"""Auto-fix engine — automatic correction of fixable QA issues."""

from __future__ import annotations

from typing import TYPE_CHECKING

from deckforge.qa.types import QAFix, QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme


class AutoFixEngine:
    """Auto-fix engine for QA issues."""

    def fix_all(
        self,
        issues: list[QAIssue],
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAFix]:
        raise NotImplementedError
