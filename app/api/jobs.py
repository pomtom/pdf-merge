from fastapi import APIRouter, Depends

from app.deps import get_registry, get_workspace
from app.errors import ValidationFailed
from app.models import (
    ExtractRequest,
    JobCreated,
    JobProgress,
    JobStatus,
    MergeRequest,
    PageOp,
    SplitRequest,
)
from app.pdf import engine
from app.pdf.engine import SourcePages
from app.services.jobs import JobRegistry
from app.services.workspace import Workspace

router = APIRouter(tags=["jobs"])


def _validate_pages(ws: Workspace, file_id: str, pages: list[PageOp]) -> list[tuple[int, int]]:
    record = ws.get_file(file_id)
    for op in pages:
        if op.index >= record.page_count:
            raise ValidationFailed(
                f"Page {op.index + 1} does not exist in {record.name} "
                f"({record.page_count} pages)."
            )
    return [(op.index, op.rotate) for op in pages]


@router.post("/sessions/{sid}/jobs/merge", status_code=202, response_model=JobCreated)
def start_merge(
    body: MergeRequest,
    ws: Workspace = Depends(get_workspace),
    registry: JobRegistry = Depends(get_registry),
) -> JobCreated:
    items = []
    for item in body.items:
        path = ws.file_path(item.file_id)  # 404s on unknown id before the job starts
        pages = None if item.pages is None else _validate_pages(ws, item.file_id, item.pages)
        if pages is not None and not pages:
            continue  # a file with every page deselected contributes nothing
        items.append(SourcePages(path=path, pages=pages))
    if not items:
        raise ValidationFailed("No pages selected to merge.")

    output_id, out_path = ws.reserve_output(body.output_name)

    def run(job, progress_cb) -> list[dict]:
        try:
            engine.merge_pdfs(items, out_path, progress_cb)
        except Exception:
            out_path.unlink(missing_ok=True)  # never leave partial outputs
            raise
        record = ws.register_output(output_id, body.output_name, out_path, job.id)
        return [{"output_id": record.output_id, "name": record.name,
                 "size_bytes": record.size_bytes}]

    job = registry.submit(ws.session_id, "merge", run)
    return JobCreated(job_id=job.id)


@router.post("/sessions/{sid}/jobs/split", status_code=202, response_model=JobCreated)
def start_split(
    body: SplitRequest,
    ws: Workspace = Depends(get_workspace),
    registry: JobRegistry = Depends(get_registry),
) -> JobCreated:
    path = ws.file_path(body.file_id)

    def run(job, progress_cb) -> list[dict]:
        paths = engine.split_pdf(
            path,
            body.mode,
            ws.outputs_dir,
            f"{job.id}_{body.output_basename}",
            progress_cb,
            ranges=body.ranges,
            chunk_size=body.chunk_size,
        )
        results = []
        for p in paths:
            # split writes files named <job_id>_<basename>_<label>.pdf; expose
            # them under the friendly name without the job prefix
            friendly = p.name.removeprefix(f"{job.id}_")
            output_id, final = ws.reserve_output(friendly)
            p.rename(final)
            record = ws.register_output(output_id, friendly, final, job.id)
            results.append({"output_id": record.output_id, "name": record.name,
                            "size_bytes": record.size_bytes})
        return results

    job = registry.submit(ws.session_id, "split", run)
    return JobCreated(job_id=job.id)


@router.post("/sessions/{sid}/jobs/extract", status_code=202, response_model=JobCreated)
def start_extract(
    body: ExtractRequest,
    ws: Workspace = Depends(get_workspace),
    registry: JobRegistry = Depends(get_registry),
) -> JobCreated:
    path = ws.file_path(body.file_id)
    pages = _validate_pages(ws, body.file_id, body.pages)
    output_id, out_path = ws.reserve_output(body.output_name)

    def run(job, progress_cb) -> list[dict]:
        try:
            engine.extract_pages(path, pages, out_path, progress_cb)
        except Exception:
            out_path.unlink(missing_ok=True)
            raise
        record = ws.register_output(output_id, body.output_name, out_path, job.id)
        return [{"output_id": record.output_id, "name": record.name,
                 "size_bytes": record.size_bytes}]

    job = registry.submit(ws.session_id, "extract", run)
    return JobCreated(job_id=job.id)


@router.get("/sessions/{sid}/jobs/{job_id}", response_model=JobStatus)
def job_status(
    job_id: str,
    ws: Workspace = Depends(get_workspace),
    registry: JobRegistry = Depends(get_registry),
) -> JobStatus:
    job = registry.get(ws.session_id, job_id)
    return JobStatus(
        job_id=job.id,
        kind=job.kind,
        status=job.status,
        progress=JobProgress(current=job.current, total=job.total, message=job.message),
        error=job.error,
        outputs=job.outputs,
    )
