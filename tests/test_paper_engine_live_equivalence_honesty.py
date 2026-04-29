from pathlib import Path


def test_paper_engine_documents_same_call_fill_not_live_equivalent():
    doc = Path("docs/PAPER_TRADING_HONESTY.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()

    assert "same submit_order call" in text
    assert "not live-equivalent" in text
    assert "reconciliation" in text
