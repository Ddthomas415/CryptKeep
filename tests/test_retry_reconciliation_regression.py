from pathlib import Path


def test_exchange_client_marks_unknown_and_reconciles() -> None:
    text = Path("services/execution/exchange_client.py").read_text()
    assert "mark_unknown(" in text
    assert "reconcile_ambiguous_submission(" in text
    assert "ambiguous_submit_blocked:" in text


def test_order_router_blocks_retry_without_reconciliation() -> None:
    text = Path("services/execution/order_router.py").read_text()
    assert "reconcile_ambiguous_submission(" in text
    assert "retry_blocked_after_ambiguous_submit:" in text
