"""Core PDF operations: merge, split, extract.

All functions report progress via ``progress_cb(current, total, message)`` and
never modify source files. Rotations are applied to the writer's copy of a
page, never to the source reader's page object.
"""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from pypdf import PdfWriter

from app.errors import ValidationFailed
from app.pdf.info import open_reader

logger = logging.getLogger(__name__)

ProgressCb = Callable[[int, int, str], None]


@dataclass
class SourcePages:
    """One input to a merge: a PDF path and the pages to take from it.

    ``pages`` is a list of (page_index, rotate_degrees); ``None`` means all
    pages in natural order without extra rotation.
    """
    path: Path
    pages: Optional[list[tuple[int, int]]] = None


def _resolve_pages(item: SourcePages, page_count: int) -> list[tuple[int, int]]:
    if item.pages is None:
        return [(i, 0) for i in range(page_count)]
    for index, _rot in item.pages:
        if index >= page_count:
            raise ValidationFailed(
                f"Page {index + 1} does not exist in {item.path.name} "
                f"({page_count} pages)."
            )
    return item.pages


def merge_pdfs(items: list[SourcePages], out_path: Path, progress_cb: ProgressCb) -> None:
    """Merge selected pages of multiple PDFs into ``out_path`` in the given order."""
    # Readers must stay open until write(): pypdf resolves indirect objects
    # (content streams) lazily at write time.
    readers = [open_reader(item.path) for item in items]
    plans = [_resolve_pages(item, len(r.pages)) for item, r in zip(items, readers)]
    total = sum(len(p) for p in plans)
    if total == 0:
        raise ValidationFailed("No pages selected to merge.")

    writer = PdfWriter()
    done = 0
    for item, reader, plan in zip(items, readers, plans):
        for index, rotate in plan:
            added = writer.add_page(reader.pages[index])
            if rotate:
                added.rotate(rotate)
            done += 1
            progress_cb(done, total, f"Adding pages from {item.path.name}")

    progress_cb(done, total, "Writing output file")
    with open(out_path, "wb") as fh:
        writer.write(fh)
    logger.info("Merged %d pages from %d files into %s", total, len(items), out_path.name)


def extract_pages(
    path: Path, pages: list[tuple[int, int]], out_path: Path, progress_cb: ProgressCb
) -> None:
    """Extract the given pages (in the given order, with rotations) into a new PDF."""
    merge_pdfs([SourcePages(path=path, pages=pages)], out_path, progress_cb)


def split_pdf(
    path: Path,
    mode: str,
    out_dir: Path,
    basename: str,
    progress_cb: ProgressCb,
    ranges: Optional[list[tuple[int, int]]] = None,
    chunk_size: Optional[int] = None,
) -> list[Path]:
    """Split a PDF into multiple files. Returns the created paths.

    Modes:
      - ``ranges``: explicit 1-based inclusive ranges, one output per range
      - ``every_page``: one output per page
      - ``chunks``: consecutive groups of ``chunk_size`` pages
    """
    reader = open_reader(path)
    page_count = len(reader.pages)

    if mode == "ranges":
        if not ranges:
            raise ValidationFailed("Split mode 'ranges' requires at least one range.")
        groups = []
        for start, end in ranges:
            if not (1 <= start <= end <= page_count):
                raise ValidationFailed(
                    f"Range {start}-{end} is out of bounds for {path.name} "
                    f"({page_count} pages)."
                )
            groups.append((f"p{start}-{end}", list(range(start - 1, end))))
    elif mode == "every_page":
        groups = [(f"p{i + 1}", [i]) for i in range(page_count)]
    elif mode == "chunks":
        if not chunk_size:
            raise ValidationFailed("Split mode 'chunks' requires a chunk size.")
        groups = []
        for start in range(0, page_count, chunk_size):
            end = min(start + chunk_size, page_count)
            groups.append((f"p{start + 1}-{end}", list(range(start, end))))
    else:
        raise ValidationFailed(f"Unknown split mode: {mode}")

    total = sum(len(indices) for _, indices in groups)
    outputs: list[Path] = []
    done = 0
    for label, indices in groups:
        writer = PdfWriter()
        for i in indices:
            writer.add_page(reader.pages[i])
            done += 1
            progress_cb(done, total, f"Splitting {path.name} ({label})")
        out_path = out_dir / f"{basename}_{label}.pdf"
        with open(out_path, "wb") as fh:
            writer.write(fh)
        outputs.append(out_path)

    logger.info("Split %s into %d files", path.name, len(outputs))
    return outputs
