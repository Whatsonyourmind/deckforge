"""Conditional formatting — stub for TDD RED phase."""

from __future__ import annotations

from deckforge.themes.types import ResolvedTheme


class ConditionalFormatter:
    """Theme-aware conditional formatting — stub."""

    @staticmethod
    def pos_neg_color(value: float, theme: ResolvedTheme) -> str:
        raise NotImplementedError

    @staticmethod
    def pos_neg_text_color(value: float, theme: ResolvedTheme) -> str:
        raise NotImplementedError

    @staticmethod
    def median_highlight(value: float, median: float, theme: ResolvedTheme) -> str:
        raise NotImplementedError

    @staticmethod
    def heatmap_gradient(
        value: float, min_val: float, max_val: float, theme: ResolvedTheme
    ) -> str:
        raise NotImplementedError

    @staticmethod
    def traffic_light(status: str) -> str:
        raise NotImplementedError
