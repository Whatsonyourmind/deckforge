"""DeckForge IR module — re-exports all IR types for convenient access."""

from deckforge.ir.brand_kit import BrandColors, BrandFonts, BrandKit, FooterConfig, LogoConfig
from deckforge.ir.charts import ChartUnion
from deckforge.ir.elements import ElementUnion
from deckforge.ir.enums import (
    Audience,
    ChartStyle,
    ChartType,
    Confidentiality,
    Density,
    ElementType,
    Emphasis,
    HeadingLevel,
    LayoutHint,
    Purpose,
    QualityTarget,
    SlideType,
    Tone,
    Transition,
)
from deckforge.ir.metadata import GenerationOptions, PresentationMetadata
from deckforge.ir.normalize import normalize_ir
from deckforge.ir.presentation import Presentation
from deckforge.ir.slides import SlideUnion
from deckforge.ir.slides.base import BaseSlide

# Rebuild Presentation to resolve all forward references through the slide -> element chain
Presentation.model_rebuild()

__all__ = [
    # Top-level
    "Presentation",
    "PresentationMetadata",
    "GenerationOptions",
    "normalize_ir",
    "BrandKit",
    "BrandColors",
    "BrandFonts",
    "LogoConfig",
    "FooterConfig",
    # Unions
    "SlideUnion",
    "ElementUnion",
    "ChartUnion",
    # Base
    "BaseSlide",
    # Enums
    "SlideType",
    "ElementType",
    "ChartType",
    "LayoutHint",
    "Transition",
    "Purpose",
    "Audience",
    "Confidentiality",
    "Density",
    "ChartStyle",
    "Emphasis",
    "QualityTarget",
    "Tone",
    "HeadingLevel",
]
