"""Pydantic models for the content generation pipeline.

Defines the data structures flowing between pipeline stages:
ParsedIntent -> PresentationOutline -> ExpandedSlide -> RefinedPresentation.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from deckforge.ir.enums import Audience, Purpose, SlideType, Tone


def _validate_word_count(v: str, max_words: int) -> str:
    """Validate that a string has at most max_words words."""
    word_count = len(v.split())
    if word_count > max_words:
        raise ValueError(
            f"Text has {word_count} words, maximum allowed is {max_words}: '{v}'"
        )
    return v


class ParsedIntent(BaseModel):
    """Structured intent extracted from a natural language prompt."""

    purpose: Purpose
    audience: Audience
    topic: str
    key_messages: list[str] = Field(min_length=3, max_length=7)
    target_slide_count: int = Field(ge=3, le=30)
    tone: Tone
    suggested_slide_types: list[SlideType]
    data_references: list[str] = Field(default_factory=list)


class SlideOutline(BaseModel):
    """Outline for a single slide in the presentation."""

    position: int
    slide_type: SlideType
    headline: str
    key_points: list[str] = Field(min_length=2, max_length=5)
    narrative_role: Literal["opening", "evidence", "transition", "conclusion", "data"]
    data_needs: list[str] | None = None

    @field_validator("headline")
    @classmethod
    def validate_headline_length(cls, v: str) -> str:
        return _validate_word_count(v, 8)


class PresentationOutline(BaseModel):
    """Complete outline for a presentation with narrative structure."""

    title: str
    narrative_arc: Literal["pyramid", "scr", "mece", "chronological"]
    sections: list[str]
    slides: list[SlideOutline]


class ExpandedSlide(BaseModel):
    """A fully expanded slide with IR-compatible elements."""

    slide_type: str
    title: str
    elements: list[dict]
    speaker_notes: str | None = None
    layout_hint: str | None = None

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, v: str) -> str:
        return _validate_word_count(v, 8)


class RefinedPresentation(BaseModel):
    """Output of the cross-slide refiner with changes log."""

    slides: list[ExpandedSlide]
    changes_made: list[str]
