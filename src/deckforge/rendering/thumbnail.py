"""Thumbnail generation -- converts PPTX to PNG slide thumbnails.

Primary path: LibreOffice headless -> PDF -> png via pdf2image.
Fallback path: Pillow-generated placeholder PNG (when LibreOffice not available).
"""

from __future__ import annotations

import io
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

# Default thumbnail dimensions (16:9 aspect ratio at reasonable resolution)
DEFAULT_WIDTH = 960
DEFAULT_HEIGHT = 540


def _find_libreoffice() -> str | None:
    """Locate the LibreOffice binary on the system."""
    for name in ("libreoffice", "soffice"):
        path = shutil.which(name)
        if path:
            return path
    return None


def pptx_to_thumbnails_fallback(
    slide_count: int,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT,
) -> list[bytes]:
    """Generate placeholder PNG thumbnails when LibreOffice is not available.

    Creates simple images with slide number text and a notice that
    LibreOffice is required for real previews.

    Args:
        slide_count: Number of placeholder slides to generate.
        width: Image width in pixels.
        height: Image height in pixels.

    Returns:
        List of PNG bytes, one per slide.
    """
    thumbnails: list[bytes] = []

    for i in range(slide_count):
        img = Image.new("RGB", (width, height), color=(45, 45, 60))
        draw = ImageDraw.Draw(img)

        # Try to use a reasonable font; fall back to default
        try:
            font_large = ImageFont.truetype("arial.ttf", 36)
            font_small = ImageFont.truetype("arial.ttf", 18)
        except (OSError, IOError):
            try:
                font_large = ImageFont.truetype("DejaVuSans.ttf", 36)
                font_small = ImageFont.truetype("DejaVuSans.ttf", 18)
            except (OSError, IOError):
                font_large = ImageFont.load_default()
                font_small = font_large

        # Draw slide number
        slide_text = f"Slide {i + 1}"
        bbox = draw.textbbox((0, 0), slide_text, font=font_large)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        draw.text(
            ((width - text_w) / 2, (height - text_h) / 2 - 20),
            slide_text,
            fill=(200, 200, 220),
            font=font_large,
        )

        # Draw notice
        notice = "Preview unavailable -- LibreOffice not installed"
        bbox_n = draw.textbbox((0, 0), notice, font=font_small)
        notice_w = bbox_n[2] - bbox_n[0]
        draw.text(
            ((width - notice_w) / 2, (height + text_h) / 2 + 10),
            notice,
            fill=(130, 130, 150),
            font=font_small,
        )

        # Draw border
        draw.rectangle(
            [(0, 0), (width - 1, height - 1)],
            outline=(80, 80, 100),
            width=2,
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        thumbnails.append(buf.getvalue())

    return thumbnails


def pptx_to_thumbnails(
    pptx_bytes: bytes,
    max_slides: int = 5,
    dpi: int = 150,
) -> list[bytes]:
    """Convert PPTX to PNG thumbnails via LibreOffice headless.

    Falls back to placeholder images if LibreOffice or pdf2image
    is not available.

    Args:
        pptx_bytes: Raw .pptx file bytes.
        max_slides: Maximum number of slide thumbnails to generate.
        dpi: Resolution for the PNG output.

    Returns:
        List of PNG bytes, one per slide (up to max_slides).
    """
    lo_binary = _find_libreoffice()
    if lo_binary is None:
        logger.info("LibreOffice not found; using placeholder thumbnails")
        # Determine slide count from the PPTX
        slide_count = _count_slides(pptx_bytes)
        return pptx_to_thumbnails_fallback(min(slide_count, max_slides))

    tmpdir = None
    try:
        tmpdir = tempfile.mkdtemp(prefix="deckforge_thumb_")
        tmpdir_path = Path(tmpdir)

        # Write PPTX to temp file
        pptx_path = tmpdir_path / "presentation.pptx"
        pptx_path.write_bytes(pptx_bytes)

        # Convert to PDF via LibreOffice headless
        result = subprocess.run(
            [
                lo_binary,
                "--headless",
                "--convert-to", "pdf",
                "--outdir", str(tmpdir_path),
                str(pptx_path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            logger.warning(
                "LibreOffice conversion failed (rc=%d): %s",
                result.returncode,
                result.stderr[:500],
            )
            slide_count = _count_slides(pptx_bytes)
            return pptx_to_thumbnails_fallback(min(slide_count, max_slides))

        pdf_path = tmpdir_path / "presentation.pdf"
        if not pdf_path.exists():
            logger.warning("LibreOffice did not produce PDF output")
            slide_count = _count_slides(pptx_bytes)
            return pptx_to_thumbnails_fallback(min(slide_count, max_slides))

        # Convert PDF pages to PNG images
        try:
            from pdf2image import convert_from_path

            images = convert_from_path(
                str(pdf_path),
                first_page=1,
                last_page=max_slides,
                dpi=dpi,
            )
        except ImportError:
            logger.info("pdf2image not installed; using placeholder thumbnails")
            slide_count = _count_slides(pptx_bytes)
            return pptx_to_thumbnails_fallback(min(slide_count, max_slides))
        except Exception as exc:
            logger.warning("pdf2image conversion failed: %s", exc)
            slide_count = _count_slides(pptx_bytes)
            return pptx_to_thumbnails_fallback(min(slide_count, max_slides))

        thumbnails: list[bytes] = []
        for img in images[:max_slides]:
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            thumbnails.append(buf.getvalue())

        return thumbnails

    except subprocess.TimeoutExpired:
        logger.warning("LibreOffice conversion timed out")
        slide_count = _count_slides(pptx_bytes)
        return pptx_to_thumbnails_fallback(min(slide_count, max_slides))

    finally:
        if tmpdir:
            import shutil as _shutil
            _shutil.rmtree(tmpdir, ignore_errors=True)


def _count_slides(pptx_bytes: bytes) -> int:
    """Count slides in a PPTX file without full parsing."""
    try:
        from pptx import Presentation as PptxPresentation

        prs = PptxPresentation(io.BytesIO(pptx_bytes))
        return len(prs.slides)
    except Exception:
        return 1


__all__ = ["pptx_to_thumbnails", "pptx_to_thumbnails_fallback"]
