"""QA pipeline -- 5-pass quality assurance with auto-fix and scoring."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.qa.checkers.brand import BrandComplianceChecker
from deckforge.qa.checkers.data import DataIntegrityChecker
from deckforge.qa.checkers.structural import StructuralChecker
from deckforge.qa.checkers.text import TextQualityChecker
from deckforge.qa.checkers.visual import VisualQualityChecker
from deckforge.qa.autofix import AutoFixEngine
from deckforge.qa.scorer import ExecutiveReadinessScorer
from deckforge.qa.types import QAFix, QAIssue, QAReport

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.registry import ThemeRegistry
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


class QAPipeline:
    """5-pass QA pipeline with auto-fix and scoring.

    Orchestrates all 5 checkers in sequence, applies auto-fixes for
    fixable issues, and scores executive readiness 0-100.

    Usage:
        pipeline = QAPipeline()
        report = pipeline.run(presentation, layout_results, theme)
        print(f"Score: {report.score}/100 -- {report.grade}")
    """

    def __init__(self, theme_registry: ThemeRegistry | None = None) -> None:
        self.structural = StructuralChecker()
        self.text = TextQualityChecker()
        self.visual = VisualQualityChecker()
        self.data = DataIntegrityChecker()
        self.brand = BrandComplianceChecker()
        self.autofix = AutoFixEngine()
        self.scorer = ExecutiveReadinessScorer()

        if theme_registry is not None:
            self._theme_registry = theme_registry
        else:
            # Lazy import to avoid circular import at module level
            from deckforge.themes.registry import ThemeRegistry
            self._theme_registry = ThemeRegistry()

    def run(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme | None = None,
    ) -> QAReport:
        """Run full QA pipeline: check -> autofix -> re-check -> score.

        Args:
            presentation: The IR Presentation to check.
            layout_results: Layout results for each slide.
            theme: Resolved theme. If None, resolved from presentation.theme.

        Returns:
            QAReport with score, grade, per-category breakdown, issues, fixes.
        """
        if theme is None:
            theme = self._theme_registry.get_theme(
                presentation.theme, presentation.brand_kit
            )

        # Pass 1-5: Run all checkers
        logger.info("QA: Running 5-pass quality checks...")
        all_issues: list[QAIssue] = []

        logger.debug("QA Pass 1: Structural checks")
        all_issues.extend(self.structural.check(presentation, layout_results, theme))

        logger.debug("QA Pass 2: Text quality checks")
        all_issues.extend(self.text.check(presentation, layout_results, theme))

        logger.debug("QA Pass 3: Visual quality checks")
        all_issues.extend(self.visual.check(presentation, layout_results, theme))

        logger.debug("QA Pass 4: Data integrity checks")
        all_issues.extend(self.data.check(presentation, layout_results, theme))

        logger.debug("QA Pass 5: Brand compliance checks")
        all_issues.extend(self.brand.check(presentation, layout_results, theme))

        logger.info("QA: Found %d issues across 5 passes", len(all_issues))

        # Auto-fix fixable issues
        logger.debug("QA: Applying auto-fixes...")
        fixes = self.autofix.fix_all(all_issues, presentation, layout_results, theme)
        logger.info("QA: Applied %d auto-fixes", len(fixes))

        # Re-check after fixes to get final issue list
        # Remove issues that were successfully fixed
        final_issues = [i for i in all_issues if not self._was_fixed(i, fixes)]
        logger.info(
            "QA: %d issues remain after auto-fix (%d resolved)",
            len(final_issues),
            len(all_issues) - len(final_issues),
        )

        # Score
        report = self.scorer.score(final_issues, fixes)
        logger.info("QA: Score %d/100 -- %s", report.score, report.grade)

        return report

    def _was_fixed(self, issue: QAIssue, fixes: list[QAFix]) -> bool:
        """Check if an issue was addressed by a fix."""
        for fix in fixes:
            if (
                fix.issue_type == issue.type
                and fix.slide_index == issue.slide_index
                and fix.region == issue.region
            ):
                return True
        return False
