"""Disk-cached page thumbnails.

Thumbnails are immutable (originals are never modified), so a cache hit is
final and the API serves them with long-lived cache headers.
"""

import logging
import os
from pathlib import Path

from app.errors import NotFoundError, RenderError
from app.pdf.render import placeholder_thumbnail, render_page_thumbnail
from app.services.workspace import Workspace

logger = logging.getLogger(__name__)


def snap_width(width: int, allowed: tuple[int, ...]) -> int:
    return min(allowed, key=lambda w: abs(w - width))


def get_thumbnail(ws: Workspace, file_id: str, page: int, width: int) -> Path:
    record = ws.get_file(file_id)
    if not 0 <= page < record.page_count:
        raise NotFoundError(f"Page {page + 1} does not exist ({record.page_count} pages).")

    cache_dir = ws.thumbs_dir / file_id
    cache_path = cache_dir / f"p{page}_w{width}.webp"
    if cache_path.is_file():
        return cache_path

    try:
        data = render_page_thumbnail(ws.file_path(file_id), page, width)
    except RenderError:
        data = placeholder_thumbnail(width)

    cache_dir.mkdir(parents=True, exist_ok=True)
    tmp = cache_path.with_suffix(".tmp")
    tmp.write_bytes(data)
    os.replace(tmp, cache_path)
    logger.debug("Rendered thumbnail %s/%s p%d w%d", ws.session_id, file_id, page, width)
    return cache_path
