"""Logging setup: concise console output plus a rotating debug log file."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(data_dir: Path) -> None:
    root = logging.getLogger()
    if root.handlers:  # already configured (e.g. uvicorn --reload re-import)
        return
    root.setLevel(logging.DEBUG)

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter("%(levelname)-7s %(name)s: %(message)s"))
    root.addHandler(console)

    logfile = RotatingFileHandler(
        data_dir / "pdf-studio.log", maxBytes=2 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    logfile.setLevel(logging.DEBUG)
    logfile.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root.addHandler(logfile)

    # pypdf emits many benign warnings on imperfect PDFs
    logging.getLogger("pypdf").setLevel(logging.ERROR)
    logging.getLogger("PIL").setLevel(logging.WARNING)
