"""High-level request builder for Google Slides API.

Orchestrates slide creation, background setting, speaker notes,
and element dispatch for a single slide.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deckforge.rendering.gslides.converter import (
    generate_object_id,
    make_color,
)
from deckforge.rendering.gslides.element_builders import dispatch_element_requests
from deckforge.rendering.gslides.finance_builders import build_finance_slide_requests

if TYPE_CHECKING:
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)


class SlideRequestBuilder:
    """Builds Slides API batchUpdate requests for a single slide.

    Each instance handles one slide: creation, background, elements, and notes.
    """

    def __init__(self, slide_id: str, page_id: str) -> None:
        """Initialize the builder.

        Args:
            slide_id: Internal tracking ID for the slide.
            page_id: Object ID for the Google Slides page.
        """
        self.slide_id = slide_id
        self.page_id = page_id

    def build_create_slide(self, insertion_index: int) -> dict:
        """Build a CreateSlideRequest.

        Args:
            insertion_index: Zero-based position to insert the slide.

        Returns:
            CreateSlide request dict.
        """
        return {
            "createSlide": {
                "objectId": self.page_id,
                "insertionIndex": insertion_index,
                "slideLayoutReference": {
                    "predefinedLayout": "BLANK",
                },
            }
        }

    def build_background(self, hex_color: str) -> dict:
        """Build an UpdatePagePropertiesRequest to set slide background.

        Args:
            hex_color: Background color as hex string.

        Returns:
            UpdatePageProperties request dict.
        """
        return {
            "updatePageProperties": {
                "objectId": self.page_id,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {
                            "color": make_color(hex_color),
                        }
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color",
            }
        }

    def build_delete_placeholders(self, placeholder_ids: list[str]) -> list[dict]:
        """Build DeleteObjectRequests for placeholder elements.

        Args:
            placeholder_ids: Object IDs to delete.

        Returns:
            List of DeleteObject request dicts.
        """
        return [
            {"deleteObject": {"objectId": pid}}
            for pid in placeholder_ids
        ]

    def build_speaker_notes(self, notes_text: str) -> list[dict]:
        """Build requests to add speaker notes to a slide.

        Creates a text element on the notes page.

        Args:
            notes_text: Speaker notes content.

        Returns:
            List of request dicts for notes.
        """
        if not notes_text:
            return []

        # Speaker notes require inserting text into the notes page shape
        # The notes shape objectId is typically "{page_id}_notes"
        notes_id = generate_object_id()

        return [
            {
                "createShape": {
                    "objectId": notes_id,
                    "shapeType": "TEXT_BOX",
                    "elementProperties": {
                        "pageObjectId": f"{self.page_id}_notes",
                        "size": {
                            "width": {"magnitude": 8229600, "unit": "EMU"},
                            "height": {"magnitude": 4572000, "unit": "EMU"},
                        },
                        "transform": {
                            "scaleX": 1,
                            "scaleY": 1,
                            "shearX": 0,
                            "shearY": 0,
                            "translateX": 457200,
                            "translateY": 457200,
                            "unit": "EMU",
                        },
                    },
                }
            },
            {
                "insertText": {
                    "objectId": notes_id,
                    "text": notes_text,
                    "insertionIndex": 0,
                }
            },
        ]

    def dispatch_element(
        self,
        element: Any,
        position: Any,
        theme: ResolvedTheme,
        charts_builder: Any = None,
    ) -> list[dict]:
        """Dispatch an element to the appropriate builder.

        Args:
            element: IR element model.
            position: ResolvedPosition with x, y, width, height.
            theme: Resolved theme.
            charts_builder: Optional SheetsChartBuilder for chart elements.

        Returns:
            List of request dicts for this element.
        """
        return dispatch_element_requests(
            self.page_id, element, position, theme, charts_builder
        )

    def dispatch_finance_slide(
        self,
        ir_slide: Any,
        theme: ResolvedTheme,
    ) -> list[dict]:
        """Dispatch a finance slide type to the finance builders.

        Args:
            ir_slide: IR slide model with slide_type.
            theme: Resolved theme.

        Returns:
            List of request dicts, or empty list if not a finance type.
        """
        result = build_finance_slide_requests(self.page_id, ir_slide, theme)
        return result if result is not None else []
