"""PPTEval-style scoring harness for DeckForge decks.

Inspired by the PPTEval evaluation framework (Zheng et al., "PPTAgent",
2025), which scores generated presentations on three independent
dimensions:

    * **Content**   -- is each slide informative, specific, and well filled?
    * **Design**    -- is the visual structure varied, balanced, and not
                       over/under-loaded?
    * **Coherence** -- does the deck read as one logical narrative, with an
                       opener, a body, and a close?

Each dimension is reported on a 1-5 scale (the PPTEval convention) and is
decomposed into named sub-scores so a reviewer can see *why* a deck lost
points.  The scorer is fully deterministic and operates on the deck
Intermediate Representation (IR) -- no rendering, network, or model calls --
so it is fast enough to run in CI on every commit.

The harness is heuristic, not a learned judge: it is a regression guard
("did this change make the demo decks measurably worse?") and a quick,
explainable quality read, not a replacement for human review.
"""

from __future__ import annotations

import json
import statistics
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# 1-5 PPTEval scale.
SCALE_MIN = 1.0
SCALE_MAX = 5.0

# A slide that carries no text-bearing or data-bearing element at all is "empty".
_TEXT_ELEMENT_TYPES = {"heading", "subheading", "body_text", "bullet_list", "quote"}
_DATA_ELEMENT_TYPES = {"chart", "table", "image", "metric"}

# Opener / closer slide types used for the Coherence narrative check.
_OPENER_TYPES = {"title_slide", "agenda", "section_divider", "key_message"}
_CLOSER_TYPES = {"thank_you", "q_and_a", "appendix"}


def _clamp(value: float) -> float:
    """Clamp a raw score into the [SCALE_MIN, SCALE_MAX] band."""
    return max(SCALE_MIN, min(SCALE_MAX, value))


@dataclass
class DimensionScore:
    """One PPTEval dimension (Content / Design / Coherence)."""

    name: str
    score: float  # 1.0 - 5.0
    sub_scores: dict[str, float] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "score": round(self.score, 2),
            "sub_scores": {k: round(v, 2) for k, v in self.sub_scores.items()},
            "notes": self.notes,
        }


@dataclass
class DeckScore:
    """Aggregate PPTEval score for a single deck."""

    name: str
    title: str
    slide_count: int
    content: DimensionScore
    design: DimensionScore
    coherence: DimensionScore

    @property
    def overall(self) -> float:
        """Mean of the three dimension scores (1-5)."""
        return round(
            statistics.fmean(
                [self.content.score, self.design.score, self.coherence.score]
            ),
            2,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "title": self.title,
            "slide_count": self.slide_count,
            "overall": self.overall,
            "dimensions": {
                "content": self.content.to_dict(),
                "design": self.design.to_dict(),
                "coherence": self.coherence.to_dict(),
            },
        }


def _element_type(element: Any) -> str:
    return getattr(element, "type", "") or ""


def _slide_type(slide: Any) -> str:
    return getattr(slide, "slide_type", "") or ""


def _extract_text(element: Any) -> str:
    """Pull all human-readable text out of one element, best-effort."""
    content = getattr(element, "content", None)
    if content is None:
        return ""
    # Pydantic content models or plain dicts.
    data = content.model_dump() if hasattr(content, "model_dump") else content
    if not isinstance(data, dict):
        return str(data)

    parts: list[str] = []
    if isinstance(data.get("text"), str):
        parts.append(data["text"])
    if isinstance(data.get("items"), list):
        parts.extend(str(i) for i in data["items"])
    # Tables: count header + cell text.
    if isinstance(data.get("headers"), list):
        parts.extend(str(h) for h in data["headers"])
    if isinstance(data.get("rows"), list):
        for row in data["rows"]:
            if isinstance(row, list):
                parts.extend(str(c) for c in row)
    return " ".join(p for p in parts if p)


