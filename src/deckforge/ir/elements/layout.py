"""Layout element models — container, column, row, grid_cell."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from pydantic import BaseModel

from deckforge.ir.elements.base import BaseElement

if TYPE_CHECKING:
    from deckforge.ir.elements import ElementUnion


# ── Content Models ─────────────────────────────────────────────────────────────


class ContainerContent(BaseModel):
    children: list[ElementUnion] = []


class GridCellContent(BaseModel):
    span: int = 1
    children: list[ElementUnion] = []


# ── Element Models ─────────────────────────────────────────────────────────────


class ContainerElement(BaseElement):
    type: Literal["container"] = "container"
    content: ContainerContent


class ColumnElement(BaseElement):
    type: Literal["column"] = "column"
    content: ContainerContent


class RowElement(BaseElement):
    type: Literal["row"] = "row"
    content: ContainerContent


class GridCellElement(BaseElement):
    type: Literal["grid_cell"] = "grid_cell"
    content: GridCellContent
