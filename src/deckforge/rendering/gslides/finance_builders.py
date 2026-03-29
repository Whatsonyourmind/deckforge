"""Finance slide type batchUpdate request builders for Google Slides API.

Translates the 9 finance-specific slide types from IR into Slides API
batchUpdate request lists. Mirrors the PPTX finance slide renderers
but targets JSON request format instead of python-pptx objects.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deckforge.rendering.gslides.converter import (
    generate_object_id,
    make_color,
    make_element_properties,
    pt_to_slides_font_size,
)

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# The 9 finance slide types
FINANCE_SLIDE_TYPES = {
    "comp_table",
    "dcf_summary",
    "waterfall_chart",
    "deal_overview",
    "returns_analysis",
    "capital_structure",
    "market_landscape",
    "investment_thesis",
    "risk_matrix",
}


def _build_title_requests(
    page_id: str,
    title: str,
    theme: ResolvedTheme,
    x: float = 0.5,
    y: float = 0.3,
    w: float = 12.0,
    h: float = 0.8,
) -> list[dict]:
    """Build title text requests for a finance slide."""
    obj_id = generate_object_id()
    return [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": make_element_properties(page_id, x, y, w, h),
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "text": title,
                "insertionIndex": 0,
            }
        },
        {
            "updateTextStyle": {
                "objectId": obj_id,
                "textRange": {"type": "ALL"},
                "style": {
                    "fontFamily": theme.typography.heading_family,
                    "fontSize": pt_to_slides_font_size(
                        theme.typography.scale.get("h2", 36)
                    ),
                    "bold": True,
                    "foregroundColor": make_color(theme.colors.text_primary),
                },
                "fields": "fontFamily,fontSize,bold,foregroundColor",
            }
        },
    ]


def _build_finance_table(
    page_id: str,
    headers: list[str],
    rows: list[list[str]],
    theme: ResolvedTheme,
    x: float = 0.5,
    y: float = 1.5,
    w: float = 12.0,
    h: float = 5.0,
    header_color: str | None = None,
) -> list[dict]:
    """Build a table with styled header for finance slides."""
    num_cols = len(headers) if headers else 1
    num_rows = 1 + len(rows)  # header + data

    obj_id = generate_object_id()
    bg_color = header_color or theme.colors.primary

    requests: list[dict] = [
        {
            "createTable": {
                "objectId": obj_id,
                "rows": num_rows,
                "columns": num_cols,
                "elementProperties": make_element_properties(page_id, x, y, w, h),
            }
        }
    ]

    # Insert headers
    for col_idx, header in enumerate(headers):
        requests.append(
            {
                "insertText": {
                    "objectId": obj_id,
                    "cellLocation": {"rowIndex": 0, "columnIndex": col_idx},
                    "text": str(header),
                    "insertionIndex": 0,
                }
            }
        )

    # Style header row
    for col_idx in range(num_cols):
        requests.append(
            {
                "updateTableCellProperties": {
                    "objectId": obj_id,
                    "tableRange": {
                        "location": {"rowIndex": 0, "columnIndex": col_idx},
                        "rowSpan": 1,
                        "columnSpan": 1,
                    },
                    "tableCellProperties": {
                        "tableCellBackgroundFill": {
                            "solidFill": {"color": make_color(bg_color)}
                        }
                    },
                    "fields": "tableCellBackgroundFill",
                }
            }
        )

    # Insert data rows
    for row_idx, row in enumerate(rows):
        for col_idx, cell in enumerate(row):
            requests.append(
                {
                    "insertText": {
                        "objectId": obj_id,
                        "cellLocation": {
                            "rowIndex": 1 + row_idx,
                            "columnIndex": col_idx,
                        },
                        "text": str(cell),
                        "insertionIndex": 0,
                    }
                }
            )

    return requests


def _build_colored_rect(
    page_id: str,
    hex_color: str,
    x: float,
    y: float,
    w: float,
    h: float,
    label: str = "",
    theme: ResolvedTheme | None = None,
) -> list[dict]:
    """Build a colored rectangle with optional label text."""
    rect_id = generate_object_id()
    requests: list[dict] = [
        {
            "createShape": {
                "objectId": rect_id,
                "shapeType": "RECTANGLE",
                "elementProperties": make_element_properties(page_id, x, y, w, h),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": rect_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {"color": make_color(hex_color)}
                    }
                },
                "fields": "shapeBackgroundFill",
            }
        },
    ]

    if label:
        requests.extend([
            {
                "insertText": {
                    "objectId": rect_id,
                    "text": label,
                    "insertionIndex": 0,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": rect_id,
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": (theme.typography.body_family if theme else "Arial"),
                        "fontSize": pt_to_slides_font_size(12),
                        "foregroundColor": make_color("#FFFFFF"),
                    },
                    "fields": "fontFamily,fontSize,foregroundColor",
                }
            },
        ])

    return requests


def _build_comp_table(page_id: str, ir_slide: Any, theme: ResolvedTheme) -> list[dict]:
    """Build comparable company analysis table slide."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Comparable Company Analysis"), theme
    )

    content = _get_slide_content(ir_slide)
    headers = content.get("headers", ["Company", "EV/EBITDA", "P/E", "Revenue Growth"])
    rows = content.get("rows", [])

    requests.extend(_build_finance_table(page_id, headers, rows, theme))
    return requests