class PPTEvalScorer:
    """Score a Presentation IR on Content, Design, and Coherence."""

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def score(self, presentation: Any, name: str = "deck") -> DeckScore:
        slides = list(getattr(presentation, "slides", []) or [])
        meta = getattr(presentation, "metadata", None)
        title = getattr(meta, "title", None) or name

        return DeckScore(
            name=name,
            title=title,
            slide_count=len(slides),
            content=self._score_content(slides),
            design=self._score_design(slides),
            coherence=self._score_coherence(slides),
        )

    # ------------------------------------------------------------------ #
    # Content: informativeness / specificity of slides
    # ------------------------------------------------------------------ #
    def _score_content(self, slides: list[Any]) -> DimensionScore:
        notes: list[str] = []
        if not slides:
            return DimensionScore("content", SCALE_MIN, notes=["no slides"])

        empty = 0
        title_present = 0
        word_counts: list[int] = []
        numeric_hits = 0  # slides that carry quantitative substance

        for slide in slides:
            elements = list(getattr(slide, "elements", []) or [])
            has_title = any(_element_type(e) == "heading" for e in elements)
            if has_title:
                title_present += 1

            body_types = {_element_type(e) for e in elements}
            text = " ".join(_extract_text(e) for e in elements).strip()
            words = len(text.split())
            word_counts.append(words)

            has_data = bool(body_types & _DATA_ELEMENT_TYPES)
            has_text = bool(body_types & _TEXT_ELEMENT_TYPES)
            if not has_data and not has_text and words == 0:
                empty += 1

            if has_data or any(ch.isdigit() for ch in text):
                numeric_hits += 1

        n = len(slides)
        # Sub-score: titling -- a titled slide is an informative slide.
        titling = SCALE_MAX * (title_present / n)
        # Sub-score: density -- reward slides that are filled but not bloated.
        # Ideal executive density ~ 15-90 words/slide.
        mean_words = statistics.fmean(word_counts) if word_counts else 0
        if mean_words <= 0:
            density = SCALE_MIN
        elif mean_words < 15:
            density = SCALE_MIN + 2.0 * (mean_words / 15)
        elif mean_words <= 90:
            density = SCALE_MAX
        else:
            # Past 90 words/slide, taper toward 3.0 (wall-of-text penalty).
            density = max(3.0, SCALE_MAX - (mean_words - 90) / 60)
        density = _clamp(density)
        # Sub-score: substance -- fraction of slides with data or numbers.
        substance = _clamp(SCALE_MIN + (SCALE_MAX - SCALE_MIN) * (numeric_hits / n))

        if empty:
            notes.append(f"{empty} empty slide(s)")
        if title_present < n:
            notes.append(f"{n - title_present} slide(s) without a heading")
        notes.append(f"mean {mean_words:.0f} words/slide")

        score = _clamp(statistics.fmean([titling, density, substance]))
        # Hard floor: empty slides cap content quality.
        if empty:
            score = min(score, SCALE_MAX - empty)
            score = _clamp(score)

        return DimensionScore(
            name="content",
            score=score,
            sub_scores={
                "titling": round(titling, 2),
                "density": round(density, 2),
                "substance": round(substance, 2),
            },
            notes=notes,
        )

    # ------------------------------------------------------------------ #
    # Design: visual variety and per-slide balance
    # ------------------------------------------------------------------ #
    def _score_design(self, slides: list[Any]) -> DimensionScore:
        notes: list[str] = []
        if not slides:
            return DimensionScore("design", SCALE_MIN, notes=["no slides"])

        slide_types = [_slide_type(s) for s in slides]
        n = len(slides)

        # Sub-score: layout variety -- distinct slide types / total (capped).
        distinct = len(set(slide_types))
        variety_ratio = distinct / n
        variety = _clamp(SCALE_MIN + (SCALE_MAX - SCALE_MIN) * min(1.0, variety_ratio / 0.6))

        # Sub-score: visual richness -- fraction of slides with a chart/table/image.
        visual_slides = 0
        balanced_slides = 0
        for slide in slides:
            elements = list(getattr(slide, "elements", []) or [])
            types = {_element_type(e) for e in elements}
            if types & _DATA_ELEMENT_TYPES:
                visual_slides += 1
            # Balance: a slide with 1-6 elements is well composed; 0 or 7+ is not.
            count = len(elements)
            if 1 <= count <= 6:
                balanced_slides += 1
        richness = _clamp(
            SCALE_MIN + (SCALE_MAX - SCALE_MIN) * min(1.0, (visual_slides / n) / 0.4)
        )
        balance = _clamp(SCALE_MIN + (SCALE_MAX - SCALE_MIN) * (balanced_slides / n))

        notes.append(f"{distinct} distinct layout(s) over {n} slides")
        notes.append(f"{visual_slides} slide(s) with chart/table/image")
        if balanced_slides < n:
            notes.append(f"{n - balanced_slides} slide(s) over/under-loaded")

        score = _clamp(statistics.fmean([variety, richness, balance]))
        return DimensionScore(
            name="design",
            score=score,
            sub_scores={
                "layout_variety": round(variety, 2),
                "visual_richness": round(richness, 2),
                "element_balance": round(balance, 2),
            },
            notes=notes,
        )

    # ------------------------------------------------------------------ #
    # Coherence: narrative flow across the deck
    # ------------------------------------------------------------------ #
    def _score_coherence(self, slides: list[Any]) -> DimensionScore:
        notes: list[str] = []
        if not slides:
            return DimensionScore("coherence", SCALE_MIN, notes=["no slides"])

        types = [_slide_type(s) for s in slides]
        n = len(slides)

        # Sub-score: opener -- does the deck start with a title/agenda?
        has_opener = types[0] in _OPENER_TYPES
        opener = SCALE_MAX if has_opener else 2.0
        if not has_opener:
            notes.append(f"deck opens on '{types[0]}', not a title/agenda")

        # Sub-score: closer -- does it end on a close/Q&A?
        has_closer = types[-1] in _CLOSER_TYPES
        closer = SCALE_MAX if has_closer else 3.0
        if not has_closer:
            notes.append(f"deck closes on '{types[-1]}', not a thank-you/Q&A")

        # Sub-score: speaker-note continuity -- a deck whose slides carry
        # speaker notes reads as a deliberate, connected narrative.
        noted = sum(
            1 for s in slides if (getattr(s, "speaker_notes", None) or "").strip()
        )
        continuity = _clamp(SCALE_MIN + (SCALE_MAX - SCALE_MIN) * (noted / n))
        notes.append(f"{noted}/{n} slides carry speaker notes")

        score = _clamp(statistics.fmean([opener, closer, continuity]))
        return DimensionScore(
            name="coherence",
            score=score,
            sub_scores={
                "opener": round(opener, 2),
                "closer": round(closer, 2),
                "note_continuity": round(continuity, 2),
            },
            notes=notes,
        )


def score_presentation(presentation: Any, name: str = "deck") -> DeckScore:
    """Convenience wrapper: score one already-validated Presentation IR."""
    return PPTEvalScorer().score(presentation, name=name)


def load_demo(demo_dir: Path) -> Any:
    """Load and validate a demo deck's ``ir.json`` into a Presentation.

    Imported lazily so importing :mod:`quality.ppteval` never forces the heavy
    ``deckforge`` package to import (keeps the scorer usable in isolation).
    """
    from deckforge.ir.normalize import normalize_ir
    from deckforge.ir.presentation import Presentation

    raw = json.loads((demo_dir / "ir.json").read_text(encoding="utf-8"))
    return Presentation.model_validate(normalize_ir(raw))
