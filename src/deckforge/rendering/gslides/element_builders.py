"""Per-element-type batchUpdate request builders for Google Slides API.

Each builder function creates a list of Slides API request dicts for a
specific element type. The list typically includes CreateShape/CreateTable/
CreateImage requests followed by InsertText and UpdateTextStyle requests.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deckforge.rendering.gslides.converter import (
    generate_object_id,
    hex_to_slides_rgb,
    inches_to_emu,
    is_bold_weight,
    make_color,
    make_element_properties,
    pt_to_slides_font_size,
)

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Mapping from element type to typography scale key and weight key
_TYPE_TYPOGRAPHY_MAP: dict[str, tuple[str, str]] = {
    "heading": ("h1", "heading"),
    "subheading": ("h2", "subtitle"),
    "body_text": ("body", "body"),
    "footnote": ("footnote", "caption"),
    "label": ("caption", "caption"),
}


def _get_text_content(element: Any) -> str:
    """Extract text content from element, handling dict or attribute access."""
    content = element.content
    if isinstance(content, dict):
        return content.get("text", "")
    return getattr(content, "text", str(content)) if content else ""


def _get_list_items(element: Any) -> list[str]:
    """Extract list items from element content."""
    content = element.content
    if isinstance(content, dict):
        return content.get("items", [])
    return getattr(content, "items", []) if content else []


def _get_font_family(element_type: str, theme: ResolvedTheme) -> str:
    """Get font family for element type from theme."""
    if element_type in ("heading", "subheading"):
        return theme.typography.heading_family
    return theme.typography.body_family


def _get_font_size_pt(element_type: str, theme: ResolvedTheme) -> int:
    """Get font size in points for element type from theme."""
    scale_key = _TYPE_TYPOGRAPHY_MAP.get(element_type, ("body", "body"))[0]
    return theme.typography.scale.get(scale_key, 18)


def _get_font_weight(element_type: str, theme: ResolvedTheme) -> int:
    """Get font weight for element type from theme."""
    weight_key = _TYPE_TYPOGRAPHY_MAP.get(element_type, ("body", "body"))[1]
    return theme.typography.weights.get(weight_key, 400)


def _get_text_color(element_type: str, theme: ResolvedTheme) -> str:
    """Get text color hex for element type from theme."""
    if element_type in ("footnote", "label"):
        return theme.colors.text_muted
    if element_type == "subheading":
        return theme.colors.text_secondary
    return theme.colors.text_primary


def _build_text_style_request(
    object_id: str,
    text: str,
    element_type: str,
    theme: ResolvedTheme,
) -> dict:
    """Build UpdateTextStyleRequest for styled text."""
    font_family = _get_font_family(element_type, theme)
    font_size = _get_font_size_pt(element_type, theme)
    font_weight = _get_font_weight(element_type, theme)
    color = _get_text_color(element_type, theme)

    return {
        "updateTextStyle": {
            "objectId": object_id,
            "textRange": {"type": "ALL"},
            "style": {
                "fontFamily": font_family,
                "fontSize": pt_to_slides_font_size(font_size),
                "bold": is_bold_weight(font_weight),
                "foregroundColor": make_color(color),
            },
            "fields": "fontFamily,fontSize,bold,foregroundColor",
        }
    }


def build_text_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for text elements (heading, subheading, body_text, footnote, label).

    Creates a TEXT_BOX shape, inserts text, and applies text styling.
    """
    text = _get_text_content(element)
    if not text:
        return []

    element_type = element.type
    if hasattr(element_type, "value"):
        element_type = element_type.value

    obj_id = generate_object_id()

    requests = [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "text": text,
                "insertionIndex": 0,
            }
        },
        _build_text_style_request(obj_id, text, element_type, theme),
    ]

    return requests