def _build_dcf_summary(page_id: str, ir_slide: Any, theme: ResolvedTheme) -> list[dict]:
    """Build DCF summary slide with assumptions and sensitivity table."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "DCF Summary"), theme
    )

    content = _get_slide_content(ir_slide)

    # Assumptions table
    assumptions = content.get("assumptions", {})
    if assumptions:
        assumption_headers = ["Parameter", "Value"]
        assumption_rows = [[k, str(v)] for k, v in assumptions.items()]
        requests.extend(
            _build_finance_table(
                page_id, assumption_headers, assumption_rows, theme,
                x=0.5, y=1.5, w=5.5, h=3.0
            )
        )

    # Sensitivity matrix
    sensitivity = content.get("sensitivity", {})
    if sensitivity:
        s_headers = sensitivity.get("headers", [])
        s_rows = sensitivity.get("rows", [])
        requests.extend(
            _build_finance_table(
                page_id, s_headers, s_rows, theme,
                x=6.5, y=1.5, w=6.0, h=3.0, header_color=theme.colors.secondary
            )
        )

    return requests


def _build_waterfall_chart(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build waterfall chart slide.

    Creates a placeholder image. Static chart rendering via Plotly
    and S3 upload would be done at render time if available.
    """
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Waterfall Analysis"), theme
    )

    # Placeholder for the chart image area
    requests.extend(
        _build_colored_rect(
            page_id, theme.colors.surface, 0.5, 1.5, 12.0, 5.0,
            label="Waterfall Chart", theme=theme
        )
    )

    return requests


def _build_deal_overview(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build deal overview slide with metrics and indicators."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Deal Overview"), theme
    )

    content = _get_slide_content(ir_slide)
    metrics = content.get("metrics", {})

    # Metrics as KPI cards arranged horizontally
    x_pos = 0.5
    card_width = 3.8
    for i, (label, value) in enumerate(list(metrics.items())[:3]):
        card_x = x_pos + i * (card_width + 0.3)
        obj_id = generate_object_id()
        text_id = generate_object_id()

        requests.extend([
            {
                "createShape": {
                    "objectId": obj_id,
                    "shapeType": "ROUND_RECTANGLE",
                    "elementProperties": make_element_properties(
                        page_id, card_x, 1.5, card_width, 2.0
                    ),
                }
            },
            {
                "updateShapeProperties": {
                    "objectId": obj_id,
                    "shapeProperties": {
                        "shapeBackgroundFill": {
                            "solidFill": {"color": make_color(theme.colors.surface)}
                        }
                    },
                    "fields": "shapeBackgroundFill",
                }
            },
            {
                "createShape": {
                    "objectId": text_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": make_element_properties(
                        page_id, card_x + 0.2, 1.7, card_width - 0.4, 1.6
                    ),
                }
            },
            {
                "insertText": {
                    "objectId": text_id,
                    "text": f"{value}\n{label}",
                    "insertionIndex": 0,
                }
            },
        ])

    return requests


def _build_returns_analysis(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build returns analysis slide with IRR/MOIC table."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Returns Analysis"), theme
    )

    content = _get_slide_content(ir_slide)
    headers = content.get("headers", ["Scenario", "IRR", "MOIC", "Exit Year"])
    rows = content.get("rows", [])

    requests.extend(_build_finance_table(page_id, headers, rows, theme))
    return requests


