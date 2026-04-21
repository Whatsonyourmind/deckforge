"""Deal-deck composers — turn structured deal data into DeckForge IR.

Callers (CreditAI, Aither, any investment platform) POST a DealFacts payload
to /v1/compose/ic-memo (or /teaser, /lp-quarterly, /exit-memo) and get a
fully composed .pptx back. The IR composition lives here so the logic is
shared across deck types and can evolve centrally.
"""
from __future__ import annotations

from deckforge.compose.ic_memo import DealFacts, compose_ic_memo

__all__ = ["DealFacts", "compose_ic_memo"]
