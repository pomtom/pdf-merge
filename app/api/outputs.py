from dataclasses import asdict

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from app.deps import get_workspace
from app.errors import NotFoundError
from app.models import OutputsResponse
from app.services.workspace import Workspace

router = APIRouter(tags=["outputs"])


@router.get("/sessions/{sid}/outputs", response_model=OutputsResponse)
def list_outputs(ws: Workspace = Depends(get_workspace)) -> OutputsResponse:
    return OutputsResponse(outputs=[asdict(o) for o in ws.outputs])


@router.get("/sessions/{sid}/outputs/{output_id}/download")
def download_output(output_id: str, ws: Workspace = Depends(get_workspace)) -> FileResponse:
    record = ws.get_output(output_id)
    path = ws.output_path(output_id)
    if not path.is_file():
        raise NotFoundError("Output file no longer exists.")
    return FileResponse(path, media_type="application/pdf", filename=record.name)
