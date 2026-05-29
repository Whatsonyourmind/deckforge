"""Tests for the PPTEval-style quality harness (``quality/`` package).

Fast: scores the 5 bundled demo decks straight from IR -- no rendering,
network, DB, or LLM calls. Acts as a regression guard so a future change that
silently degrades the demo decks (drops titles, empties slides, breaks the
narrative arc) trips a test instead of shipping.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from quality.ppteval import (  # noqa: E402
    SCALE_MAX,
    SCALE_MIN,
    DeckScore,
    PPTEvalScorer,
    load_demo,
    score_presentation,
)
from quality.score_demos import DEMO_NAMES, DEMOS_DIR, score_all  # noqa: E402


@pytest.fixture(scope="module")
def demo_scores() -> dict[str, DeckScore]:
    scorer = PPTEvalScorer()
    out: dict[str, DeckScore] = {}
    for name in DEMO_NAMES:
        out[name] = scorer.score(load_demo(DEMOS_DIR / name), name=name)
    return out


def test_all_five_demos_present() -> None:
    for name in DEMO_NAMES:
        assert (DEMOS_DIR / name / "ir.json").exists(), f"missing demo: {name}"
    assert len(DEMO_NAMES) == 5


@pytest.mark.parametrize("name", DEMO_NAMES)
def test_demo_scores_in_band(demo_scores: dict[str, DeckScore], name: str) -> None:
    deck = demo_scores[name]
    for dim in (deck.content, deck.design, deck.coherence):
        assert SCALE_MIN <= dim.score <= SCALE_MAX, f"{name}/{dim.name} out of band"
        assert dim.sub_scores, f"{name}/{dim.name} has no sub-scores"
        for sub_name, sub_val in dim.sub_scores.items():
            assert SCALE_MIN <= sub_val <= SCALE_MAX, f"{name}/{dim.name}/{sub_name}"
    assert SCALE_MIN <= deck.overall <= SCALE_MAX


@pytest.mark.parametrize("name", DEMO_NAMES)
def test_demos_meet_quality_floor(demo_scores: dict[str, DeckScore], name: str) -> None:
    """The shipped demo decks are curated -- they must score well.

    A regression that drops them below 3.5/5 overall should fail CI.
    """
    deck = demo_scores[name]
    assert deck.slide_count >= 5, f"{name} unexpectedly short"
    assert deck.overall >= 3.5, f"{name} overall {deck.overall} below floor"


def test_dimensions_have_expected_subscores(demo_scores: dict[str, DeckScore]) -> None:
    deck = demo_scores["board-update"]
    assert set(deck.content.sub_scores) == {"titling", "density", "substance"}
    assert set(deck.design.sub_scores) == {
        "layout_variety",
        "visual_richness",
        "element_balance",
    }
    assert set(deck.coherence.sub_scores) == {"opener", "closer", "note_continuity"}


def test_empty_deck_floors_content() -> None:
    """A deck with no slides scores the minimum and never raises."""

    class _Empty:
        slides: list = []
        metadata = None

    deck = score_presentation(_Empty(), name="empty")
    assert deck.content.score == SCALE_MIN
    assert deck.slide_count == 0


def test_score_all_report_shape() -> None:
    results = score_all()
    assert len(results) == len(DEMO_NAMES)
    for r in results:
        assert "error" not in r, f"{r.get('name')}: {r.get('error')}"
        assert {"name", "title", "slide_count", "overall", "dimensions"} <= set(r)
        assert set(r["dimensions"]) == {"content", "design", "coherence"}


def test_scoring_is_deterministic() -> None:
    a = score_all()
    b = score_all()
    assert [r["overall"] for r in a] == [r["overall"] for r in b]
