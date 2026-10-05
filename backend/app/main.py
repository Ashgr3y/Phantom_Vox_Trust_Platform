from __future__ import annotations

import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.router import router
from app.core.config import PROJECT_ROOT, get_settings
from app.db.bootstrap import initialize_database
from app.inference.rawnetlite import rawnetlite_adapter


settings = get_settings()


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == 404 and "." not in Path(path).name:
                return await super().get_response("index.html", scope)
            raise


@asynccontextmanager
async def lifespan(_app: FastAPI):
    initialize_database()
    if settings.require_ml:
        rawnetlite_adapter.warmup()
    yield


app = FastAPI(
    title="Phantom Vox Voice Trust API",
    description="Real-time voice-risk orchestration, prevention, verification, incident, and audit APIs.",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


request_buckets: dict[str, deque[float]] = defaultdict(deque)


@app.middleware("http")
async def basic_rate_limit(request: Request, call_next):
    if request.url.path.startswith("/api/v1/health"):
        return await call_next(request)
    address = request.client.host if request.client else "unknown"
    now = time.monotonic()
    bucket = request_buckets[address]
    while bucket and bucket[0] < now - 60:
        bucket.popleft()
    if len(bucket) >= 240:
        return JSONResponse(status_code=429, content={"detail": "Request limit exceeded. Retry in one minute."})
    bucket.append(now)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Permissions-Policy"] = "microphone=(self)"
    return response


@app.exception_handler(Exception)
async def safe_exception_handler(_request: Request, exc: Exception):
    if settings.environment == "development":
        return JSONResponse(status_code=500, content={"detail": "Unexpected server error", "development_message": str(exc)})
    return JSONResponse(status_code=500, content={"detail": "Unexpected server error"})


app.include_router(router)

frontend_dist = PROJECT_ROOT / "frontend" / "dist"
if frontend_dist.exists():
    app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="frontend")
