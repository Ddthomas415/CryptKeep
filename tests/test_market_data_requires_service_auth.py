from pathlib import Path

def test_market_data_latest_route_requires_service_auth() -> None:
    text = Path("phase1_research_copilot/market_data/main.py").read_text()
    assert "_require_service_token" in text
    assert 'alias="Authorization"' in text
    assert 'detail="unauthorized"' in text
