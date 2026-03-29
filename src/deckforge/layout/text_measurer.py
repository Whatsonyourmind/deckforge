"""Pillow-based text measurement with font caching and word wrap."""

from __future__ import annotations

import logging
import platform
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from deckforge.layout.types import BoundingBox

logger = logging.getLogger(__name__)


# Common font name mappings to actual .ttf filenames
_FONT_NAME_MAP: dict[str, list[str]] = {
    "arial": ["arial.ttf", "Arial.ttf", "LiberationSans-Regular.ttf", "liberation-sans/LiberationSans-Regular.ttf"],
    "arial bold": ["arialbd.ttf", "Arial Bold.ttf", "LiberationSans-Bold.ttf"],
    "times new roman": ["times.ttf", "Times New Roman.ttf", "LiberationSerif-Regular.ttf"],
    "courier new": ["cour.ttf", "Courier New.ttf", "LiberationMono-Regular.ttf"],
    "montserrat": ["Montserrat-Regular.ttf", "montserrat/Montserrat-Regular.ttf"],
    "open sans": ["OpenSans-Regular.ttf", "open-sans/OpenSans-Regular.ttf"],
    "calibri": ["calibri.ttf", "Calibri.ttf"],
    "verdana": ["verdana.ttf", "Verdana.ttf"],
    "georgia": ["georgia.ttf", "Georgia.ttf"],
}

# Fallback font names to try in order
_FALLBACK_FONTS = [
    "DejaVuSans.ttf",
    "dejavu-sans/DejaVuSans.ttf",
    "LiberationSans-Regular.ttf",
    "liberation-sans/LiberationSans-Regular.ttf",
    "arial.ttf",
    "Arial.ttf",
]


def _default_font_dirs() -> list[Path]:
    """Return platform-specific system font directories."""
    system = platform.system()
    if system == "Windows":
        return [Path("C:/Windows/Fonts")]
    elif system == "Darwin":
        return [
            Path("/System/Library/Fonts"),
            Path("/Library/Fonts"),
            Path.home() / "Library/Fonts",
        ]
    else:  # Linux and others
        return [
            Path("/usr/share/fonts"),
            Path("/usr/local/share/fonts"),
            Path.home() / ".fonts",
        ]


