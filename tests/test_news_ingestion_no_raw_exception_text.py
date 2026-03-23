from pathlib import Path

def test_news_ingestion_does_not_log_or_audit_raw_exception_text() -> None:
    text = Path("phase1_research_copilot/news_ingestion/main.py").read_text()
    assert 'str(exc)' not in text
    assert '"error_type": type(exc).__name__' in text
