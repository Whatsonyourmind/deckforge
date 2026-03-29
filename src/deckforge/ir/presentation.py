"""Top-level Presentation model composing slides, metadata, brand_kit."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from deckforge.ir.brand_kit import BrandKit
from deckforge.ir.metadata import GenerationOptions, PresentationMetadata
from deckforge.ir.slides import SlideUnion


class Presentation(BaseModel):
    """The complete IR for a DeckForge presentation."""

    model_config = ConfigDict(json_schema_extra={"title": "DeckForge Presentation IR"})

    schema_version: Literal["1.0"] = "1.0"
    metadata: PresentationMetadata
    brand_kit: BrandKit | None = None
    theme: str = "executive-dark"
    slides: list[SlideUnion]
    generation_options: GenerationOptions | None = None

    @model_validator(mode="after")
    def validate_slides_not_empty(self) -> Presentation:
        if not self.slides:
            raise ValueError("Presentation must have at least one slide")
        return self
