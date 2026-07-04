"""Generate sample PDFs into scripts/samples/ for manual and API testing.

Pages are stamped with their number in large type so ordering, rotation and
extraction mistakes are visible at a glance. Uses hand-built minimal PDF
syntax (no dependencies) for the visible files, and pypdf for the encrypted
sample.

Usage:  python scripts/generate_test_pdfs.py
"""

import sys
import zlib
from pathlib import Path

SAMPLES = Path(__file__).parent / "samples"

A4 = (595, 842)
LETTER_LANDSCAPE = (792, 612)


def make_pdf(pages: list[tuple[float, float, str]]) -> bytes:
    """Build a minimal valid PDF: one Helvetica text label per page."""
    objects: list[bytes] = []  # 1-indexed body objects

    def add(body: bytes) -> int:
        objects.append(body)
        return len(objects)

    # Object numbers are assigned in order: font, then per page
    # (content, page), then Pages, then Catalog.
    font = add(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    page_nums = []
    for width, height, label in pages:
        text = (
            f"BT /F1 72 Tf 1 0 0 1 {width / 2 - 18 * len(label)} {height / 2 - 24} Tm "
            f"({label}) Tj ET"
        ).encode()
        stream = zlib.compress(text)
        content = add(
            b"<< /Length %d /Filter /FlateDecode >>\nstream\n%s\nendstream"
            % (len(stream), stream)
        )
        page = add(b"")  # placeholder, patched once we know the Pages object number
        page_nums.append((page, width, height, content))

    pages_num = add(b"")  # placeholder
    kid_refs = b" ".join(b"%d 0 R" % p for p, *_ in page_nums)
    objects[pages_num - 1] = (
        b"<< /Type /Pages /Kids [%s] /Count %d >>" % (kid_refs, len(page_nums))
    )
    for page, width, height, content in page_nums:
        objects[page - 1] = (
            b"<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %d %d] "
            b"/Resources << /Font << /F1 %d 0 R >> >> /Contents %d 0 R >>"
            % (pages_num, width, height, font, content)
        )
    catalog = add(b"<< /Type /Catalog /Pages %d 0 R >>" % pages_num)

    out = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for i, body in enumerate(objects, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref_at = len(out)
    out += b"xref\n0 %d\n" % (len(objects) + 1)
    out += b"0000000000 65535 f \n"
    for off in offsets[1:]:
        out += b"%010d 00000 n \n" % off
    out += (
        b"trailer\n<< /Size %d /Root %d 0 R >>\nstartxref\n%d\n%%%%EOF\n"
        % (len(objects) + 1, catalog, xref_at)
    )
    return bytes(out)


def numbered(count: int, size=A4) -> bytes:
    return make_pdf([(size[0], size[1], str(i + 1)) for i in range(count)])


def main() -> None:
    SAMPLES.mkdir(exist_ok=True)

    (SAMPLES / "small_3p.pdf").write_bytes(numbered(3))
    (SAMPLES / "medium_50p.pdf").write_bytes(numbered(50))
    (SAMPLES / "large_500p.pdf").write_bytes(numbered(500))
    (SAMPLES / "landscape_5p.pdf").write_bytes(numbered(5, LETTER_LANDSCAPE))

    # Corrupt: a valid PDF with its tail (xref + trailer) cut off.
    data = numbered(3)
    (SAMPLES / "corrupt.pdf").write_bytes(data[: int(len(data) * 0.6)])

    # Encrypted with a real user password (requires pypdf).
    try:
        from pypdf import PdfReader, PdfWriter

        import io
        reader = PdfReader(io.BytesIO(numbered(2)))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(user_password="secret")
        with open(SAMPLES / "encrypted.pdf", "wb") as fh:
            writer.write(fh)
    except ImportError:
        print("pypdf not available - skipped encrypted.pdf", file=sys.stderr)

    for f in sorted(SAMPLES.glob("*.pdf")):
        print(f"{f.name:20} {f.stat().st_size:>10,} bytes")


if __name__ == "__main__":
    main()
