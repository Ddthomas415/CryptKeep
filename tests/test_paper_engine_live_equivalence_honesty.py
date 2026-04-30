from pathlib import Path


def test_paper_engine_documents_explicit_fill_evaluation_not_live_equivalent():
    doc = Path("docs/PAPER_TRADING_HONESTY.md")
    assert doc.exists()
    text = doc.read_text(encoding="utf-8").lower()

    assert "evaluate_open_orders()" in text
    assert "market-quality" in text
    assert "read-only" in text
    assert "deterministic safety" in text
    assert "cash/position adequacy" in text
    assert "not live-equivalent" in text
    assert "reconciliation" in text
