"""FastAPI Application Entrypoint

Initializes the API server, middleware, routes, and exception handlers.
In production (or when frontend/dist exists), also serves the built React dashboard
so judges can open a single public URL.
"""

from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.config import settings
from backend.app.core.logging import logger

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Intelligent EV Fleet Energy & Optimization Platform",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Logs incoming HTTP requests and response status codes."""
    logger.debug(f"HTTP {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        return response
    except Exception as exc:
        logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred while processing the request.",
                "status_code": 500,
            },
        )


@app.get("/health", tags=["Health"])
async def root_health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Include V1 Router
from backend.app.api.v1.router import api_v1_router

app.include_router(api_v1_router)

# Serve the Vite production build when present (Docker / Render / local prod mode).
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FRONTEND_DIST = _REPO_ROOT / "frontend" / "dist"
_FRONTEND_INDEX = _FRONTEND_DIST / "index.html"
_API_PREFIXES = ("/api", "/docs", "/redoc", "/openapi.json", "/health")


def _is_api_or_docs_path(path: str) -> bool:
    return path == "/health" or any(
        path == prefix or path.startswith(prefix + "/") for prefix in _API_PREFIXES
    )


if _FRONTEND_DIST.is_dir() and _FRONTEND_INDEX.is_file():
    _assets_dir = _FRONTEND_DIST / "assets"
    if _assets_dir.is_dir():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="frontend_assets")

    @app.get("/")
    async def serve_frontend_root():
        return FileResponse(_FRONTEND_INDEX)

    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        """Serve static files or fall back to index.html for the SPA shell."""
        request_path = f"/{full_path}"
        if _is_api_or_docs_path(request_path):
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"detail": "Not Found"},
            )

        candidate = (_FRONTEND_DIST / full_path).resolve()
        try:
            candidate.relative_to(_FRONTEND_DIST.resolve())
        except ValueError:
            return FileResponse(_FRONTEND_INDEX)

        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(_FRONTEND_INDEX)

    logger.info("Frontend static build mounted from %s", _FRONTEND_DIST)

