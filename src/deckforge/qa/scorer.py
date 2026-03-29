"""Executive readiness scorer -- 5-category scoring from 0 to 100."""

from __future__ import annotations

import logging

from deckforge.qa.types import QACategory, QAFix, QAIssue, QAReport

logger = logging.getLogger(__name__)

# 5 scoring categories, each worth 20 points max
_CATEGORIES = [
    "structural",
    "text_quality",
    "visual_quality",
    "data_integrity",
    "brand_compliance",
]

# Map issue types to categories
_ISSUE_CATEGORY_MAP: dict[str, str] = {
    # Structural
    "missing_title": "structural",
    "empty_slide": "structural",
    "no_opener": "structural",
    "no_narrative_flow": "structural",
    # Text quality
    "text_overflow": "text_quality",
    "orphan_word": "text_quality",
    "capitalization_inconsistency": "text_quality",
    # Visual quality
    "contrast_failure": "visual_quality",
    "font_below_floor": "visual_quality",
    "alignment_inconsistency": "visual_quality",
    # Data integrity
    "nan_data_value": "data_integrity",
    "percentage_sum_wrong": "data_integrity",
    "table_total_mismatch": "data_integrity",
    # Brand compliance
    "unapproved_font": "brand_compliance",
    "unapproved_color": "brand_compliance",
    "missing_logo": "brand_compliance",
    "missing_confidentiality": "brand_compliance",
}

# Point deductions per issue type
_DEDUCTIONS: dict[str, int] = {
    # Structural (high impact)
    "missing_title": 5,
    "empty_slide": 8,
    "no_opener": 3,
    "no_narrative_flow": 2,
    # Text quality
    "text_overflow": 6,
    "orphan_word": 1,
    "capitalization_inconsistency": 2,
    # Visual quality
    "contrast_failure": 7,
    "font_below_floor": 4,
    "alignment_inconsistency": 2,
    # Data integrity
    "nan_data_value": 8,
    "percentage_sum_wrong": 5,
    "table_total_mismatch": 6,
    # Brand compliance
    "unapproved_font": 5,
    "unapproved_color": 3,
    "missing_logo": 2,
    "missing_confidentiality": 3,
}

# Grade thresholds
_GRADES = [
    (90, "Executive Ready"),
    (70, "Review Recommended"),
    (50, "Needs Attention"),
    (0, "Not Ready"),
]


class ExecutiveReadinessScorer:
    """Score a deck's executive readiness from 0 to 100.

    5 categories each worth 20 points:
        - Structural (slide structure, flow)
        - Text quality (overflow, orphans, casing)
        - Visual quality (contrast, font sizes, alignment)
        - Data integrity (NaN, sums, totals)
        - Brand compliance (fonts, colors, logo)

    Grade thresholds:
        - 90-100: Executive Ready
        - 70-89: Review Recommended
        - 50-69: Needs Attention
        - 0-49: Not Ready
    """

    MAX_CATEGORY_SCORE = 20

    def score(self, issues: list[QAIssue], fixes: list[QAFix]) -> QAReport:
        """Score a presentation based on remaining issues and applied fixes.

        Args:
            issues: Remaining unfixed issues.
            fixes: Applied fixes (not counted against score).

        Returns:
            QAReport with score, grade, and per-category breakdown.
        """
        # Build per-category issue lists
        category_issues: dict[str, list[QAIssue]] = {cat: [] for cat in _CATEGORIES}
        category_fixes: dict[str, list[QAFix]] = {cat: [] for cat in _CATEGORIES}

        for issue in issues:
            cat = _ISSUE_CATEGORY_MAP.get(issue.type, "structural")
            if cat in category_issues:
                category_issues[cat].append(issue)

        for fix in fixes:
            cat = _ISSUE_CATEGORY_MAP.get(fix.issue_type, "structural")
            if cat in category_fixes:
                category_fixes[cat].append(fix)

        # Score each category
        categories: list[QACategory] = []
        total_score = 0

        for cat_name in _CATEGORIES:
            cat_issues = category_issues[cat_name]
            cat_fixes = category_fixes[cat_name]

            # Calculate deductions
            deduction = sum(
                _DEDUCTIONS.get(issue.type, 3) for issue in cat_issues
            )

            cat_score = max(0, self.MAX_CATEGORY_SCORE - deduction)

            categories.append(
                QACategory(
                    name=cat_name,
                    max_score=self.MAX_CATEGORY_SCORE,
                    score=cat_score,
                    issues=cat_issues,
                    fixes=cat_fixes,
                )
            )
            total_score += cat_score

        # Determine grade
        grade = "Not Ready"
        for threshold, label in _GRADES:
            if total_score >= threshold:
                grade = label
                break

        return QAReport(
            score=total_score,
            grade=grade,
            categories=categories,
            issues=issues,
            fixes=fixes,
        )
