"""Brand compliance checker -- font families, colors, logo, confidentiality."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from deckforge.qa.types import QAIssue

if TYPE_CHECKING:
    from deckforge.ir.presentation import Presentation
    from deckforge.layout.types import LayoutResult
    from deckforge.themes.types import ResolvedTheme

logger = logging.getLogger(__name__)

# Element types that can have font overrides
_STYLED_ELEMENT_TYPES = {
    "heading", "subheading", "body_text", "bullet_list",
    "numbered_list", "callout_box", "pull_quote", "footnote", "label",
}


class BrandComplianceChecker:
    """Check brand compliance in a presentation.

    Checks:
        - All font families against theme typography (heading, body, mono)
        - All explicit colors against theme color palette
        - Brand kit logo referenced in elements if specified
        - Confidentiality marking present if metadata.confidentiality is set
    """

    def check(
        self,
        presentation: Presentation,
        layout_results: list[LayoutResult],
        theme: ResolvedTheme,
    ) -> list[QAIssue]:
        """Run brand compliance checks on the presentation."""
        issues: list[QAIssue] = []

        # Build approved font set from theme
        approved_fonts = {
            theme.typography.heading_family.lower(),
            theme.typography.body_family.lower(),
            theme.typography.mono_family.lower(),
        }

        # Build approved color palette from theme
        approved_colors = self._build_color_palette(theme)

        for idx, slide in enumerate(presentation.slides):
            for elem in slide.elements:
                etype = getattr(elem, "type", None)
                if etype not in _STYLED_ELEMENT_TYPES:
                    continue

                # Check font family overrides
                overrides = getattr(elem, "style_overrides", None)
                if overrides and isinstance(overrides, dict):
                    font_family = overrides.get("font_family")
                    if font_family and font_family.lower() not in approved_fonts:
                        issues.append(
                            QAIssue(
                                type="unapproved_font",
                                severity="warning",
                                slide_index=idx,
                                region=None,
                                message=(
                                    f"Font '{font_family}' is not in theme-approved "
                                    f"families: {', '.join(sorted(approved_fonts))}"
                                ),
                                details={
                                    "font_family": font_family,
                                    "approved": sorted(approved_fonts),
                                },
                            )
                        )

                    # Check explicit color overrides
                    color = overrides.get("color")
                    if color and color.lower() not in approved_colors:
                        issues.append(
                            QAIssue(
                                type="unapproved_color",
                                severity="info",
                                slide_index=idx,
                                region=None,
                                message=(
                                    f"Color '{color}' is not in theme palette"
                                ),
                                details={
                                    "color": color,
                                },
                            )
                        )

        # Check logo reference
        brand_kit = presentation.brand_kit
        if brand_kit and brand_kit.logo:
            logo_referenced = any(
                getattr(elem, "type", None) == "logo"
                for slide in presentation.slides
                for elem in slide.elements
            )
            if not logo_referenced:
                issues.append(
                    QAIssue(
                        type="missing_logo",
                        severity="info",
                        slide_index=0,
                        region=None,
                        message="Brand kit specifies a logo but no logo element found",
                    )
                )

        # Check confidentiality marking
        if presentation.metadata.confidentiality and presentation.metadata.confidentiality.value != "public":
            has_footer_with_conf = False
            for slide in presentation.slides:
                for elem in slide.elements:
                    content = getattr(elem, "content", None)
                    if content:
                        text = getattr(content, "text", "")
                        if isinstance(text, str) and presentation.metadata.confidentiality.value.lower() in text.lower():
                            has_footer_with_conf = True
                            break
                if has_footer_with_conf:
                    break

            if not has_footer_with_conf:
                issues.append(
                    QAIssue(
                        type="missing_confidentiality",
                        severity="info",
                        slide_index=0,
                        region=None,
                        message=(
                            f"Metadata specifies confidentiality "
                            f"'{presentation.metadata.confidentiality.value}' "
                            f"but no slide mentions it"
                        ),
                    )
                )

        return issues

    def _build_color_palette(self, theme: ResolvedTheme) -> set[str]:
        """Build a set of approved colors from the theme."""
        colors = set()
        for field_name in type(theme.colors).model_fields:
            val = getattr(theme.colors, field_name, None)
            if isinstance(val, str):
                colors.add(val.lower())
        for chart_color in theme.chart_colors:
            colors.add(chart_color.lower())
        return colors
