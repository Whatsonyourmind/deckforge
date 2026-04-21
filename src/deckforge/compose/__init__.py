"""Deal-deck composers — turn structured deal data into DeckForge IR.

Callers (CreditAI, Aither, any investment platform) POST a facts payload to
``/v1/compose/<type>`` or import these composers directly to get a fully
validated Presentation IR, which they then POST to ``/v1/render`` for a
.pptx binary.

Available composers:

- ``compose_ic_memo`` — 12-slide investment committee memo
- ``compose_teaser`` — 6-slide anonymized deal teaser
- ``compose_lp_quarterly`` — 9-slide LP quarterly fund report
- ``compose_exit_memo`` — 8-slide exit recommendation deck
"""
from __future__ import annotations

from deckforge.compose.exit_memo import (
    BuyerCandidate,
    ExitMemoFacts,
    ExitMilestone,
    compose_exit_memo,
)
from deckforge.compose.ic_memo import (
    ComparableTransaction,
    DealFacts,
    compose_ic_memo,
)
from deckforge.compose.lp_quarterly import (
    LPQuarterlyFacts,
    PortfolioHolding,
    PortfolioMover,
    compose_lp_quarterly,
)
from deckforge.compose.teaser import (
    ProcessMilestone,
    TeaserFacts,
    compose_teaser,
)

__all__ = [
    # IC memo
    "ComparableTransaction",
    "DealFacts",
    "compose_ic_memo",
    # Teaser
    "ProcessMilestone",
    "TeaserFacts",
    "compose_teaser",
    # LP quarterly
    "LPQuarterlyFacts",
    "PortfolioHolding",
    "PortfolioMover",
    "compose_lp_quarterly",
    # Exit memo
    "BuyerCandidate",
    "ExitMemoFacts",
    "ExitMilestone",
    "compose_exit_memo",
]
