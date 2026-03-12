from __future__ import annotations

from fastapi import FastAPI

from services.gateway.routes.api_v1 import router as api_v1_router
from services.gateway.routes.live import router as live_router
from services.gateway.routes import query as query_routes
from services.gateway.routes.alerts import router as alerts_router
from services.gateway.routes.health import router as health_router
from services.gateway.routes.paper import router as paper_router
from services.gateway.routes.query import router as query_router
from shared.config import get_settings
from shared.logging import get_logger
from shared.schemas.documents import DocumentSearchRequest, DocumentSearchResponse

settings = get_settings("gateway")
logger = get_logger("gateway", settings.log_level)
app = FastAPI(title="gateway")

app.include_router(health_router)
app.include_router(api_v1_router)
app.include_router(query_router)
app.include_router(paper_router)
app.include_router(live_router)
app.include_router(alerts_router)

logger.info("gateway_started", extra={"context": {"env": settings.app_env}})


@app.post("/documents/search", response_model=DocumentSearchResponse)
async def documents_search(req: DocumentSearchRequest) -> DocumentSearchResponse:
    return await query_routes.documents_search(req)


@app.get("/market/{symbol}/snapshot")
async def market_snapshot(symbol: str) -> dict:
    return await query_routes.market_snapshot(symbol)
