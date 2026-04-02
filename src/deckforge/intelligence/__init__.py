"""DeckForge Intelligence Layer — powered by OraClaw.

Proprietary AI algorithms for theme selection, content QA, and financial
projections. Calls OraClaw's API endpoints. Gracefully degrades to defaults
when OraClaw is unavailable or disabled.
"""

from deckforge.intelligence.client import OraClaw, oraclaw
from deckforge.intelligence.theme_selector import BanditThemeSelector
from deckforge.intelligence.content_qa import ConvergenceQA
from deckforge.intelligence.finance_projections import MonteCarloProjections

__all__ = [
    "OraClaw",
    "oraclaw",
    "BanditThemeSelector",
    "ConvergenceQA",
    "MonteCarloProjections",
]
