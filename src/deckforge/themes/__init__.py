"""DeckForge theme system — curated themes, variable resolution, brand kit overlay, contrast validation."""

from deckforge.themes.contrast import (
    ContrastChecker,
    ContrastIssue,
    hex_to_rgb,
    passes_wcag_aa,
    validate_theme_contrast,
)
from deckforge.themes.resolver import ThemeResolver
from deckforge.themes.types import (
    ComponentStyle,
    ResolvedTheme,
    SlideMaster,
    ThemeColors,
    ThemeSpacing,
    ThemeTypography,
)

__all__ = [
    "ComponentStyle",
    "ContrastChecker",
    "ContrastIssue",
    "ResolvedTheme",
    "SlideMaster",
    "ThemeColors",
    "ThemeResolver",
    "ThemeSpacing",
    "ThemeTypography",
    "hex_to_rgb",
    "passes_wcag_aa",
    "validate_theme_contrast",
]
