"""Cross-field validators for the Presentation model."""

from __future__ import annotations

from typing import Any

from pydantic import model_validator


def validate_slides_not_empty(cls: Any, values: Any) -> Any:
    """Ensure the slides list has at least one slide."""
    if not values.slides:
        raise ValueError("Presentation must have at least one slide")
    return values
