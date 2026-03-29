"""Executive readiness scorer — 5-category scoring from 0 to 100."""

from __future__ import annotations

from deckforge.qa.types import QAFix, QAIssue, QAReport


class ExecutiveReadinessScorer:
    """Score a deck's executive readiness from 0 to 100."""

    def score(self, issues: list[QAIssue], fixes: list[QAFix]) -> QAReport:
        raise NotImplementedError
