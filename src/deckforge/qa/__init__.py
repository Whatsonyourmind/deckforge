"""QA pipeline -- 5-pass quality assurance for DeckForge presentations."""

from deckforge.qa.pipeline import QAPipeline
from deckforge.qa.types import QACategory, QAFix, QAIssue, QAReport

__all__ = [
    "QAPipeline",
    "QACategory",
    "QAFix",
    "QAIssue",
    "QAReport",
]
