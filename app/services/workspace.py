"""Per-session workspaces on disk.

Layout under DATA_DIR:
    <session_id>/
        manifest.json           session state (files, outputs, order)
        uploads/<file_id>.pdf   originals, never modified
        thumbs/<file_id>/       render cache
        outputs/<output_id>_<name>.pdf
"""

import json
import logging
import os
import shutil
import threading
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from app.errors import NotFoundError, ValidationFailed
from app.pdf.info import probe_pdf

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass
class FileRecord:
    file_id: str
    name: str
    size_bytes: int
    page_count: int
    pages: list[dict]  # [{index, width_pt, height_pt, rotation}]
    added_at: str


@dataclass
class OutputRecord:
    output_id: str
    name: str
    size_bytes: int
    created_at: str
    job_id: str


class Workspace:
    def __init__(self, session_id: str, root: Path):
        self.session_id = session_id
        self.root = root
        self.uploads_dir = root / "uploads"
        self.thumbs_dir = root / "thumbs"
        self.outputs_dir = root / "outputs"
        self._manifest_path = root / "manifest.json"
        self._lock = threading.Lock()
        self.files: list[FileRecord] = []
        self.outputs: list[OutputRecord] = []
        self.created_at = _now()

    # ---- persistence -------------------------------------------------------

    @classmethod
    def create(cls, session_id: str, root: Path) -> "Workspace":
        ws = cls(session_id, root)
        for d in (ws.uploads_dir, ws.thumbs_dir, ws.outputs_dir):
            d.mkdir(parents=True, exist_ok=True)
        ws._save()
        return ws

    @classmethod
    def load(cls, session_id: str, root: Path) -> "Workspace":
        ws = cls(session_id, root)
        data = json.loads(ws._manifest_path.read_text(encoding="utf-8"))
        ws.created_at = data.get("created_at", _now())
        ws.files = [FileRecord(**f) for f in data.get("files", [])]
        ws.outputs = [OutputRecord(**o) for o in data.get("outputs", [])]
        for d in (ws.uploads_dir, ws.thumbs_dir, ws.outputs_dir):
            d.mkdir(parents=True, exist_ok=True)
        return ws

    def _save(self) -> None:
        """Atomic manifest write; callers must hold self._lock (or be single-threaded init)."""
        data = {
            "session_id": self.session_id,
            "created_at": self.created_at,
            "files": [asdict(f) for f in self.files],
            "outputs": [asdict(o) for o in self.outputs],
        }
        tmp = self._manifest_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=1), encoding="utf-8")
        os.replace(tmp, self._manifest_path)

    def touch(self) -> None:
        """Mark the session as recently active (manifest mtime drives TTL cleanup)."""
        try:
            os.utime(self._manifest_path)
        except OSError:
            pass

    # ---- files ---------------------------------------------------------------

    def upload_target(self) -> tuple[str, Path]:
        """Reserve a file id and the path where the route should stream the upload."""
        file_id = uuid.uuid4().hex[:12]
        return file_id, self.uploads_dir / f"{file_id}.pdf"

    def finalize_upload(self, file_id: str, original_name: str) -> FileRecord:
        """Probe a streamed upload and register it. Deletes the file on failure."""
        path = self.uploads_dir / f"{file_id}.pdf"
        try:
            info = probe_pdf(path)
        except Exception:
            path.unlink(missing_ok=True)
            raise
        record = FileRecord(
            file_id=file_id,
            name=original_name,
            size_bytes=path.stat().st_size,
            page_count=info.page_count,
            pages=[asdict(p) for p in info.pages],
            added_at=_now(),
        )
        with self._lock:
            self.files.append(record)
            self._save()
        logger.info(
            "Session %s: accepted %s (%d pages, %d bytes)",
            self.session_id, original_name, record.page_count, record.size_bytes,
        )
        return record

    def get_file(self, file_id: str) -> FileRecord:
        for f in self.files:
            if f.file_id == file_id:
                return f
        raise NotFoundError(f"File {file_id} not found in this session.")

    def file_path(self, file_id: str) -> Path:
        self.get_file(file_id)
        return self.uploads_dir / f"{file_id}.pdf"

    def reorder(self, order: list[str]) -> None:
        with self._lock:
            current = {f.file_id for f in self.files}
            if set(order) != current or len(order) != len(self.files):
                raise ValidationFailed("Order must be a permutation of the current file ids.")
            by_id = {f.file_id: f for f in self.files}
            self.files = [by_id[fid] for fid in order]
            self._save()

    def remove_file(self, file_id: str) -> None:
        record = self.get_file(file_id)
        with self._lock:
            self.files = [f for f in self.files if f.file_id != file_id]
            self._save()
        (self.uploads_dir / f"{file_id}.pdf").unlink(missing_ok=True)
        shutil.rmtree(self.thumbs_dir / file_id, ignore_errors=True)
        logger.info("Session %s: removed %s", self.session_id, record.name)

    # ---- outputs ---------------------------------------------------------------

    def reserve_output(self, name: str) -> tuple[str, Path]:
        output_id = uuid.uuid4().hex[:12]
        return output_id, self.outputs_dir / f"{output_id}_{name}"

    def register_output(self, output_id: str, name: str, path: Path, job_id: str) -> OutputRecord:
        record = OutputRecord(
            output_id=output_id,
            name=name,
            size_bytes=path.stat().st_size,
            created_at=_now(),
            job_id=job_id,
        )
        with self._lock:
            self.outputs.append(record)
            self._save()
        return record

    def get_output(self, output_id: str) -> OutputRecord:
        for o in self.outputs:
            if o.output_id == output_id:
                return o
        raise NotFoundError(f"Output {output_id} not found in this session.")

    def output_path(self, output_id: str) -> Path:
        record = self.get_output(output_id)
        return self.outputs_dir / f"{record.output_id}_{record.name}"


class WorkspaceManager:
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self._cache: dict[str, Workspace] = {}
        self._lock = threading.Lock()

    def create_session(self) -> Workspace:
        session_id = uuid.uuid4().hex[:16]
        ws = Workspace.create(session_id, self.base_dir / session_id)
        with self._lock:
            self._cache[session_id] = ws
        logger.info("Created session %s", session_id)
        return ws

    def get(self, session_id: str) -> Workspace:
        with self._lock:
            if session_id in self._cache:
                return self._cache[session_id]
        root = self.base_dir / session_id
        if not (root / "manifest.json").is_file():
            raise NotFoundError("Session not found or expired.")
        ws = Workspace.load(session_id, root)
        with self._lock:
            self._cache[session_id] = ws
        return ws

    def delete(self, session_id: str) -> None:
        with self._lock:
            self._cache.pop(session_id, None)
        shutil.rmtree(self.base_dir / session_id, ignore_errors=True)
        logger.info("Deleted session %s", session_id)

    def cleanup_stale(self, ttl_hours: float) -> int:
        """Remove session dirs whose manifest hasn't been touched within the TTL."""
        cutoff = time.time() - ttl_hours * 3600
        removed = 0
        for entry in self.base_dir.iterdir():
            if not entry.is_dir():
                continue
            manifest = entry / "manifest.json"
            try:
                stale = (not manifest.is_file()) or manifest.stat().st_mtime < cutoff
            except OSError:
                continue
            if stale:
                self.delete(entry.name)
                removed += 1
        if removed:
            logger.info("Cleaned up %d stale session(s)", removed)
        return removed
