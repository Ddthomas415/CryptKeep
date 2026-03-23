from pathlib import Path

def test_phase1_shared_config_defines_service_token() -> None:
    text = Path("phase1_research_copilot/shared/config.py").read_text()
    assert 'service_token: str = ""' in text
