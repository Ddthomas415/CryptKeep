from pathlib import Path

def test_memory_retrieval_routes_require_service_auth() -> None:
    text = Path("phase1_research_copilot/memory_retrieval/main.py").read_text()
    assert "_require_service_token" in text
    assert 'alias="Authorization"' in text
    assert 'detail="unauthorized"' in text
