"""Brand kit merger — deep merges BrandKit overlay onto a ResolvedTheme."""

from __future__ import annotations

import copy
import logging
from typing import Any

from deckforge.ir.brand_kit import BrandKit
from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Keys that brand kit cannot override (structural properties)
PROTECTED_KEYS: set[str] = {"spacing", "typography.scale", "typography.line_height"}


class BrandKitMerger:
    """Merges a BrandKit overlay onto a ResolvedTheme.

    Brand kit can override colors and fonts but cannot modify
    structural properties like spacing, typography scale, or line height.
    Returns a new ResolvedTheme without mutating the original.
    """

    @staticmethod
    def merge(theme: ResolvedTheme, brand_kit: BrandKit) -> ResolvedTheme:
        """Apply brand kit overrides to a theme, returning a new ResolvedTheme.

        Mapping:
          - brand_kit.colors.primary -> theme.colors.primary
          - brand_kit.colors.secondary -> theme.colors.secondary
          - brand_kit.colors.accent[0] -> theme.colors.accent (first accent)
          - brand_kit.colors.background -> theme.colors.background
          - brand_kit.colors.text -> theme.colors.text_primary
          - brand_kit.colors.muted -> theme.colors.text_muted
          - brand_kit.fonts.heading -> theme.typography.heading_family
          - brand_kit.fonts.body -> theme.typography.body_family
          - brand_kit.fonts.mono -> theme.typography.mono_family
          - brand_kit.fonts.caption -> (no direct mapping, logged)
          - brand_kit.logo -> theme.logo
          - brand_kit.footer -> theme.footer

        Protected keys (spacing, typography.scale, typography.line_height)
        are skipped with a warning if brand_kit attempts to set them.
        """
        # Work on a deep copy to avoid mutation
        theme_dict = theme.model_dump()

        if brand_kit.colors is not None:
            colors = brand_kit.colors
            if colors.primary:
                theme_dict["colors"]["primary"] = colors.primary
            if colors.secondary is not None:
                theme_dict["colors"]["secondary"] = colors.secondary
            if colors.accent:
                theme_dict["colors"]["accent"] = colors.accent[0]
            if colors.background is not None:
                theme_dict["colors"]["background"] = colors.background
            if colors.text is not None:
                theme_dict["colors"]["text_primary"] = colors.text
            if colors.muted is not None:
                theme_dict["colors"]["text_muted"] = colors.muted

        if brand_kit.fonts is not None:
            fonts = brand_kit.fonts
            # Check protected keys
            if fonts.heading is not None:
                theme_dict["typography"]["heading_family"] = fonts.heading
            if fonts.body is not None:
                theme_dict["typography"]["body_family"] = fonts.body
            if fonts.mono is not None:
                theme_dict["typography"]["mono_family"] = fonts.mono
            if fonts.caption is not None:
                logger.info(
                    "BrandKit caption font '%s' noted but no direct theme mapping",
                    fonts.caption,
                )

        # Protected keys: spacing, typography.scale, typography.line_height
        # These are never overridden by brand kit — log if attempted
        for key in PROTECTED_KEYS:
            logger.debug(
                "Protected key '%s' preserved from theme (brand kit cannot override)",
                key,
            )

        if brand_kit.logo is not None:
            logo = brand_kit.logo
            theme_dict["logo"] = {
                "max_width": logo.max_width or theme_dict["logo"]["max_width"],
                "max_height": logo.max_height or theme_dict["logo"]["max_height"],
                "placement": logo.placement,
                "opacity": theme_dict["logo"].get("opacity", 1.0),
            }

        if brand_kit.footer is not None:
            footer = brand_kit.footer
            theme_dict["footer"] = {
                "text": footer.text,
                "include_page_numbers": footer.include_page_numbers,
                "include_date": footer.include_date,
                "include_logo": footer.include_logo,
            }

        return ResolvedTheme(**theme_dict)

    @staticmethod
    def _deep_merge(
        base: dict[str, Any],
        overlay: dict[str, Any],
        protected: set[str],
        prefix: str = "",
    ) -> dict[str, Any]:
        """Recursively merge overlay into base, skipping protected key paths."""
        result = copy.deepcopy(base)
        for key, value in overlay.items():
            current_path = f"{prefix}.{key}" if prefix else key
            if current_path in protected:
                logger.warning(
                    "BrandKit attempted to override protected key '%s' — skipped",
                    current_path,
                )
                continue
            if (
                isinstance(value, dict)
                and key in result
                and isinstance(result[key], dict)
            ):
                result[key] = BrandKitMerger._deep_merge(
                    result[key], value, protected, current_path
                )
            else:
                result[key] = copy.deepcopy(value)
        return result
