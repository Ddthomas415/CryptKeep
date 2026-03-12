from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.app.api.middleware import register_middleware
from backend.app.api.routes import (
    audit,
    connections,
    dashboard,
    health,
    research,
    risk,
    settings,
    terminal,
    trading,
)
from backend.app.core.errors import register_exception_handlers
from backend.app.core.logging import get_logger
from backend.app.core.telemetry import init_telemetry

logger = get_logger("backend.main")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_telemetry()
    logger.info("app_startup")
    yield


app = FastAPI(
    title="Crypto Trading AI",
    version="0.1.0",
    description="Starter backend for a crypto trading AI platform",
    lifespan=lifespan,
)

register_middleware(app)
register_exception_handlers(app)

app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(dashboard.router, prefix="/api/v1/dashboard", tags=["dashboard"])
app.include_router(research.router, prefix="/api/v1/research", tags=["research"])
app.include_router(connections.router, prefix="/api/v1/connections", tags=["connections"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(risk.router, prefix="/api/v1/risk", tags=["risk"])
app.include_router(trading.router, prefix="/api/v1/trading", tags=["trading"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])
app.include_router(terminal.router, prefix="/api/v1/terminal", tags=["terminal"])


@app.get("/")
def root() -> dict:
    return {
        "name": "Crypto Trading AI",
        "status": "ok",
        "docs": "/docs",
    }
