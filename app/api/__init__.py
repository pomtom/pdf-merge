from fastapi import APIRouter

from app import __version__
from app.api import files, jobs, outputs, sessions

api_router = APIRouter()


@api_router.get("/health")
def health() -> dict:
    return {"status": "ok", "version": __version__}


api_router.include_router(sessions.router)
api_router.include_router(files.router)
api_router.include_router(jobs.router)
api_router.include_router(outputs.router)
