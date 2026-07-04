"""Application settings, overridable via environment variables."""

import os
import tempfile
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    data_dir: Path = field(
        default_factory=lambda: Path(
            os.environ.get("PDF_STUDIO_DATA", Path(tempfile.gettempdir()) / "pdf-studio")
        )
    )
    host: str = os.environ.get("PDF_STUDIO_HOST", "127.0.0.1")
    port: int = int(os.environ.get("PDF_STUDIO_PORT", "8000"))
    # Allowed thumbnail widths; requests snap to the nearest one so the
    # disk cache stays bounded.
    thumb_widths: tuple[int, ...] = (160, 320, 640)
    session_ttl_hours: float = float(os.environ.get("PDF_STUDIO_TTL_HOURS", "24"))
    max_workers: int = int(os.environ.get("PDF_STUDIO_WORKERS", "2"))
    upload_chunk_bytes: int = 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    return settings
