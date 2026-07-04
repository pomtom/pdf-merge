"""Application factory. Run with:  uvicorn app.main:app"""

import asyncio
import logging
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.errors import register_handlers
from app.logging_conf import setup_logging
from app.services.jobs import JobRegistry
from app.services.workspace import WorkspaceManager

logger = logging.getLogger("pdfstudio")

STATIC_DIR = Path(__file__).resolve().parent.parent / "static"


def create_app() -> FastAPI:
    settings = get_settings()
    setup_logging(settings.data_dir)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.workspaces.cleanup_stale(settings.session_ttl_hours)

        async def cleanup_loop():
            while True:
                await asyncio.sleep(3600)
                try:
                    app.state.workspaces.cleanup_stale(settings.session_ttl_hours)
                except Exception:
                    logger.exception("Stale-session cleanup failed")

        task = asyncio.create_task(cleanup_loop())
        logger.info("PDF Studio %s ready at http://%s:%d", __version__, settings.host, settings.port)
        yield
        task.cancel()
        app.state.jobs.shutdown()

    app = FastAPI(title="PDF Studio", version=__version__, lifespan=lifespan)
    app.state.workspaces = WorkspaceManager(settings.data_dir)
    app.state.jobs = JobRegistry(settings.max_workers)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        ms = (time.perf_counter() - start) * 1000
        logging.getLogger("pdfstudio.http").debug(
            "%s %s -> %d (%.1f ms)", request.method, request.url.path, response.status_code, ms
        )
        return response

    register_handlers(app)
    app.include_router(api_router, prefix="/api")
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
