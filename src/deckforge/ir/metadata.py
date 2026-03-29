"""Presentation metadata and generation options models."""

from __future__ import annotations

from pydantic import BaseModel

from deckforge.ir.enums import (
    Audience,
    ChartStyle,
    Confidentiality,
    Density,
    Emphasis,
    Purpose,
    QualityTarget,
)


class PresentationMetadata(BaseModel):
    """Metadata describing the presentation context and audience."""

    title: str
    subtitle: str | None = None
    author: str | None = None
    company: str | None = None
    date: str | None = None
    language: str = "en"
    purpose: Purpose | None = None
    audience: Audience | None = None
    confidentiality: Confidentiality = Confidentiality.INTERNAL


class GenerationOptions(BaseModel):
    """Options controlling AI content generation behavior."""

    target_slide_count: int | list[int] | None = None
    density: Density = Density.BALANCED
    chart_style: ChartStyle = ChartStyle.MINIMAL
    emphasis: Emphasis = Emphasis.VISUAL
    quality_target: QualityTarget = QualityTarget.PRESENTATION_READY