def build_bullet_list_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for bullet list elements.

    Creates a TEXT_BOX, inserts each bullet on a new line,
    then applies CreateParagraphBulletsRequest.
    """
    items = _get_list_items(element)
    if not items:
        return []

    obj_id = generate_object_id()
    text = "\n".join(items)

    requests = [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "text": text,
                "insertionIndex": 0,
            }
        },
        _build_text_style_request(obj_id, text, "body_text", theme),
        {
            "createParagraphBullets": {
                "objectId": obj_id,
                "textRange": {"type": "ALL"},
                "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
            }
        },
    ]

    return requests


def build_numbered_list_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for numbered list elements.

    Same as bullet list but with NUMBERED preset.
    """
    items = _get_list_items(element)
    if not items:
        return []

    obj_id = generate_object_id()
    text = "\n".join(items)

    requests = [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "text": text,
                "insertionIndex": 0,
            }
        },
        _build_text_style_request(obj_id, text, "body_text", theme),
        {
            "createParagraphBullets": {
                "objectId": obj_id,
                "textRange": {"type": "ALL"},
                "bulletPreset": "NUMBERED_DECIMAL_ALPHA_ROMAN",
            }
        },
    ]

    return requests


def build_table_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for table elements.

    Creates a table, inserts text in each cell, styles the header row.
    """
    content = element.content if isinstance(element.content, dict) else {}
    headers = content.get("headers", [])
    rows = content.get("rows", [])

    if not headers and not rows:
        return []

    num_cols = len(headers) if headers else (len(rows[0]) if rows else 1)
    num_rows = (1 if headers else 0) + len(rows)

    obj_id = generate_object_id()

    requests: list[dict] = [
        {
            "createTable": {
                "objectId": obj_id,
                "rows": num_rows,
                "columns": num_cols,
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        }
    ]

    # Insert header text
    if headers:
        for col_idx, header_text in enumerate(headers):
            requests.append(
                {
                    "insertText": {
                        "objectId": obj_id,
                        "cellLocation": {
                            "rowIndex": 0,
                            "columnIndex": col_idx,
                        },
                        "text": str(header_text),
                        "insertionIndex": 0,
                    }
                }
            )

        # Style header row background
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
                                "solidFill": {"color": make_color(theme.colors.primary)}
                            }
                        },
                        "fields": "tableCellBackgroundFill",
                    }
                }
            )

    # Insert data rows
    row_offset = 1 if headers else 0
    for row_idx, row in enumerate(rows):
        for col_idx, cell_text in enumerate(row):
            requests.append(
                {
                    "insertText": {
                        "objectId": obj_id,
                        "cellLocation": {
                            "rowIndex": row_offset + row_idx,
                            "columnIndex": col_idx,
                        },
                        "text": str(cell_text),
                        "insertionIndex": 0,
                    }
                }
            )

    return requests


def build_image_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for image elements.

    Creates an image from a URL with the specified positioning.
    """
    content = element.content if isinstance(element.content, dict) else {}
    url = content.get("url", "")
    if not url:
        return []

    obj_id = generate_object_id()

    return [
        {
            "createImage": {
                "objectId": obj_id,
                "url": url,
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        }
    ]


def build_shape_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for generic shape elements.

    Creates a RECTANGLE shape with fill color from theme.
    """
    obj_id = generate_object_id()

    requests = [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "RECTANGLE",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
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
    ]

    return requests


def build_divider_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for divider elements.

    Creates a STRAIGHT_LINE across the element's width.
    """
    obj_id = generate_object_id()

    return [
        {
            "createLine": {
                "objectId": obj_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, 0
                ),
            }
        },
        {
            "updateLineProperties": {
                "objectId": obj_id,
                "lineProperties": {
                    "lineFill": {
                        "solidFill": {"color": make_color(theme.colors.text_muted)}
                    },
                    "weight": {"magnitude": 1, "unit": "PT"},
                },
                "fields": "lineFill,weight",
            }
        },
    ]


