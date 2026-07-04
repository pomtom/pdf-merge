from fastapi import APIRouter, Depends, Response

from app.deps import get_manager
from app.services.workspace import WorkspaceManager

router = APIRouter(tags=["sessions"])


@router.post("/sessions", status_code=201)
def create_session(manager: WorkspaceManager = Depends(get_manager)) -> dict:
    ws = manager.create_session()
    return {"session_id": ws.session_id}


@router.delete("/sessions/{sid}", status_code=204)
def delete_session(sid: str, manager: WorkspaceManager = Depends(get_manager)) -> Response:
    manager.get(sid)  # 404 if unknown
    manager.delete(sid)
    return Response(status_code=204)
