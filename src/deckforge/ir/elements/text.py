"""Text element models — heading, subheading, body_text, bullet_list, etc."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel

from deckforge.ir.elements.base import BaseElement
from deckforge.ir.enums import HeadingLevel


# ── Content Models ─────────────────────────────────────────────────────────────


class HeadingContent(BaseModel):
    text: str
    level: HeadingLevel = HeadingLevel.H1


class SubheadingContent(BaseModel):
    text: str


class BodyTextContent(BaseModel):
    text: str
    markdown: bool = False


class BulletListContent(BaseModel):
    items: list[str]
    style: Literal["disc", "dash", "arrow"] = "disc"


class NumberedListContent(BaseModel):
    items: list[str]
    start: int = 1


class CalloutBoxContent(BaseModel):
    text: str
    style: Literal["info", "warning", "success", "error"] = "info"


class PullQuoteContent(BaseModel):
    text: str
    attribution: str | None = None


class FootnoteContent(BaseModel):
    text: str
    number: int | None = None


class LabelContent(BaseModel):
    text: str


# ── Element Models ─────────────────────────────────────────────────────────────


class HeadingElement(BaseElement):
    type: Literal["heading"] = "heading"
    content: HeadingContent


class SubheadingElement(BaseElement):
    type: Literal["subheading"] = "subheading"
    content: SubheadingContent


class BodyTextElement(BaseElement):
    type: Literal["body_text"] = "body_text"
    content: BodyTextContent


class BulletListElement(BaseElement):
    type: Literal["bullet_list"] = "bullet_list"
    content: BulletListContent


class NumberedListElement(BaseElement):
    type: Literal["numbered_list"] = "numbered_list"
    content: NumberedListContent


class CalloutBoxElement(BaseElement):
    type: Literal["callout_box"] = "callout_box"
    content: CalloutBoxContent


class PullQuoteElement(BaseElement):
    type: Literal["pull_quote"] = "pull_quote"
    content: PullQuoteContent


class FootnoteElement(BaseElement):
    type: Literal["footnote"] = "footnote"
    content: FootnoteContent


class LabelElement(BaseElement):
    type: Literal["label"] = "label"
    content: LabelContent
