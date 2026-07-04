"""FastAPI dependencies wiring routes to the app-level singletons."""

from fastapi import Request

from app.services.jobs import JobRegistry
from app.services.workspace import Workspace, WorkspaceManager


def get_manager(request: Request) -> WorkspaceManager:
    return request.app.state.workspaces


def get_registry(request: Request) -> JobRegistry:
    return request.app.state.jobs


def get_workspace(sid: str, request: Request) -> Workspace:
    ws = get_manager(request).get(sid)
    ws.touch()
    return ws