def _build_capital_structure(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build capital structure slide with sources/uses tables and debt stack."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Capital Structure"), theme
    )

    content = _get_slide_content(ir_slide)

    # Sources table
    sources = content.get("sources", [])
    if sources:
        s_headers = ["Source", "Amount", "% Total"]
        requests.extend(
            _build_finance_table(
                page_id, s_headers, sources, theme,
                x=0.5, y=1.5, w=5.5, h=3.0
            )
        )

    # Uses table
    uses = content.get("uses", [])
    if uses:
        u_headers = ["Use", "Amount", "% Total"]
        requests.extend(
            _build_finance_table(
                page_id, u_headers, uses, theme,
                x=6.5, y=1.5, w=6.0, h=3.0, header_color=theme.colors.secondary
            )
        )

    # Debt stack colored rectangles
    debt_stack = content.get("debt_stack", [])
    chart_colors = getattr(theme, "chart_colors", []) or [
        theme.colors.primary, theme.colors.secondary, theme.colors.accent
    ]
    y_offset = 5.0
    for i, layer in enumerate(debt_stack[:5]):
        layer_name = layer if isinstance(layer, str) else layer.get("name", f"Tranche {i+1}")
        color = chart_colors[i % len(chart_colors)]
        requests.extend(
            _build_colored_rect(
                page_id, color, 0.5, y_offset + i * 0.5, 12.0, 0.45,
                label=layer_name, theme=theme
            )
        )

    return requests


def _build_market_landscape(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build market landscape slide with TAM/SAM/SOM and positioning table."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Market Landscape"), theme
    )

    content = _get_slide_content(ir_slide)

    # TAM/SAM/SOM as nested rounded rectangles
    tam = content.get("tam", "TAM")
    sam = content.get("sam", "SAM")
    som = content.get("som", "SOM")

    # Outer (TAM)
    requests.extend(
        _build_colored_rect(
            page_id, theme.colors.primary + "40" if len(theme.colors.primary) == 7
            else theme.colors.primary,
            0.5, 1.5, 6.0, 5.0, label=f"TAM: {tam}", theme=theme
        )
    )
    # Middle (SAM)
    requests.extend(
        _build_colored_rect(
            page_id, theme.colors.primary + "80" if len(theme.colors.primary) == 7
            else theme.colors.primary,
            1.5, 2.2, 4.0, 3.5, label=f"SAM: {sam}", theme=theme
        )
    )
    # Inner (SOM)
    requests.extend(
        _build_colored_rect(
            page_id, theme.colors.primary,
            2.5, 3.0, 2.0, 2.0, label=f"SOM: {som}", theme=theme
        )
    )

    # Competitive positioning table
    comp = content.get("competitors", [])
    if comp:
        comp_headers = ["Competitor", "Position", "Share"]
        requests.extend(
            _build_finance_table(
                page_id, comp_headers, comp, theme,
                x=7.0, y=1.5, w=5.5, h=5.0
            )
        )

    return requests


def _build_investment_thesis(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build investment thesis slide with numbered thesis points."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Investment Thesis"), theme
    )

    content = _get_slide_content(ir_slide)
    thesis_points = content.get("thesis_points", [])

    # Numbered thesis shapes
    for i, point in enumerate(thesis_points[:6]):
        point_text = point if isinstance(point, str) else point.get("text", "")
        obj_id = generate_object_id()
        requests.extend([
            {
                "createShape": {
                    "objectId": obj_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": make_element_properties(
                        page_id, 0.5, 1.5 + i * 0.9, 12.0, 0.8
                    ),
                }
            },
            {
                "insertText": {
                    "objectId": obj_id,
                    "text": f"{i + 1}. {point_text}",
                    "insertionIndex": 0,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": obj_id,
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": theme.typography.body_family,
                        "fontSize": pt_to_slides_font_size(
                            theme.typography.scale.get("body", 18)
                        ),
                        "foregroundColor": make_color(theme.colors.text_primary),
                    },
                    "fields": "fontFamily,fontSize,foregroundColor",
                }
            },
        ])

    # Risk/reward table
    risks = content.get("risks", [])
    if risks:
        risk_headers = ["Risk", "Mitigation", "Impact"]
        requests.extend(
            _build_finance_table(
                page_id, risk_headers, risks, theme,
                x=0.5, y=5.5, w=12.0, h=1.5, header_color=theme.colors.negative
            )
        )

    return requests


