"""Tests for the preview endpoint and thumbnail generation.

Tests cover the thumbnail fallback path (always available) and the preview
response schema. Full LibreOffice integration tests are skipped when
LibreOffice is not installed.
"""

from __future__ import annotations

import base64
import io
import shutil

import pytest
from PIL import Image

from deckforge.ir.presentation import Presentation
from deckforge.rendering.thumbnail import (
    _count_slides,
    pptx_to_thumbnails,
    pptx_to_thumbnails_fallback,
)
from deckforge.workers.tasks import render_pipeline


# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_ir(slides: list[dict], theme: str = "executive-dark") -> dict:
    return {
        "schema_version": "1.0",
        "metadata": {"title": "Preview Test"},
        "theme": theme,
        "slides": slides,
    }


def _title_slide(title: str = "Test Slide") -> dict:
    return {
        "slide_type": "title_slide",
        "elements": [
            {"type": "heading", "content": {"text": title, "level": "h1"}},
        ],
    }


def _get_test_pptx_bytes(slide_count: int = 3) -> bytes:
    """Generate real PPTX bytes using the render pipeline."""
    slides = [_title_slide(f"Slide {i + 1}") for i in range(slide_count)]
    ir = Presentation.model_validate(_make_ir(slides))
    return render_pipeline(ir)


# ── Fallback Thumbnail Tests ─────────────────────────────────────────────────


class TestThumbnailFallback:
    """Test placeholder thumbnail generation (no LibreOffice required)."""

    def test_fallback_returns_correct_count(self):
        """Fallback generates the requested number of thumbnails."""
        result = pptx_to_thumbnails_fallback(3)
        assert len(result) == 3

    def test_fallback_returns_png_bytes(self):
        """Each fallback thumbnail is valid PNG bytes."""
        result = pptx_to_thumbnails_fallback(1)
        assert len(result) == 1

        # Verify it's a valid PNG by loading with Pillow
        img = Image.open(io.BytesIO(result[0]))
        assert img.format == "PNG"
        assert img.size == (960, 540)

    def test_fallback_custom_dimensions(self):
        """Fallback respects custom width/height."""
        result = pptx_to_thumbnails_fallback(1, width=400, height=225)
        img = Image.open(io.BytesIO(result[0]))
        assert img.size == (400, 225)

    def test_fallback_zero_slides(self):
        """Zero slides produces empty list."""
        result = pptx_to_thumbnails_fallback(0)
        assert result == []

    def test_fallback_single_slide(self):
        """Single slide produces one thumbnail."""
        result = pptx_to_thumbnails_fallback(1)
        assert len(result) == 1


# ── pptx_to_thumbnails Tests ────────────────────────────────────────────────


class TestPptxToThumbnails:
    """Test the main pptx_to_thumbnails function."""

    def test_returns_thumbnails_for_3_slide_pptx(self):
        """3-slide PPTX produces 3 thumbnails (fallback or real)."""
        pptx_bytes = _get_test_pptx_bytes(3)
        result = pptx_to_thumbnails(pptx_bytes, max_slides=5)
        assert len(result) == 3

        # Each thumbnail should be valid PNG
        for png_bytes in result:
            img = Image.open(io.BytesIO(png_bytes))
            assert img.format == "PNG"

    def test_max_slides_limits_output(self):
        """max_slides parameter limits the number of returned thumbnails."""
        pptx_bytes = _get_test_pptx_bytes(5)
        result = pptx_to_thumbnails(pptx_bytes, max_slides=2)
        assert len(result) == 2

    def test_thumbnails_are_base64_encodable(self):
        """Thumbnails can be base64-encoded without errors."""
        pptx_bytes = _get_test_pptx_bytes(1)
        result = pptx_to_thumbnails(pptx_bytes, max_slides=1)
        assert len(result) == 1

        encoded = base64.b64encode(result[0]).decode("ascii")
        assert len(encoded) > 100

        # Verify round-trip
        decoded = base64.b64decode(encoded)
        img = Image.open(io.BytesIO(decoded))
        assert img.format == "PNG"


# ── Slide Count Helper Tests ────────────────────────────────────────────────


class TestCountSlides:
    def test_count_slides_matches(self):
        """_count_slides correctly counts slides in a PPTX."""
        pptx_bytes = _get_test_pptx_bytes(4)
        assert _count_slides(pptx_bytes) == 4

    def test_count_slides_invalid_input(self):
        """_count_slides returns 1 for invalid input."""
        assert _count_slides(b"not a pptx") == 1


# ── PreviewResponse Schema Tests ────────────────────────────────────────────


class TestPreviewResponseSchema:
    def test_schema_structure(self):
        """PreviewResponse has correct structure."""
        from deckforge.api.schemas.responses import PreviewResponse, ThumbnailItem

        thumb = ThumbnailItem(slide_index=0, image_base64="abc123")
        resp = PreviewResponse(slide_count=1, thumbnails=[thumb])

        assert resp.slide_count == 1
        assert len(resp.thumbnails) == 1
        assert resp.thumbnails[0].slide_index == 0
        assert resp.thumbnails[0].image_base64 == "abc123"

    def test_schema_serialization(self):
        """PreviewResponse serializes to dict correctly."""
        from deckforge.api.schemas.responses import PreviewResponse, ThumbnailItem

        thumbnails = [
            ThumbnailItem(slide_index=i, image_base64=f"data{i}")
            for i in range(3)
        ]
        resp = PreviewResponse(slide_count=3, thumbnails=thumbnails)
        data = resp.model_dump()

        assert data["slide_count"] == 3
        assert len(data["thumbnails"]) == 3
        assert data["thumbnails"][0]["slide_index"] == 0
        assert data["thumbnails"][2]["image_base64"] == "data2"


# ── LibreOffice Integration Tests (skipped if not available) ────────────────


_has_libreoffice = shutil.which("libreoffice") is not None or shutil.which("soffice") is not None


@pytest.mark.skipif(not _has_libreoffice, reason="LibreOffice not installed")
class TestLibreOfficeIntegration:
    """Tests that require LibreOffice to be installed."""

    def test_real_thumbnails_from_libreoffice(self):
        """With LibreOffice, thumbnails are real rendered images."""
        pptx_bytes = _get_test_pptx_bytes(2)
        result = pptx_to_thumbnails(pptx_bytes, max_slides=2, dpi=72)
        assert len(result) == 2

        for png_bytes in result:
            img = Image.open(io.BytesIO(png_bytes))
            assert img.format == "PNG"
            # Real thumbnails should be larger than placeholders
            assert img.size[0] > 100
            assert img.size[1] > 100
