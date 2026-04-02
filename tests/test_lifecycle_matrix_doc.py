from pathlib import Path


def test_lifecycle_matrix_documents_active_lifecycle_boundary() -> None:
    text = Path("docs/safety/lifecycle_matrix.md").read_text(encoding="utf-8")

    assert "services/execution/lifecycle_boundary.py" in text
    assert "Routes through `lifecycle_boundary.cancel_order_via_boundary(...)`" in text
    assert "Routes through `lifecycle_boundary.fetch_order_via_boundary(...)`" in text
    assert "Routes through `lifecycle_boundary.fetch_my_trades_via_boundary(...)`" in text
    assert "Active adapter and order-manager cancel/fetch paths now funnel through `services/execution/lifecycle_boundary.py`." in text
    assert "`services/execution/live_executor.py` still performs reconcile fetches through `services/execution/exchange_client.py`." in text
