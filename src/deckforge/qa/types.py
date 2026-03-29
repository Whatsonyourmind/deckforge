"""QA type models — QAIssue, QAFix, QACategory, QAReport."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class QAIssue(BaseModel):
    """A single quality issue found during QA checking."""

    type: str
    severity: Literal["error", "warning", "info"]
    slide_index: int
    region: str | None = None
    message: str
    details: dict[str, Any] | None = None


class QAFix(BaseModel):
    """Record of an auto-fix applied to resolve a QA issue."""

    issue_type: str
    slide_index: int
    region: str | None = None
    action: str
    before: Any = None
    after: Any = None


class QACategory(BaseModel):
    """Score breakdown for a single QA category."""

    name: str
    max_score: int = 20
    score: int = 20
    issues: list[QAIssue] = Field(default_factory=list)
    fixes: list[QAFix] = Field(default_factory=list)


class QAReport(BaseModel):
    """Complete QA report with score, grade, and breakdowns."""

    score: int
    grade: str
    categories: list[QACategory] = Field(default_factory=list)
    issues: list[QAIssue] = Field(default_factory=list)
    fixes: list[QAFix] = Field(default_factory=list)
