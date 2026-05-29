"""DeckForge quality harness.

A PPTEval-style scoring harness that evaluates rendered demo decks on three
dimensions -- Content, Design, and Coherence -- each broken into sub-scores.

This package is intentionally dependency-light: it scores directly from the
deck Intermediate Representation (IR) without invoking the rendering pipeline,
so it runs in well under a second and needs no Postgres/Redis/LLM keys.
"""

from quality.ppteval import (
    DeckScore,
    DimensionScore,
    PPTEvalScorer,
    score_presentation,
)

__all__ = [
    "DeckScore",
    "DimensionScore",
    "PPTEvalScorer",
    "score_presentation",
]