def build_kpi_card_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for KPI card elements.

    Creates a container shape with a large value text and label text.
    """
    content = element.content if isinstance(element.content, dict) else {}
    value = content.get("value", "")
    label = content.get("label", "")
    change = content.get("change", "")

    obj_id_bg = generate_object_id()
    obj_id_value = generate_object_id()
    obj_id_label = generate_object_id()

    requests: list[dict] = [
        # Background shape
        {
            "createShape": {
                "objectId": obj_id_bg,
                "shapeType": "ROUND_RECTANGLE",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": obj_id_bg,
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {"color": make_color(theme.colors.surface)}
                    }
                },
                "fields": "shapeBackgroundFill",
            }
        },
    ]

    # Value text (large)
    value_height = position.height * 0.5
    if value:
        requests.extend([
            {
                "createShape": {
                    "objectId": obj_id_value,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": make_element_properties(
                        page_id,
                        position.x + 0.1,
                        position.y + 0.1,
                        position.width - 0.2,
                        value_height,
                    ),
                }
            },
            {
                "insertText": {
                    "objectId": obj_id_value,
                    "text": f"{value} {change}".strip() if change else value,
                    "insertionIndex": 0,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": obj_id_value,
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
        ])

    # Label text
    if label:
        requests.extend([
            {
                "createShape": {
                    "objectId": obj_id_label,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": make_element_properties(
                        page_id,
                        position.x + 0.1,
                        position.y + value_height + 0.15,
                        position.width - 0.2,
                        position.height - value_height - 0.2,
                    ),
                }
            },
            {
                "insertText": {
                    "objectId": obj_id_label,
                    "text": label,
                    "insertionIndex": 0,
                }
            },
            {
                "updateTextStyle": {
                    "objectId": obj_id_label,
                    "textRange": {"type": "ALL"},
                    "style": {
                        "fontFamily": theme.typography.body_family,
                        "fontSize": pt_to_slides_font_size(
                            theme.typography.scale.get("caption", 14)
                        ),
                        "foregroundColor": make_color(theme.colors.text_secondary),
                    },
                    "fields": "fontFamily,fontSize,foregroundColor",
                }
            },
        ])

    return requests


def build_callout_box_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for callout box elements.

    Creates a ROUND_RECTANGLE with accent background and text inside.
    """
    text = _get_text_content(element)
    if not text:
        return []

    obj_id = generate_object_id()

    return [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "ROUND_RECTANGLE",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": obj_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {"color": make_color(theme.colors.accent)}
                    }
                },
                "fields": "shapeBackgroundFill",
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "text": text,
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
                    "foregroundColor": make_color("#FFFFFF"),
                },
                "fields": "fontFamily,fontSize,foregroundColor",
            }
        },
    ]


def build_pull_quote_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for pull quote elements.

    Creates italic text with optional attribution line.
    """
    content = element.content if isinstance(element.content, dict) else {}
    quote_text = content.get("text", "")
    attribution = content.get("attribution", "")

    if not quote_text:
        return []

    obj_id = generate_object_id()
    full_text = f'"{quote_text}"'
    if attribution:
        full_text += f"\n-- {attribution}"

    return [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "insertText": {
                "objectId": obj_id,
                "text": full_text,
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
                        theme.typography.scale.get("h3", 28)
                    ),
                    "italic": True,
                    "foregroundColor": make_color(theme.colors.text_primary),
                },
                "fields": "fontFamily,fontSize,italic,foregroundColor",
            }
        },
    ]


def build_progress_bar_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for progress bar / gauge elements.

    Creates two overlapping rectangles: background track + fill.
    """
    content = element.content if isinstance(element.content, dict) else {}
    value = content.get("value", 0)
    max_value = content.get("max", 100)
    pct = min(value / max_value, 1.0) if max_value > 0 else 0

    bg_id = generate_object_id()
    fill_id = generate_object_id()

    fill_width = max(position.width * pct, 0.05)

    return [
        # Background track
        {
            "createShape": {
                "objectId": bg_id,
                "shapeType": "RECTANGLE",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": bg_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {"color": make_color(theme.colors.surface)}
                    }
                },
                "fields": "shapeBackgroundFill",
            }
        },
        # Fill bar
        {
            "createShape": {
                "objectId": fill_id,
                "shapeType": "RECTANGLE",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, fill_width, position.height
                ),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": fill_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {
                        "solidFill": {"color": make_color(theme.colors.primary)}
                    }
                },
                "fields": "shapeBackgroundFill",
            }
        },
    ]


