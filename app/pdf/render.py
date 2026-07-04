"""Page thumbnail rendering with pypdfium2.

PDFium is not thread-safe: every render happens under a single global lock,
which also caps rendering memory to one page at a time.
"""

import io
import logging
import threading

import pypdfium2 as pdfium
from PIL import Image, ImageDraw

from app.errors import RenderError

logger = logging.getLogger(__name__)

RENDER_LOCK = threading.Lock()


def render_page_thumbnail(pdf_path, page_index: int, width_px: int) -> bytes:
    """Render one page to WEBP bytes at the requested pixel width."""
    try:
        with RENDER_LOCK:
            doc = pdfium.PdfDocument(str(pdf_path))
            try:
                page = doc[page_index]
                try:
                    page_width = page.get_width()  # points; 1pt = 1px at 72 dpi
                    scale = width_px / page_width if page_width else 1.0
                    bitmap = page.render(scale=scale)
                    image = bitmap.to_pil()
                finally:
                    page.close()
            finally:
                doc.close()
        buf = io.BytesIO()
        image.save(buf, "WEBP", quality=80)
        return buf.getvalue()
    except Exception as exc:
        logger.warning("Render failed for %s page %d: %s", pdf_path, page_index, exc)
        raise RenderError(f"Could not render page {page_index + 1}.") from exc


def placeholder_thumbnail(width_px: int) -> bytes:
    """Grey tile shown for pages PDFium cannot render, so the grid never breaks."""
    height = int(width_px * 1.414)  # A4-ish aspect
    image = Image.new("RGB", (width_px, height), "#e5e5e5")
    draw = ImageDraw.Draw(image)
    draw.rectangle([0, 0, width_px - 1, height - 1], outline="#b0b0b0")
    cx, cy, r = width_px // 2, height // 2, width_px // 8
    draw.line([cx - r, cy - r, cx + r, cy + r], fill="#909090", width=3)
    draw.line([cx - r, cy + r, cx + r, cy - r], fill="#909090", width=3)
    buf = io.BytesIO()
    image.save(buf, "WEBP", quality=80)
    return buf.getvalue()
