from pathlib import Path

def test_memory_retrieval_retrieve_route_requires_service_auth() -> None:
    text = Path("phase1_research_copilot/memory_retrieval/main.py").read_text()
    assert 'async def retrieve_context(req: RetrieveRequest, authorization: str | None = Header(default=None, alias="Authorization"))' in text
    assert "_require_service_token(authorization)" in text
