"""Theme registry — loads, resolves, caches YAML themes from the data directory."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from deckforge.ir.brand_kit import BrandKit
from deckforge.themes.brand_kit_merger import BrandKitMerger
from deckforge.themes.contrast import ContrastIssue, validate_theme_contrast
from deckforge.themes.resolver import ThemeResolver
from deckforge.themes.types import (
    ComponentStyle,
    FooterDefaults,
    LogoDefaults,
    ResolvedTheme,
    SlideMaster,
    ThemeColors,
    ThemeSpacing,
    ThemeTypography,
)

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path(__file__).parent / "data"


class ThemeRegistry:
    """Registry for loading, resolving, and caching theme YAML files.

    Themes are loaded from YAML files in the data/ directory, resolved
    via ThemeResolver, validated for contrast, and cached.
    """

    def __init__(self, themes_dir: Path | None = None) -> None:
        self._themes_dir = themes_dir or _DEFAULT_DATA_DIR
        self._cache: dict[str, ResolvedTheme] = {}

    def load_theme(self, theme_id: str) -> ResolvedTheme:
        """Load a theme YAML file, resolve variables, validate, and cache.

        Args:
            theme_id: Filename stem (e.g., 'executive-dark' for executive-dark.yaml)

        Returns:
            Fully resolved ResolvedTheme with all $references expanded.

        Raises:
            FileNotFoundError: If the YAML file doesn't exist.
            ValueError: If the YAML is invalid or resolution fails.
        """
        if theme_id in self._cache:
            return self._cache[theme_id]

        yaml_path = self._themes_dir / f"{theme_id}.yaml"
        if not yaml_path.exists():
            msg = f"Theme file not found: {yaml_path}"
            raise FileNotFoundError(msg)

        with open(yaml_path, encoding="utf-8") as f:
            raw: dict[str, Any] = yaml.safe_load(f)

        # Resolve all $variable references
        resolver = ThemeResolver(raw)
        resolved = resolver.resolve_all()

        # Convert to ResolvedTheme Pydantic model
        theme = self._dict_to_theme(resolved)

        # Validate contrast (log warnings, don't reject)
        issues = validate_theme_contrast(theme)
        if issues:
            for issue in issues:
                logger.warning(
                    "Theme '%s' contrast issue: %s — ratio %.1f:1 (need %.1f:1)",
                    theme_id,
                    issue.context,
                    issue.ratio,
                    issue.required_ratio,
                )

        self._cache[theme_id] = theme
        return theme

    def list_themes(self) -> list[dict[str, str]]:
        """List all available themes with name, description, version."""
        themes = []
        for yaml_path in sorted(self._themes_dir.glob("*.yaml")):
            with open(yaml_path, encoding="utf-8") as f:
                raw = yaml.safe_load(f)
            themes.append(
                {
                    "id": yaml_path.stem,
                    "name": raw.get("name", yaml_path.stem),
                    "description": raw.get("description", ""),
                    "version": raw.get("version", "1.0"),
                }
            )
        return themes

    def get_theme(
        self,
        theme_id: str,
        brand_kit: BrandKit | None = None,
    ) -> ResolvedTheme:
        """Get a theme, optionally merged with a BrandKit overlay.

        Args:
            theme_id: Theme identifier (YAML filename stem).
            brand_kit: Optional BrandKit to overlay on the theme.

        Returns:
            ResolvedTheme, possibly with brand kit overrides applied.
        """
        theme = self.load_theme(theme_id)
        if brand_kit is not None:
            return BrandKitMerger.merge(theme, brand_kit)
        return theme

    def validate_all(self) -> dict[str, list[ContrastIssue]]:
        """Load every theme and check contrast. Returns issues per theme."""
        results: dict[str, list[ContrastIssue]] = {}
        for yaml_path in sorted(self._themes_dir.glob("*.yaml")):
            theme_id = yaml_path.stem
            try:
                theme = self.load_theme(theme_id)
                results[theme_id] = validate_theme_contrast(theme)
            except Exception as exc:
                logger.error("Failed to load theme '%s': %s", theme_id, exc)
                # Create a synthetic issue for load failures
                results[theme_id] = [
                    ContrastIssue(
                        fg_color="",
                        bg_color="",
                        ratio=0.0,
                        required_ratio=4.5,
                        context=f"Load error: {exc}",
                    )
                ]
        return results

    def _dict_to_theme(self, d: dict[str, Any]) -> ResolvedTheme:
        """Convert a resolved dict into a ResolvedTheme model."""
        # Extract colors — use palette (semantic) if available, falling back to colors (raw)
        colors_raw = d.get("palette", d.get("colors", {}))
        colors_fallback = d.get("colors", {})

        def color(key: str, fallback_key: str | None = None) -> str:
            val = colors_raw.get(key)
            if val and not str(val).startswith("$"):
                return str(val)
            if fallback_key:
                val = colors_raw.get(fallback_key) or colors_fallback.get(fallback_key)
                if val and not str(val).startswith("$"):
                    return str(val)
            val = colors_fallback.get(key, "#000000")
            return str(val) if not str(val).startswith("$") else "#000000"

        colors = ThemeColors(
            primary=color("primary"),
            secondary=color("secondary"),
            accent=color("accent"),
            background=color("background", "bg"),
            surface=color("surface"),
            text_primary=color("text_primary", "text"),
            text_secondary=color("text_secondary"),
            text_muted=color("text_muted", "muted"),
            positive=color("positive", "success"),
            negative=color("negative", "danger"),
            warning=color("warning"),
        )

        # Typography
        typo_raw = d.get("typography", {})
        typography = ThemeTypography(
            heading_family=typo_raw.get("heading_family", "Arial"),
            body_family=typo_raw.get("body_family", "Calibri"),
            mono_family=typo_raw.get("mono_family", "Consolas"),
            scale=typo_raw.get("scale", {}),
            weights=typo_raw.get("weights", {}),
            line_height=typo_raw.get("line_height", 1.4),
        )

        # Spacing
        spacing_raw = d.get("spacing", {})
        spacing = ThemeSpacing(
            margin_top=spacing_raw.get("margin_top", 0.5),
            margin_bottom=spacing_raw.get("margin_bottom", 0.5),
            margin_left=spacing_raw.get("margin_left", 0.75),
            margin_right=spacing_raw.get("margin_right", 0.75),
            gutter=spacing_raw.get("gutter", 0.3),
            element_gap=spacing_raw.get("element_gap", 0.2),
            section_gap=spacing_raw.get("section_gap", 0.5),
        )

        # Slide masters
        masters_raw = d.get("slide_masters", {})
        slide_masters: dict[str, SlideMaster] = {}
        for master_name, master_data in masters_raw.items():
            if not isinstance(master_data, dict):
                continue
            regions: dict[str, ComponentStyle] = {}
            regions_raw = master_data.get("regions", {})
            if isinstance(regions_raw, dict):
                for region_name, region_data in regions_raw.items():
                    if isinstance(region_data, dict):
                        regions[region_name] = ComponentStyle(**{
                            k: v for k, v in region_data.items()
                            if k in ComponentStyle.model_fields
                        })
            bg = master_data.get("background", colors.background)
            if isinstance(bg, str) and not bg.startswith("$"):
                pass
            else:
                bg = colors.background
            slide_masters[master_name] = SlideMaster(
                background=bg, regions=regions
            )

        # Chart colors
        chart_colors = d.get("chart_colors", [])
        if isinstance(chart_colors, list):
            chart_colors = [str(c) for c in chart_colors if not str(c).startswith("$")]

        # Logo defaults
        logo_raw = d.get("logo", {})
        logo = LogoDefaults(
            max_width=logo_raw.get("max_width", 1.0),
            max_height=logo_raw.get("max_height", 0.5),
            placement=logo_raw.get("placement", "top_left"),
            opacity=logo_raw.get("opacity", 1.0),
        )

        # Footer defaults
        footer_raw = d.get("footer", {})
        footer = FooterDefaults(
            text=footer_raw.get("text"),
            include_page_numbers=footer_raw.get("include_page_numbers", True),
            include_date=footer_raw.get("include_date", False),
            include_logo=footer_raw.get("include_logo", False),
        )

        # Protected keys
        protected = d.get("_protected", [])

        return ResolvedTheme(
            name=d.get("name", "Unnamed"),
            description=d.get("description", ""),
            version=str(d.get("version", "1.0")),
            colors=colors,
            typography=typography,
            spacing=spacing,
            slide_masters=slide_masters,
            chart_colors=chart_colors,
            logo=logo,
            footer=footer,
            protected_keys=protected if isinstance(protected, list) else [],
        )
