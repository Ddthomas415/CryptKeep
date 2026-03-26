from fastapi import APIRouter, Depends, Request

from backend.app.api.deps import require_min_role
from backend.app.core.envelopes import success
from backend.app.domain.policy.roles import Role
from backend.app.schemas.common import ApiEnvelope
from backend.app.schemas.research import (
    ExplainRequest,
    ExplainResponse,
    ResearchSearchResponse,
    SearchRequest,
)
from backend.app.services.research_service import ResearchService

router = APIRouter()
service = ResearchService()


@router.post("/explain", response_model=ApiEnvelope[ExplainResponse], dependencies=[Depends(require_min_role(Role.VIEWER))])
def research_explain(payload: ExplainRequest, request: Request) -> dict:
    data = service.explain(asset=payload.asset, question=payload.question)
    return success(data=data, request_id=request.state.request_id)


@router.post("/search", response_model=ApiEnvelope[ResearchSearchResponse], dependencies=[Depends(require_min_role(Role.VIEWER))])
def research_search(payload: SearchRequest, request: Request) -> dict:
    data = service.search(query=payload.query, asset=payload.asset)
    return success(
        data=data,
        meta={"page": payload.page, "page_size": payload.page_size, "total": len(data["items"])},
        request_id=request.state.request_id,
    )


# Backward aliases for direct-function tests that import route functions by old names.
explain = research_explain
search = research_search