def build_metric_group_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build requests for metric group elements.

    Arranges multiple KPI cards horizontally within the element's bounds.
    """
    content = element.content if isinstance(element.content, dict) else {}
    metrics = content.get("metrics", [])
    if not metrics:
        return []

    num_metrics = len(metrics)
    card_width = position.width / num_metrics if num_metrics > 0 else position.width
    gap = 0.1

    all_requests: list[dict] = []
    for i, metric in enumerate(metrics):
        # Create a mock element for build_kpi_card_requests
        class _MetricElement:
            type = "kpi_card"
            content = metric
            style_overrides = None

        class _MetricPos:
            x = position.x + i * card_width + (gap if i > 0 else 0)
            y = position.y
            width = card_width - gap
            height = position.height

        all_requests.extend(
            build_kpi_card_requests(page_id, _MetricElement(), _MetricPos(), theme)
        )

    return all_requests


def build_chart_placeholder_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
) -> list[dict]:
    """Build placeholder requests for chart elements.

    Creates a rectangle with 'Chart' label. Will be replaced by
    Sheets-backed charts in Plan 06-02.
    """
    bg_id = generate_object_id()
    text_id = generate_object_id()

    return [
        {
            "createShape": {
                "objectId": bg_id,
                "shapeType": "RECTANGLE",
                "elementProperties": make_element_properties(
                    page_id, position.x, position.y, position.width, position.height
                ),
            }
        },
        {
            "updateShapeProperties": {
                "objectId": bg_id,
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
                    page_id,
                    position.x + position.width * 0.3,
                    position.y + position.height * 0.4,
                    position.width * 0.4,
                    position.height * 0.2,
                ),
            }
        },
        {
            "insertText": {
                "objectId": text_id,
                "text": "Chart",
                "insertionIndex": 0,
            }
        },
        {
            "updateTextStyle": {
                "objectId": text_id,
                "textRange": {"type": "ALL"},
                "style": {
                    "fontFamily": theme.typography.body_family,
                    "fontSize": pt_to_slides_font_size(
                        theme.typography.scale.get("body", 18)
                    ),
                    "foregroundColor": make_color(theme.colors.text_muted),
                },
                "fields": "fontFamily,fontSize,foregroundColor",
            }
        },
    ]


# ── Element type -> builder dispatch table ──────────────────────────────────

ELEMENT_BUILDERS: dict[str, Any] = {
    # Text
    "heading": build_text_requests,
    "subheading": build_text_requests,
    "body_text": build_text_requests,
    "footnote": build_text_requests,
    "label": build_text_requests,
    # Lists
    "bullet_list": build_bullet_list_requests,
    "numbered_list": build_numbered_list_requests,
    # Data
    "table": build_table_requests,
    "chart": build_chart_placeholder_requests,
    "kpi_card": build_kpi_card_requests,
    "metric_group": build_metric_group_requests,
    "progress_bar": build_progress_bar_requests,
    "gauge": build_progress_bar_requests,  # Gauge rendered as progress bar
    "sparkline": build_chart_placeholder_requests,  # Sparkline as placeholder
    # Visual
    "image": build_image_requests,
    "icon": build_chart_placeholder_requests,  # Icon as placeholder
    "shape": build_shape_requests,
    "divider": build_divider_requests,
    "logo": build_image_requests,  # Logo reuses image builder
    "callout_box": build_callout_box_requests,
    "pull_quote": build_pull_quote_requests,
}

# Structural/no-op element types -- return empty list
_NOOP_TYPES = {"spacer", "background", "container", "column", "row", "grid_cell"}


def dispatch_element_requests(
    page_id: str,
    element: Any,
    position: Any,
    theme: ResolvedTheme,
    charts_builder: Any = None,
) -> list[dict]:
    """Dispatch an element to the appropriate builder function.

    Args:
        page_id: Slide page object ID.
        element: IR element.
        position: ResolvedPosition with x, y, width, height.
        theme: Resolved theme.
        charts_builder: Optional SheetsChartBuilder for chart elements.

    Returns:
        List of Slides API request dicts.
    """
    element_type = element.type
    if hasattr(element_type, "value"):
        element_type = element_type.value

    if element_type in _NOOP_TYPES:
        return []

    # Chart elements can use SheetsChartBuilder if available
    if element_type == "chart" and charts_builder is not None:
        # Plan 06-02 will implement this path
        return build_chart_placeholder_requests(page_id, element, position, theme)

    builder = ELEMENT_BUILDERS.get(element_type)
    if builder is None:
        logger.warning("No GSlides builder for element type: %s", element_type)
        return []

    return builder(page_id, element, position, theme)
