from __future__ import annotations

from fastapi import FastAPI

from services.memory.retrieval.hybrid_search import search_documents
from shared.audit_client import emit_audit_event
from shared.config import get_settings
from shared.db import SessionLocal, check_db_connection
from shared.logging import get_logger
from shared.schemas.documents import DocumentSearchRequest, DocumentSearchResponse

settings = get_settings("memory")
logger = get_logger("memory", settings.log_level)
app = FastAPI(title="memory")


@app.on_event("startup")
def startup() -> None:
    ok = check_db_connection()
    logger.info("startup_db_check", extra={"context": {"ok": ok}})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/search", response_model=DocumentSearchResponse)
async def search(req: DocumentSearchRequest) -> DocumentSearchResponse:
    with SessionLocal() as db:
        results = search_documents(
            db=db,
            settings=settings,
            query=req.query,
            asset=req.asset,
            timeline=req.timeline,
            limit=req.limit,
        )
    await emit_audit_event(
        settings=settings,
        service_name="memory",
        event_type="memory_search",
        message="Memory search completed",
        payload={"asset": req.asset, "query": req.query, "count": len(results)},
    )
    return DocumentSearchResponse(results=results)
