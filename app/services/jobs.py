"""In-memory background job registry running PDF work on a thread pool."""

import logging
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable

from app.errors import AppError, NotFoundError

logger = logging.getLogger(__name__)

# A job function receives its Job (for the id) and a progress callback
# (current, total, message), and returns the list of output dicts to expose
# on the finished job.
ProgressCb = Callable[[int, int, str], None]
JobFn = Callable[["Job", ProgressCb], list[dict]]


@dataclass
class Job:
    id: str
    session_id: str
    kind: str
    status: str = "queued"  # queued | running | done | error
    current: int = 0
    total: int = 0
    message: str = ""
    error: dict | None = None
    outputs: list[dict] = field(default_factory=list)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


class JobRegistry:
    def __init__(self, max_workers: int):
        self._jobs: dict[str, Job] = {}
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers, thread_name_prefix="pdfjob"
        )

    def submit(self, session_id: str, kind: str, fn: JobFn) -> Job:
        job = Job(id=uuid.uuid4().hex[:12], session_id=session_id, kind=kind)
        with self._lock:
            self._jobs[job.id] = job
        self._executor.submit(self._run, job, fn)
        logger.info("Job %s (%s) queued for session %s", job.id, kind, session_id)
        return job

    def _run(self, job: Job, fn: JobFn) -> None:
        def progress_cb(current: int, total: int, message: str) -> None:
            job.current, job.total, job.message = current, total, message

        job.status = "running"
        try:
            job.outputs = fn(job, progress_cb)
            job.status = "done"
            job.message = "Completed"
            logger.info("Job %s finished with %d output(s)", job.id, len(job.outputs))
        except AppError as exc:
            job.error = {"code": exc.code, "message": exc.message}
            job.status = "error"
            logger.warning("Job %s failed: %s", job.id, exc.message)
        except Exception as exc:
            job.error = {"code": "job_failed", "message": f"Operation failed: {exc}"}
            job.status = "error"
            logger.exception("Job %s crashed", job.id)

    def get(self, session_id: str, job_id: str) -> Job:
        job = self._jobs.get(job_id)
        if job is None or job.session_id != session_id:
            raise NotFoundError("Job not found.")
        return job

    def shutdown(self) -> None:
        self._executor.shutdown(wait=False, cancel_futures=True)
