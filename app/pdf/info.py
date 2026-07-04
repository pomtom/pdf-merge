"""Probing uploaded PDFs: page count, page geometry, encryption/corruption detection."""

import logging
from dataclasses import dataclass, field
from pathlib import Path

from pypdf import PdfReader

from app.errors import EncryptedPdfError, InvalidPdfError

logger = logging.getLogger(__name__)


@dataclass
class PageDim:
    index: int
    width_pt: float
    height_pt: float
    rotation: int


@dataclass
class PdfInfo:
    page_count: int
    pages: list[PageDim] = field(default_factory=list)
    was_encrypted: bool = False  # owner-locked but readable with empty password


def open_reader(path: Path) -> PdfReader:
    """Open a PDF for reading, transparently handling empty-password encryption."""
    reader = PdfReader(str(path), strict=False)
    if reader.is_encrypted:
        try:
            result = reader.decrypt("")
        except Exception as exc:
            raise EncryptedPdfError(
                f"{path.name} is password-protected and cannot be processed."
            ) from exc
        if not result:  # PasswordType.NOT_DECRYPTED is falsy
            raise EncryptedPdfError(
                f"{path.name} is password-protected and cannot be processed."
            )
    return reader


def probe_pdf(path: Path) -> PdfInfo:
    """Validate a PDF and return its structure. Touches only page dictionaries,
    never content streams, so probing large files stays cheap."""
    try:
        reader = open_reader(path)
        page_count = len(reader.pages)
        if page_count == 0:
            raise InvalidPdfError(f"{path.name} contains no pages.")
        pages = []
        for i, page in enumerate(reader.pages):
            box = page.mediabox
            pages.append(
                PageDim(
                    index=i,
                    width_pt=round(float(box.width), 2),
                    height_pt=round(float(box.height), 2),
                    rotation=int(page.get("/Rotate") or 0) % 360,
                )
            )
        return PdfInfo(page_count=page_count, pages=pages, was_encrypted=reader.is_encrypted)
    except (EncryptedPdfError, InvalidPdfError):
        raise
    except Exception as exc:
        logger.debug("Probe failed for %s", path, exc_info=True)
        raise InvalidPdfError(f"{path.name} is not a readable PDF file.") from exc
