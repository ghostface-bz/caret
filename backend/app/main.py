"""FastAPI application entrypoint."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import scans
from app.db import Base, engine

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Secure Code Reviewer API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup() -> None:
    """Ensure tables exist.

    Alembic migrations (see backend/alembic/) are the preferred path and are
    run via `alembic upgrade head`. `create_all` is a safety net so the app
    also works if migrations haven't been applied yet (idempotent: it only
    creates missing tables/types).
    """
    Base.metadata.create_all(bind=engine)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(scans.router, prefix="/api")
