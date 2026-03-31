"""Normalize simplified IR payloads into the strict Pydantic schema format.

The demo IRs and user-authored payloads use a simplified shorthand that
does not match the strict Pydantic discriminated-union schema.  This
module provides a single ``normalize_ir`` function that transparently
converts simplified payloads *before* Pydantic validation so that:

1. ``POST /v1/render`` accepts both simplified and strict IR.
2. If the input already matches the strict schema it passes through unchanged.
3. All transformation logic lives in one reusable place (not buried in scripts).

The transform rules mirror ``scripts/generate_demos.py`` but are
production-quality, idempotent, and safe for arbitrary input.
"""

from __future__ import annotations

import copy
import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Slide-type aliases: simplified demo names -> strict SlideType enum values
# ---------------------------------------------------------------------------
SLIDE_TYPE_MAP: dict[str, str] = {
    # Shorthand aliases
    "title": "title_slide",
    "bullets": "bullet_points",
    "chart": "chart_slide",
    "table": "table_slide",
    "two_column": "two_column_text",
    "team": "team_slide",
    "closing": "thank_you",
    "quote": "quote_slide",
    "executive_summary": "key_message",
    # Identity mappings (already correct)
    "title_slide": "title_slide",
    "bullet_points": "bullet_points",
    "chart_slide": "chart_slide",
    "table_slide": "table_slide",
    "two_column_text": "two_column_text",
    "team_slide": "team_slide",
    "thank_you": "thank_you",
    "comparison": "comparison",
    "timeline": "timeline",
    "process_flow": "process_flow",
    "section_divider": "section_divider",
    "key_message": "key_message",
    "quote_slide": "quote_slide",
    "stats_callout": "stats_callout",
    "agenda": "agenda",
    "image_with_caption": "image_with_caption",
    "icon_grid": "icon_grid",
    "matrix": "matrix",
    "funnel": "funnel",
    "map_slide": "map_slide",
    "appendix": "appendix",
    "q_and_a": "q_and_a",
    "org_chart": "org_chart",
    # Finance
    "dcf_summary": "dcf_summary",
    "comp_table": "comp_table",
    "waterfall_chart": "waterfall_chart",
    "deal_overview": "deal_overview",
    "returns_analysis": "returns_analysis",
    "capital_structure": "capital_structure",
    "market_landscape": "market_landscape",
    "risk_matrix": "risk_matrix",
    "investment_thesis": "investment_thesis",
}

# Role -> strict element type
ROLE_TO_ELEMENT_TYPE: dict[str, str] = {
    "title": "heading",
    "subtitle": "subheading",
    "body": "body_text",
    "left_header": "heading",
    "right_header": "heading",
    "left_body": "body_text",
    "right_body": "body_text",
    "attribution": "footnote",
}


# ---------------------------------------------------------------------------
# Chart-data normalization
# ---------------------------------------------------------------------------

