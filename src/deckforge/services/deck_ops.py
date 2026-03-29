"""Deck operation logic — composable mutations on stored IR dicts.

Provides stateless methods to append, replace, reorder, retheme slides
in an IR dictionary, with re-validation via the Presentation model.
"""

from __future__ import annotations

import copy
from typing import Any

from deckforge.ir import Presentation
from deckforge.workers.tasks import render_pipeline


class DeckOperations:
    """Stateless service for mutating Presentation IR dictionaries.

    All methods accept an IR dict, perform the mutation, re-validate
    via Presentation.model_validate(), and return the updated dict.
    """

    def append_slides(
        self,
        ir_dict: dict[str, Any],
        new_slides: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Append slides to the IR and re-validate.

        Args:
            ir_dict: The full Presentation IR as a dictionary.
            new_slides: List of slide dicts to append.

        Returns:
            Updated IR dict with appended slides.

        Raises:
            ValueError: If the resulting IR is invalid.
        """
        result = copy.deepcopy(ir_dict)
        result["slides"].extend(new_slides)
        # Re-validate
        self._validate(result)
        return result

    def replace_slide(
        self,
        ir_dict: dict[str, Any],
        index: int,
        new_slide: dict[str, Any],
    ) -> dict[str, Any]:
        """Replace a slide at the given index and re-validate.

        Args:
            ir_dict: The full Presentation IR as a dictionary.
            index: Zero-based slide index to replace.
            new_slide: The replacement slide dict.

        Returns:
            Updated IR dict with the replaced slide.

        Raises:
            ValueError: If index is out of range or resulting IR is invalid.
        """
        result = copy.deepcopy(ir_dict)
        slides = result["slides"]
        if index < 0 or index >= len(slides):
            raise ValueError(
                f"Slide index {index} out of range (0-{len(slides) - 1})"
            )
        slides[index] = new_slide
        self._validate(result)
        return result

    def reorder_slides(
        self,
        ir_dict: dict[str, Any],
        new_order: list[int],
    ) -> dict[str, Any]:
        """Reorder slides per a new index list and re-validate.

        Args:
            ir_dict: The full Presentation IR as a dictionary.
            new_order: List of slide indices in desired order.
                       Must be a permutation of [0..N-1].

        Returns:
            Updated IR dict with reordered slides.

        Raises:
            ValueError: If indices are invalid (wrong count, duplicates, out of range).
        """
        result = copy.deepcopy(ir_dict)
        slides = result["slides"]
        n = len(slides)

        if len(new_order) != n:
            raise ValueError(
                f"Invalid indices: expected {n} indices, got {len(new_order)}"
            )
        if set(new_order) != set(range(n)):
            raise ValueError(
                f"Invalid indices: must be a permutation of [0..{n - 1}]"
            )

        result["slides"] = [slides[i] for i in new_order]
        self._validate(result)
        return result

    def retheme(
        self,
        ir_dict: dict[str, Any],
        new_theme: str,
    ) -> dict[str, Any]:
        """Change the theme in the IR and re-validate.

        Args:
            ir_dict: The full Presentation IR as a dictionary.
            new_theme: The new theme name string.

        Returns:
            Updated IR dict with the new theme.

        Raises:
            ValueError: If the resulting IR is invalid.
        """
        result = copy.deepcopy(ir_dict)
        result["theme"] = new_theme
        self._validate(result)
        return result

    def re_render(self, ir_dict: dict[str, Any]) -> bytes:
        """Re-render a Presentation IR to PPTX bytes.

        Args:
            ir_dict: The full Presentation IR as a dictionary.

        Returns:
            Raw PPTX bytes.
        """
        presentation = Presentation.model_validate(ir_dict)
        return render_pipeline(presentation)

    @staticmethod
    def _validate(ir_dict: dict[str, Any]) -> None:
        """Validate an IR dict via the Presentation model.

        Raises:
            ValueError: If validation fails (wraps Pydantic ValidationError).
        """
        try:
            Presentation.model_validate(ir_dict)
        except Exception as exc:
            raise ValueError(f"IR validation failed: {exc}") from exc
