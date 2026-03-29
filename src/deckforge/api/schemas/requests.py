"""Request body schemas for the DeckForge API."""

from __future__ import annotations

from pydantic import BaseModel, Field

from deckforge.ir.brand_kit import BrandKit
from deckforge.ir.metadata import GenerationOptions
from deckforge.llm.models import LLMConfig


class GenerateRequest(BaseModel):
    """POST /v1/generate request body.

    Accepts a natural language prompt and optional configuration for
    the content generation pipeline.
    """

    prompt: str = Field(min_length=10, max_length=5000)
    generation_options: GenerationOptions | None = None
    theme: str = "executive-dark"
    brand_kit: BrandKit | None = None
    llm_config: LLMConfig | None = None
    webhook_url: str | None = None
