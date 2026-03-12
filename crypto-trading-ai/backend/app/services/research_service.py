from backend.app.schemas.research import ExplainResponse, ResearchSearchItem


class ResearchService:
    def explain(self, asset: str, question: str) -> dict:
        return ExplainResponse.example(asset=asset, question=question)

    def search(self, query: str, asset: str | None = None) -> dict:
        items = [
            ResearchSearchItem(
                id="doc_1",
                type="document",
                source="newsapi",
                title=f"Recent context for {asset or 'market'}",
                summary=f"Mock search result for query: {query}",
                timeline="present",
                timestamp="2026-03-11T12:40:00Z",
                confidence=0.73,
                relevance=0.82,
            ).model_dump()
        ]
        return {"items": items}


def explain(request) -> ExplainResponse:
    service = ResearchService()
    data = service.explain(asset=request.asset, question=request.question)
    return ExplainResponse(**data)


def search(query: str) -> dict:
    service = ResearchService()
    return service.search(query=query)