def _build_risk_matrix(
    page_id: str, ir_slide: Any, theme: ResolvedTheme
) -> list[dict]:
    """Build risk matrix slide with 5x5 colored grid."""
    requests = _build_title_requests(
        page_id, _get_title(ir_slide, "Risk Matrix"), theme
    )

    content = _get_slide_content(ir_slide)
    risks = content.get("risks", [])

    # 5x5 heatmap grid colors (green -> yellow -> red)
    heatmap = [
        ["#34A853", "#34A853", "#FBBC04", "#FBBC04", "#EA4335"],
        ["#34A853", "#FBBC04", "#FBBC04", "#EA4335", "#EA4335"],
        ["#FBBC04", "#FBBC04", "#EA4335", "#EA4335", "#EA4335"],
        ["#FBBC04", "#EA4335", "#EA4335", "#EA4335", "#B71C1C"],
        ["#EA4335", "#EA4335", "#EA4335", "#B71C1C", "#B71C1C"],
    ]

    cell_size = 1.0
    grid_x = 2.0
    grid_y = 1.5

    for row in range(5):
        for col in range(5):
            color = heatmap[row][col]
            requests.extend(
                _build_colored_rect(
                    page_id, color,
                    grid_x + col * (cell_size + 0.05),
                    grid_y + row * (cell_size + 0.05),
                    cell_size, cell_size,
                    theme=theme,
                )
            )

    # Place risk labels if provided
    for risk in risks[:10]:
        risk_name = risk if isinstance(risk, str) else risk.get("name", "")
        impact = risk.get("impact", 3) if isinstance(risk, dict) else 3
        likelihood = risk.get("likelihood", 3) if isinstance(risk, dict) else 3
        # Clamp to 1-5
        col_idx = max(0, min(4, likelihood - 1))
        row_idx = max(0, min(4, 5 - impact))

        label_id = generate_object_id()
        requests.extend([
            {
                "createShape": {
                    "objectId": label_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": make_element_properties(
                        page_id,
                        grid_x + col_idx * (cell_size + 0.05) + 0.05,
                        grid_y + row_idx * (cell_size + 0.05) + 0.3,
                        cell_size - 0.1,
                        0.4,
                    ),
                }
            },
            {
                "insertText": {
                    "objectId": label_id,
                    "text": risk_name,
                    "insertionIndex": 0,
                }
            },
        ])

    return requests


def _get_title(ir_slide: Any, default: str) -> str:
    """Extract slide title from IR slide."""
    # Try common title locations
    for attr in ("title", "heading"):
        val = getattr(ir_slide, attr, None)
        if val:
            return str(val)

    # Check elements for a heading
    elements = getattr(ir_slide, "elements", [])
    for el in elements:
        el_type = el.type if hasattr(el, "type") else ""
        if hasattr(el_type, "value"):
            el_type = el_type.value
        if el_type == "heading":
            content = el.content if isinstance(el.content, dict) else {}
            return content.get("text", default)

    return default


def _get_slide_content(ir_slide: Any) -> dict:
    """Extract content dict from IR slide, handling various formats."""
    if hasattr(ir_slide, "content") and isinstance(ir_slide.content, dict):
        return ir_slide.content

    # Fallback: try to build from elements
    elements = getattr(ir_slide, "elements", [])
    if elements:
        for el in elements:
            content = getattr(el, "content", None)
            if isinstance(content, dict) and ("headers" in content or "rows" in content):
                return content

    return {}


def build_finance_slide_requests(
    page_id: str,
    ir_slide: Any,
    theme: ResolvedTheme,
) -> list[dict] | None:
    """Build batchUpdate requests for a finance slide type.

    Args:
        page_id: Slide page object ID.
        ir_slide: IR slide model.
        theme: Resolved theme.

    Returns:
        List of request dicts if this is a finance slide type, None otherwise.
    """
    slide_type = ir_slide.slide_type
    if hasattr(slide_type, "value"):
        slide_type = slide_type.value

    if slide_type not in FINANCE_SLIDE_TYPES:
        return None

    builders = {
        "comp_table": _build_comp_table,
        "dcf_summary": _build_dcf_summary,
        "waterfall_chart": _build_waterfall_chart,
        "deal_overview": _build_deal_overview,
        "returns_analysis": _build_returns_analysis,
        "capital_structure": _build_capital_structure,
        "market_landscape": _build_market_landscape,
        "investment_thesis": _build_investment_thesis,
        "risk_matrix": _build_risk_matrix,
    }

    builder = builders.get(slide_type)
    if builder is None:
        logger.warning("No GSlides finance builder for: %s", slide_type)
        return None

    return builder(page_id, ir_slide, theme)
