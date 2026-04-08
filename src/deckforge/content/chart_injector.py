"""Chart element injection helper for the NL content pipeline.

This module closes the gap identified by STATE decision [03-01]: the
content pipeline (intent -> outline -> expand -> refine) historically
never produced ``chart`` IR elements, which meant NL-generated decks
silently shipped without any of the 24 chart renderers that back the
``/v1/render`` path.

Responsibilities:

1. **Heuristic numeric extraction** from slide outline + expanded text.
2. **Chart-intent detection** -- decide whether a slide should carry a
   chart element based on its numeric content and slide_type.
3. **Validation of LLM-emitted chart elements** against the Pydantic
   :class:`~deckforge.ir.elements.data.ChartElement` schema.
4. **Recommender fallback** -- when the LLM produces no chart or a
   malformed one for a data-heavy slide, build a minimal but valid chart
   element using :func:`deckforge.charts.recommender.recommend_chart_type`
   plus the numbers we extracted.

The module is intentionally side-effect free and synchronous: it can be
called from ``slide_writer.py`` inside the async expand path or from
tests without touching the LLM.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from deckforge.charts.recommender import ChartRecommendation, recommend_chart_type

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Slide types where a chart is strongly expected if the content carries
# numeric data. These are the finance + universal chart-ish slide types.
CHART_EXPECTING_SLIDE_TYPES = frozenset(
    {
        "chart_slide",
        "stats_callout",
        "dcf_summary",
        "comp_table",
        "waterfall_chart",
        "deal_overview",
        "returns_analysis",
        "capital_structure",
        "market_landscape",
        "risk_matrix",
        "investment_thesis",
    }
)

# Keywords in the slide content that strongly imply a data visualization.
_DATA_KEYWORDS = (
    "revenue",
    "growth",
    "margin",
    "ebitda",
    "trend",
    "quarter",
    "forecast",
    "projection",
    "market share",
    "share",
    "pipeline",
    "breakdown",
    "allocation",
    "distribution",
    "performance",
    "yoy",
    "cagr",
    "arr",
    "mrr",
    "roi",
)

# Numeric pattern: optional sign, digits, decimal, optional suffix (%, B, M, K, bps)
_NUMBER_PATTERN = re.compile(
    r"(?P<sign>[-+]?)\$?(?P<num>\d{1,3}(?:[,\d]{0,12})(?:\.\d+)?)"
    r"\s?(?P<suffix>%|bps|[BMK]|bn|mn|tn)?",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def extract_numbers(text: str) -> list[float]:
    """Return a list of numeric values parsed from free-form text.

    Understands common financial suffixes (``%``, ``bps``, ``B``, ``M``, ``K``)
    and dollar prefixes. Suffixes are converted into plain floats where
    sensible (e.g. ``"$1.2B"`` -> ``1_200_000_000``, ``"23%"`` -> ``23``,
    ``"200bps"`` -> ``200``).
    """
    if not text:
        return []

    results: list[float] = []
    for match in _NUMBER_PATTERN.finditer(text):
        raw = match.group("num").replace(",", "")
        if not raw or raw == ".":
            continue
        try:
            value = float(raw)
        except ValueError:
            continue

        if match.group("sign") == "-":
            value = -value

        suffix = (match.group("suffix") or "").lower()
        if suffix == "b" or suffix == "bn":
            value *= 1_000_000_000
        elif suffix == "m" or suffix == "mn":
            value *= 1_000_000
        elif suffix == "k":
            value *= 1_000
        elif suffix == "tn":
            value *= 1_000_000_000_000
        # "%", "bps" are left as their numeric magnitude
        results.append(value)

    return results


def has_numeric_content(text: str) -> bool:
    """Return True when *text* contains at least two numeric tokens.

    Two is used as the floor because a single number rarely justifies a
    chart (it's a KPI card at that point), whereas two or more usually
    imply a comparison or trend.
    """
    return len(extract_numbers(text)) >= 2


def mentions_data_keywords(text: str) -> bool:
    """Check whether *text* contains domain keywords that hint at data."""
    if not text:
        return False
    lower = text.lower()
    return any(keyword in lower for keyword in _DATA_KEYWORDS)


def slide_should_have_chart(
    slide_type: str,
    content_blob: str,
) -> bool:
    """Decide if a slide is a candidate for a chart element.

    Rules:
    - A chart-expecting slide_type with any numeric content -> yes.
    - A non-chart slide_type needs BOTH numeric content AND a data
      keyword to qualify (avoids false positives on narrative slides).
    """
    if slide_type in CHART_EXPECTING_SLIDE_TYPES and has_numeric_content(
        content_blob
    ):
        return True
    if has_numeric_content(content_blob) and mentions_data_keywords(content_blob):
        return True
    return False


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_chart_element(element: dict[str, Any]) -> bool:
    """Validate a chart element dict against the IR ChartElement schema.

    Returns ``True`` when the element can be parsed by the Pydantic model;
    ``False`` otherwise. Logs a debug line on failure so callers can
    decide to fall back to the recommender.
    """
    if not isinstance(element, dict):
        return False
    if element.get("type") != "chart":
        return False
    if "chart_data" not in element:
        return False

    try:
        from deckforge.ir.elements.data import ChartElement

        ChartElement.model_validate(element)
        return True
    except Exception as exc:  # pragma: no cover - pydantic error path
        logger.debug("Chart element failed validation: %s", exc)
        return False


# ---------------------------------------------------------------------------
# Recommender fallback
# ---------------------------------------------------------------------------


def _categories_from_key_points(key_points: list[str]) -> list[str]:
    """Derive category labels from key_point strings.

    Strips leading numbers/symbols so that a bullet like ``"2024 $1.2B"``
    becomes the category ``"2024"``. Falls back to ``"Item N"``.
    """
    categories: list[str] = []
    for i, kp in enumerate(key_points):
        # Take the first word cluster before the first number, else first 3 words
        tokens = kp.split()
        label_tokens: list[str] = []
        for tok in tokens:
            if any(ch.isdigit() for ch in tok):
                break
            label_tokens.append(tok)
        label = " ".join(label_tokens).strip(":,;").strip()
        if not label:
            label = f"Item {i + 1}"
        categories.append(label[:32])
    return categories


def build_chart_from_recommendation(
    slide_type: str,
    headline: str,
    key_points: list[str],
    content_blob: str,
) -> dict[str, Any] | None:
    """Produce a minimal valid chart element dict via the recommender.

    Returns ``None`` if no numeric data could be extracted.
    """
    numbers = extract_numbers(content_blob or " ".join(key_points))
    if len(numbers) < 2:
        return None

    # Describe the data shape to the recommender.
    data_shape = {
        "series_count": 1,
        "category_count": len(numbers),
        "has_dates": any(
            re.search(r"\b(19|20)\d{2}\b", kp) for kp in key_points
        ),
    }
    recommendation: ChartRecommendation = recommend_chart_type(data_shape)
    chart_type = recommendation.chart_type

    title = headline or "Data Overview"

    # Build category labels. Prefer key_points when their count matches
    # the number count, else generate generic "Series N" labels.
    if len(key_points) == len(numbers):
        categories = _categories_from_key_points(key_points)
    else:
        categories = [f"Item {i + 1}" for i in range(len(numbers))]

    # Dispatch to the chart_type-specific IR shape. We only need to produce
    # something that ChartElement.model_validate() accepts. Unknown/exotic
    # chart types fall back to a bar chart to guarantee renderer coverage.
    values = [float(n) for n in numbers]

    if chart_type in ("pie", "donut"):
        chart_data = {
            "chart_type": chart_type,
            "labels": categories,
            "values": values,
            "title": title,
        }
    elif chart_type in ("line", "multi_line", "area", "stacked_area"):
        chart_data = {
            "chart_type": chart_type,
            "categories": categories,
            "series": [{"name": title, "values": values}],
            "title": title,
        }
    elif chart_type == "waterfall":
        chart_data = {
            "chart_type": "waterfall",
            "categories": categories,
            "values": values,
            "title": title,
        }
    elif chart_type == "funnel":
        chart_data = {
            "chart_type": "funnel",
            "stages": categories,
            "values": values,
            "title": title,
        }
    else:
        # Default: bar/grouped_bar/stacked_bar/horizontal_bar all share shape
        if chart_type not in (
            "bar",
            "grouped_bar",
            "stacked_bar",
            "horizontal_bar",
        ):
            chart_type = "bar"
        chart_data = {
            "chart_type": chart_type,
            "categories": categories,
            "series": [{"name": title, "values": values}],
            "title": title,
        }

    element = {
        "type": "chart",
        "chart_data": chart_data,
    }

    if not validate_chart_element(element):
        logger.warning(
            "Recommender fallback produced invalid chart element for slide_type=%s",
            slide_type,
        )
        return None

    logger.debug(
        "Recommender fallback built %s chart for slide_type=%s (%d values)",
        chart_type,
        slide_type,
        len(values),
    )
    return element


# ---------------------------------------------------------------------------
# Public entry point used by slide_writer
# ---------------------------------------------------------------------------


def ensure_chart_element(
    slide_type: str,
    headline: str,
    key_points: list[str],
    elements: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return *elements* with a valid chart element guaranteed when applicable.

    Post-processing pass run after the LLM expand call:

    1. Validates every existing ``chart`` element; drops malformed ones.
    2. If the slide qualifies as chart-bearing (see
       :func:`slide_should_have_chart`) and no valid chart remains, calls
       the recommender fallback to inject one.
    3. Non-chart elements are passed through untouched.

    The function never raises -- failures are logged and the original
    element list is preserved.
    """
    content_blob = "\n".join(
        [headline or "", *(key_points or []), *_stringify_elements(elements)]
    )

    cleaned: list[dict[str, Any]] = []
    has_valid_chart = False
    for el in elements:
        if isinstance(el, dict) and el.get("type") == "chart":
            if validate_chart_element(el):
                has_valid_chart = True
                cleaned.append(el)
            else:
                logger.info(
                    "Dropping malformed chart element from slide_type=%s",
                    slide_type,
                )
            continue
        cleaned.append(el)

    if has_valid_chart:
        return cleaned

    if not slide_should_have_chart(slide_type, content_blob):
        return cleaned

    fallback = build_chart_from_recommendation(
        slide_type=slide_type,
        headline=headline,
        key_points=key_points or [],
        content_blob=content_blob,
    )
    if fallback is not None:
        cleaned.append(fallback)
        logger.info(
            "Injected recommender-fallback chart element into slide_type=%s",
            slide_type,
        )
    return cleaned


# Keys inside element ``content`` dicts that carry meaningful free-form
# text (vs styling/level metadata whose digits are noise like ``"h1"``).
_TEXTUAL_CONTENT_KEYS = frozenset(
    {"text", "items", "label", "title", "caption", "value", "subtitle", "body"}
)


def _stringify_elements(elements: list[dict[str, Any]]) -> list[str]:
    """Flatten element content into plain strings for number extraction.

    Only textual keys are considered so that styling metadata like
    ``level: "h1"`` or ``style: "disc"`` does not leak digits into the
    numeric extraction step.
    """
    out: list[str] = []
    for el in elements or []:
        if not isinstance(el, dict):
            continue
        content = el.get("content")
        if isinstance(content, dict):
            for key, value in content.items():
                if key not in _TEXTUAL_CONTENT_KEYS:
                    continue
                if isinstance(value, str):
                    out.append(value)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, str):
                            out.append(item)
        elif isinstance(content, str):
            out.append(content)
    return out


__all__ = [
    "CHART_EXPECTING_SLIDE_TYPES",
    "build_chart_from_recommendation",
    "ensure_chart_element",
    "extract_numbers",
    "has_numeric_content",
    "mentions_data_keywords",
    "slide_should_have_chart",
    "validate_chart_element",
]
