from pathlib import Path

def test_gateway_chat_route_requires_service_auth() -> None:
    text = Path("phase1_research_copilot/gateway/main.py").read_text()
    assert "_require_service_token" in text
    assert 'alias="Authorization"' in text
    assert 'detail="unauthorized"' in text
