"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .config import get_settings
from .db import initialize_database

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


settings = get_settings()
app = FastAPI(title="ModelSwitch Chat", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.allowed_origins),
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Simulate-Failure"],
)


@app.exception_handler(Exception)
async def unexpected_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    logger.exception(
        "Unhandled error while handling %s %s", request.method, request.url.path
    )
    return JSONResponse(status_code=500, content={"detail": "internal server error"})


@app.get("/health")
async def health() -> dict[str, object]:
    return {
        "status": "ok",
        "keys_configured": len(settings.llm_api_keys),
        "cache_enabled": settings.cache_enabled,
    }