class TextMeasurer:
    """Measures text dimensions using Pillow for accurate layout computation.

    Uses font rendering at MEASUREMENT_DPI to compute bounding boxes in inches.
    Includes a SAFETY_MARGIN multiplier for cross-platform rendering differences.

    Attributes:
        MEASUREMENT_DPI: DPI used for measurement (72, matching PostScript point size).
        SAFETY_MARGIN: Multiplier applied to measurements (5% = 0.05).
    """

    MEASUREMENT_DPI: int = 72
    SAFETY_MARGIN: float = 0.05

    def __init__(self, font_dir: str | None = None) -> None:
        """Initialize the text measurer.

        Args:
            font_dir: Optional path to font directory. Auto-detects system fonts if None.
        """
        if font_dir:
            self._font_dirs = [Path(font_dir)]
        else:
            self._font_dirs = _default_font_dirs()

        self._font_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}

        # Create a shared drawing surface for measurements
        self._image = Image.new("RGB", (1, 1))
        self._draw = ImageDraw.Draw(self._image)

    def _resolve_font_path(self, font_name: str) -> Path | None:
        """Find a .ttf file matching the given font name.

        Args:
            font_name: Human-readable font name (e.g., "Arial", "Montserrat").

        Returns:
            Path to the .ttf file, or None if not found.
        """
        normalized = font_name.lower().strip()

        # Check name map for known aliases
        candidates = _FONT_NAME_MAP.get(normalized, [])

        # Also try the raw name as a filename
        raw_candidates = [
            f"{font_name}.ttf",
            f"{font_name.replace(' ', '')}.ttf",
            f"{font_name.replace(' ', '-')}.ttf",
            f"{font_name}-Regular.ttf",
        ]
        all_candidates = candidates + raw_candidates

        for font_dir in self._font_dirs:
            if not font_dir.exists():
                continue
            for candidate in all_candidates:
                # Try direct path
                path = font_dir / candidate
                if path.exists():
                    return path
                # Try recursive search
                matches = list(font_dir.rglob(candidate))
                if matches:
                    return matches[0]

        return None

    def _find_fallback_font(self) -> Path | None:
        """Find a fallback font from the known fallback list."""
        for font_dir in self._font_dirs:
            if not font_dir.exists():
                continue
            for fallback in _FALLBACK_FONTS:
                path = font_dir / fallback
                if path.exists():
                    return path
                matches = list(font_dir.rglob(fallback.split("/")[-1]))
                if matches:
                    return matches[0]

        # Last resort: find ANY .ttf file
        for font_dir in self._font_dirs:
            if not font_dir.exists():
                continue
            ttf_files = list(font_dir.rglob("*.ttf"))
            if ttf_files:
                return ttf_files[0]

        return None

    def _get_font(self, font_name: str, size_pt: int) -> ImageFont.FreeTypeFont:
        """Load or retrieve a cached FreeTypeFont.

        Args:
            font_name: Font name to load.
            size_pt: Font size in points.

        Returns:
            Loaded FreeTypeFont instance.
        """
        cache_key = (font_name, size_pt)
        if cache_key in self._font_cache:
            return self._font_cache[cache_key]

        font_path = self._resolve_font_path(font_name)
        if font_path is None:
            logger.warning(
                "Font %r not found, falling back to default font", font_name
            )
            font_path = self._find_fallback_font()

        if font_path is not None:
            try:
                font = ImageFont.truetype(str(font_path), size_pt)
                self._font_cache[cache_key] = font
                return font
            except (OSError, IOError) as e:
                logger.warning("Failed to load font %s: %s", font_path, e)

        # Ultimate fallback: Pillow's built-in bitmap font
        logger.warning("No TrueType fonts available, using Pillow default font")
        font = ImageFont.load_default()
        self._font_cache[cache_key] = font
        return font

    def _word_wrap(self, text: str, font: ImageFont.FreeTypeFont, max_width_px: float) -> str:
        """Wrap text at word boundaries to fit within max_width_px.

        Args:
            text: Input text to wrap.
            font: Font to use for width calculations.
            max_width_px: Maximum line width in pixels.

        Returns:
            Text with newlines inserted at wrap points.
        """
        lines: list[str] = []
        for paragraph in text.split("\n"):
            words = paragraph.split()
            if not words:
                lines.append("")
                continue

            current_line = words[0]
            for word in words[1:]:
                test_line = f"{current_line} {word}"
                line_width = font.getlength(test_line)
                if line_width <= max_width_px:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word
            lines.append(current_line)

        return "\n".join(lines)

    def measure_text(
        self,
        text: str,
        font_name: str,
        size_pt: int = 14,
        max_width_inches: float | None = None,
    ) -> BoundingBox:
        """Measure text and return bounding box in inches.

        Args:
            text: Text to measure.
            font_name: Font name to use.
            size_pt: Font size in points.
            max_width_inches: If provided, word-wrap text at this width.

        Returns:
            BoundingBox with dimensions in inches, including safety margin.
        """
        font = self._get_font(font_name, size_pt)

        if max_width_inches is not None:
            max_width_px = max_width_inches * self.MEASUREMENT_DPI
            text = self._word_wrap(text, font, max_width_px)

        # Measure using appropriate method
        if "\n" in text:
            bbox = self._draw.multiline_textbbox((0, 0), text, font=font)
        else:
            bbox = font.getbbox(text)

        # bbox is (left, top, right, bottom) in pixels
        width_px = bbox[2] - bbox[0]
        height_px = bbox[3] - bbox[1]

        # Convert pixels to inches
        width_inches = width_px / self.MEASUREMENT_DPI
        height_inches = height_px / self.MEASUREMENT_DPI

        # Apply safety margin
        margin_mult = 1.0 + self.SAFETY_MARGIN
        return BoundingBox(
            width_inches=width_inches * margin_mult,
            height_inches=height_inches * margin_mult,
        )

    def measure_bullet_list(
        self,
        items: list[str],
        font_name: str,
        size_pt: int = 14,
        max_width_inches: float = 10.0,
        line_spacing: float = 1.4,
    ) -> BoundingBox:
        """Measure a list of bullet items and return total bounding box.

        Args:
            items: List of text items.
            font_name: Font name to use.
            size_pt: Font size in points.
            max_width_inches: Maximum width for word wrapping.
            line_spacing: Multiplier for inter-item spacing (default 1.4).

        Returns:
            BoundingBox covering all items with spacing.
        """
        if not items:
            return BoundingBox(width_inches=0.0, height_inches=0.0)

        max_width = 0.0
        total_height = 0.0

        for i, item in enumerate(items):
            bb = self.measure_text(item, font_name, size_pt, max_width_inches=max_width_inches)
            max_width = max(max_width, bb.width_inches)

            if i == 0:
                total_height += bb.height_inches
            else:
                # Add spacing between items
                total_height += bb.height_inches * line_spacing

        return BoundingBox(width_inches=max_width, height_inches=total_height)
