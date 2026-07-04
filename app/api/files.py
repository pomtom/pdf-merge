import logging

from fastapi import APIRouter, Depends, Response, UploadFile
from fastapi.responses import FileResponse

from app.config import get_settings
from app.deps import get_workspace
from app.errors import AppError
from app.models import (
    FileEntry,
    FilesResponse,
    OrderRequest,
    RejectedFile,
    UploadResponse,
)
from app.services.thumbnails import get_thumbnail, snap_width
from app.services.workspace import FileRecord, Workspace

logger = logging.getLogger(__name__)

router = APIRouter(tags=["files"])


def _entry(record: FileRecord) -> FileEntry:
    return FileEntry(
        file_id=record.file_id,
        name=record.name,
        size_bytes=record.size_bytes,
        page_count=record.page_count,
        pages=record.pages,
    )


@router.post("/sessions/{sid}/files", status_code=201, response_model=UploadResponse)
async def upload_files(
    files: list[UploadFile], ws: Workspace = Depends(get_workspace)
) -> UploadResponse:
    settings = get_settings()
    accepted: list[FileEntry] = []
    rejected: list[RejectedFile] = []

    for upload in files:
        name = upload.filename or "unnamed.pdf"
        file_id, target = ws.upload_target()
        try:
            # Stream to disk in 1 MB chunks: peak RAM stays constant no matter
            # how large the file is.
            with open(target, "wb") as fh:
                while chunk := await upload.read(settings.upload_chunk_bytes):
                    fh.write(chunk)
            record = ws.finalize_upload(file_id, name)
            accepted.append(_entry(record))
        except AppError as exc:
            target.unlink(missing_ok=True)
            rejected.append(RejectedFile(name=name, code=exc.code, message=exc.message))
            logger.info("Rejected upload %s: %s", name, exc.message)
        finally:
            await upload.close()

    return UploadResponse(files=accepted, rejected=rejected)


@router.get("/sessions/{sid}/files", response_model=FilesResponse)
def list_files(ws: Workspace = Depends(get_workspace)) -> FilesResponse:
    return FilesResponse(files=[_entry(f) for f in ws.files])


@router.get("/sessions/{sid}/files/{file_id}", response_model=FileEntry)
def get_file(file_id: str, ws: Workspace = Depends(get_workspace)) -> FileEntry:
    return _entry(ws.get_file(file_id))


@router.patch("/sessions/{sid}/files/order", status_code=204)
def reorder_files(body: OrderRequest, ws: Workspace = Depends(get_workspace)) -> Response:
    ws.reorder(body.order)
    return Response(status_code=204)


@router.delete("/sessions/{sid}/files/{file_id}", status_code=204)
def remove_file(file_id: str, ws: Workspace = Depends(get_workspace)) -> Response:
    ws.remove_file(file_id)
    return Response(status_code=204)


@router.get("/sessions/{sid}/files/{file_id}/pages/{page}/thumbnail")
def page_thumbnail(
    file_id: str, page: int, w: int = 160, ws: Workspace = Depends(get_workspace)
) -> FileResponse:
    width = snap_width(w, get_settings().thumb_widths)
    path = get_thumbnail(ws, file_id, page, width)
    return FileResponse(
        path,
        media_type="image/webp",
        headers={"Cache-Control": "max-age=31536000, immutable"},
    )
