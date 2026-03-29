"""Content generation pipeline -- transforms NL prompts to Presentation IR.

Re-exports the main pipeline class and data models for convenient access.
"""

from deckforge.content.intent_parser import IntentParser
from deckforge.content.models import (
    ExpandedSlide,
    ParsedIntent,
    PresentationOutline,
    RefinedPresentation,
    SlideOutline,
)
from deckforge.content.outliner import Outliner
from deckforge.content.pipeline import ContentPipeline
from deckforge.content.refiner import CrossSlideRefiner
from deckforge.content.slide_writer import SlideWriter

__all__ = [
    "ContentPipeline",
    "IntentParser",
    "Outliner",
    "SlideWriter",
    "CrossSlideRefiner",
    "ParsedIntent",
    "PresentationOutline",
    "SlideOutline",
    "ExpandedSlide",
    "RefinedPresentation",
]