def _normalize_chart_data(chart_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Transform chart data from simplified format to the strict ChartUnion schema."""
    categories = data.get("categories", [])
    series = data.get("series", [])

    if chart_type == "waterfall":
        values = series[0]["values"] if series else []
        return {"chart_type": "waterfall", "categories": categories, "values": values}

    if chart_type == "funnel":
        values = series[0]["values"] if series else []
        return {"chart_type": "funnel", "stages": categories, "values": values}

    if chart_type in ("pie", "donut"):
        values = series[0]["values"] if series else []
        result: dict[str, Any] = {
            "chart_type": chart_type,
            "labels": categories,
            "values": values,
        }
        if chart_type == "donut":
            result["inner_radius"] = 0.5
        return result

    if chart_type == "radar":
        return {"chart_type": "radar", "axes": categories, "series": series}

    if chart_type == "treemap":
        values = series[0]["values"] if series else []
        return {"chart_type": "treemap", "labels": categories, "values": values}

    # Generic category-based (bar, line, area, stacked_bar, ...)
    return {"chart_type": chart_type, "categories": categories, "series": series}


# ---------------------------------------------------------------------------
# Element normalization
# ---------------------------------------------------------------------------

def _is_strict_element(elem: dict[str, Any]) -> bool:
    """Return True if the element already matches the strict schema."""
    etype = elem.get("type", "")
    # Strict elements use types like heading, subheading, body_text,
    # bullet_list, table, chart -- and have "content" or "chart_data".
    if etype in (
        "heading", "subheading", "body_text", "bullet_list", "numbered_list",
        "callout_box", "pull_quote", "footnote", "label",
        "table", "chart",
        "kpi_card", "metric_group", "progress_bar", "gauge", "sparkline",
        "image", "icon", "shape", "divider", "spacer", "logo", "background",
        "container", "column", "row", "grid_cell",
    ):
        # Has "content" dict or "chart_data" dict -> likely already strict
        if "content" in elem or "chart_data" in elem:
            return True
    return False


def _normalize_element(elem: dict[str, Any]) -> dict[str, Any] | None:
    """Normalize a simplified element into the strict IR schema.

    Returns None for unrecognised element types (they are dropped with a warning).
    If the element already matches the strict schema, it is returned as-is.
    """
    # Pass through elements that already look strict
    if _is_strict_element(elem):
        return elem

    elem_type = elem.get("type", "")
    role = elem.get("role", "body")

    if elem_type == "text":
        content_text = elem.get("content", "")
        ir_type = ROLE_TO_ELEMENT_TYPE.get(role, "body_text")

        if ir_type == "heading":
            return {
                "type": "heading",
                "content": {
                    "text": content_text,
                    "level": "h1" if role == "title" else "h2",
                },
            }
        if ir_type == "subheading":
            return {"type": "subheading", "content": {"text": content_text}}
        if ir_type == "footnote":
            return {"type": "footnote", "content": {"text": content_text}}
        return {"type": "body_text", "content": {"text": content_text}}

    if elem_type == "list":
        items = elem.get("items", [])
        return {"type": "bullet_list", "content": {"items": items}}

    if elem_type == "table":
        data = elem.get("data", {})
        return {
            "type": "table",
            "content": {
                "headers": data.get("headers", []),
                "rows": data.get("rows", []),
            },
        }

    if elem_type == "chart":
        chart_type = elem.get("chart_type", "bar")
        data = elem.get("data", {})
        chart_data = _normalize_chart_data(chart_type, data)
        return {"type": "chart", "chart_data": chart_data}

    if elem_type == "timeline":
        items_raw = elem.get("items", [])
        bullet_items: list[str] = []
        for item in items_raw:
            if isinstance(item, dict):
                date = item.get("date", "")
                title = item.get("title", "")
                desc = item.get("description", "")
                bullet_items.append(f"{date}: {title} -- {desc}")
            else:
                bullet_items.append(str(item))
        return {"type": "bullet_list", "content": {"items": bullet_items}}

    logger.warning("normalize: unknown element type %r, dropping", elem_type)
    return None


# ---------------------------------------------------------------------------
# Slide normalization
# ---------------------------------------------------------------------------

def _normalize_slide(slide: dict[str, Any]) -> dict[str, Any]:
    """Normalize a single slide dict (type mapping + element transforms)."""
    raw_type = slide.get("slide_type", "")
    mapped_type = SLIDE_TYPE_MAP.get(raw_type, raw_type)

    result: dict[str, Any] = {
        "slide_type": mapped_type,
        "elements": [],
    }

    # Preserve optional fields
    for key in ("speaker_notes", "layout_hint", "transition", "build_animations"):
        if slide.get(key) is not None:
            result[key] = slide[key]

    # Normalize each element
    for elem in slide.get("elements", []):
        normalized = _normalize_element(elem)
        if normalized is not None:
            result["elements"].append(normalized)

    return result


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def normalize_ir(ir_data: dict[str, Any]) -> dict[str, Any]:
    """Normalize a (possibly simplified) IR dict into the strict Pydantic schema.

    This function is **idempotent**: passing already-strict IR through it
    returns an equivalent dict.  It operates on a deep copy so the caller's
    data is never mutated.

    Args:
        ir_data: Raw IR dict (simplified or strict).

    Returns:
        A dict that can be passed to ``Presentation.model_validate()``.
    """
    data = copy.deepcopy(ir_data)

    result: dict[str, Any] = {
        "schema_version": data.get("schema_version", "1.0"),
        "metadata": data.get("metadata", {}),
        "theme": data.get("theme", "executive-dark"),
        "slides": [],
    }

    if data.get("brand_kit"):
        result["brand_kit"] = data["brand_kit"]
    if data.get("generation_options"):
        result["generation_options"] = data["generation_options"]

    for slide in data.get("slides", []):
        result["slides"].append(_normalize_slide(slide))

    return result
