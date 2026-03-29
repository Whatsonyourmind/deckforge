"""Elements module — composes ElementUnion as discriminated union on 'type' field."""

from __future__ import annotations

from typing import Annotated, Union

from pydantic import Field

from deckforge.ir.elements.data import (
    ChartElement,
    GaugeElement,
    KpiCardElement,
    MetricGroupElement,
    ProgressBarElement,
    SparklineElement,
    TableElement,
)
from deckforge.ir.elements.layout import (
    ColumnElement,
    ContainerContent,
    ContainerElement,
    GridCellContent,
    GridCellElement,
    RowElement,
)
from deckforge.ir.elements.text import (
    BodyTextElement,
    BulletListElement,
    CalloutBoxElement,
    FootnoteElement,
    HeadingElement,
    LabelElement,
    NumberedListElement,
    PullQuoteElement,
    SubheadingElement,
)
from deckforge.ir.elements.visual import (
    BackgroundElement,
    DividerElement,
    IconElement,
    ImageElement,
    LogoElement,
    ShapeElement,
    SpacerElement,
)

ElementUnion = Annotated[
    Union[
        # Text
        HeadingElement,
        SubheadingElement,
        BodyTextElement,
        BulletListElement,
        NumberedListElement,
        CalloutBoxElement,
        PullQuoteElement,
        FootnoteElement,
        LabelElement,
        # Data
        TableElement,
        ChartElement,
        KpiCardElement,
        MetricGroupElement,
        ProgressBarElement,
        GaugeElement,
        SparklineElement,
        # Visual
        ImageElement,
        IconElement,
        ShapeElement,
        DividerElement,
        SpacerElement,
        LogoElement,
        BackgroundElement,
        # Layout
        ContainerElement,
        ColumnElement,
        RowElement,
        GridCellElement,
    ],
    Field(discriminator="type"),
]

# Rebuild models that have forward references to ElementUnion
ContainerContent.model_rebuild()
GridCellContent.model_rebuild()
ContainerElement.model_rebuild()
ColumnElement.model_rebuild()
RowElement.model_rebuild()
GridCellElement.model_rebuild()

__all__ = [
    "ElementUnion",
    # Text
    "HeadingElement",
    "SubheadingElement",
    "BodyTextElement",
    "BulletListElement",
    "NumberedListElement",
    "CalloutBoxElement",
    "PullQuoteElement",
    "FootnoteElement",
    "LabelElement",
    # Data
    "TableElement",
    "ChartElement",
    "KpiCardElement",
    "MetricGroupElement",
    "ProgressBarElement",
    "GaugeElement",
    "SparklineElement",
    # Visual
    "ImageElement",
    "IconElement",
    "ShapeElement",
    "DividerElement",
    "SpacerElement",
    "LogoElement",
    "BackgroundElement",
    # Layout
    "ContainerElement",
    "ColumnElement",
    "RowElement",
    "GridCellElement",
]
