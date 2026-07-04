# PDF Studio

A local web application for working with PDF files: merge many PDFs into one,
split a PDF into parts, and extract selected pages — with page-level control
(reorder files, rotate pages, delete pages) and live page previews.

Everything runs on your machine. The server binds to `127.0.0.1` only, no
files ever leave your computer, and original files are never modified.

Built as a FastAPI backend + vanilla-JS single-page frontend — no build step.

## Features

- **Merge** any number of PDFs, in any order, with drag-and-drop reordering
- **Page-level editing** before merging: select, rotate (90/180/270), delete pages
- **Merge only selected pages** across files
- **Split** a PDF by page ranges (`1-3, 7, 9-12`), into fixed-size chunks, or one file per page
- **Extract** selected pages into a new PDF
- **Page previews**: lazily rendered thumbnails, cached on disk — a 500-page file stays fast
- **Large-file friendly**: uploads stream to disk in 1 MB chunks; no size limits
- **Background processing** with live progress — the UI never freezes
- **Light & dark mode**, follows your OS preference until you toggle manually
- Corrupt and password-protected files are rejected cleanly, never crash a batch

## Quick start

Double-click **`run.bat`** (or run `.\run.ps1` in PowerShell).

It creates a virtual environment on first run (using [uv](https://docs.astral.sh/uv/)
if available, otherwise `py`/`python`), installs dependencies, starts the
server and opens `http://127.0.0.1:8000` in your browser.

Manual equivalent:

```powershell
uv venv .venv --python 3.12
uv pip install -r requirements.txt --python .venv\Scripts\python.exe
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

## Usage

1. **Add files** — drag PDFs anywhere onto the window, or click *+ Add PDFs*.
2. **Arrange** — drag the `⠿` handle to reorder files; the merge follows this order.
3. **Edit pages** — click a file to open its page grid. Click a page to select it
   (Shift-click selects a range), `⟳` rotates, `🗑` deletes/restores.
4. **Act** — *Merge* combines everything (or only selected pages), *Split* divides
   the active file, *Extract* pulls the selected pages into a new PDF.
5. **Download** — finished jobs show a download link in the toast at the bottom right.

## Where data lives

Uploads, thumbnails and outputs are stored per session under
`%TEMP%\pdf-studio\` (override with the `PDF_STUDIO_DATA` environment
variable). Sessions untouched for 24 hours are cleaned up automatically
(`PDF_STUDIO_TTL_HOURS` to change). A debug log is written to
`pdf-studio.log` in the same directory.

## Project structure

```
app/
  main.py            app factory, static serving, startup cleanup
  config.py          settings (env-var overridable)
  models.py          API request/response schemas
  errors.py          error envelope: {"error": {code, message, detail}}
  api/               REST routers: sessions, files, jobs, outputs
  services/          workspace (session state), jobs (thread pool), thumbnails (cache)
  pdf/               engine (merge/split/extract), info (probing), render (pypdfium2)
static/              frontend SPA (vanilla JS modules, CSS design tokens)
scripts/
  generate_test_pdfs.py   builds sample PDFs (numbered pages, corrupt, encrypted)
```

Key libraries: [pypdf](https://pypdf.readthedocs.io/) for PDF structure
operations, [pypdfium2](https://pypdfium2.readthedocs.io/) (Chromium's PDFium)
for page rendering, FastAPI + uvicorn for the server. No Node, no build step —
the only vendored JS dependency is SortableJS for drag-reorder.

## Notes & limits

- Merging builds the output in memory; practical ceiling is a few hundred MB
  of output on a typical desktop.
- Password-protected inputs are rejected (owner-locked PDFs that open without
  a password are accepted transparently). Password support is planned.
- Windows is the primary target; the app itself is cross-platform Python.

## Troubleshooting

- **Port already in use** — set `PDF_STUDIO_PORT` or stop the other process.
- **Pillow fails to install** on a very new Python: use Python 3.12
  (`uv venv .venv --python 3.12`), which has wheels for every dependency.
- Check `%TEMP%\pdf-studio\pdf-studio.log` for details on any error.

## Roadmap (Phase 2)

Bookmarks/outline on merge · page-number stamping · password-protect output
(AES-256) · pure-Python output compression · metadata editing · text search
across files · batch operations.
