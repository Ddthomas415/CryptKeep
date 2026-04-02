from pathlib import Path


def test_intent_executor_no_direct_adapter_place_order() -> None:
    text = Path("services/execution/intent_executor.py").read_text()
    assert "adapter.place_order(req)" not in text
    assert "adapter.submit_order(" in text


def test_live_paths_use_centralized_submit_boundary() -> None:
    intent_consumer = Path("services/execution/intent_consumer.py").read_text()
    live_intent_consumer = Path("services/execution/live_intent_consumer.py").read_text()
    live_executor = Path("services/execution/live_executor.py").read_text()
    exchange_client = Path("services/execution/exchange_client.py").read_text()
    live_adapter = Path("services/execution/live_exchange_adapter.py").read_text()

    assert "ad.submit_order(" in intent_consumer
    assert "ad.submit_order(" in live_intent_consumer
    assert "client.submit_order(" in live_executor
    assert "place_order(" in exchange_client
    assert "place_order(" in live_adapter


def test_active_adapter_lifecycle_paths_use_centralized_lifecycle_boundary() -> None:
    lifecycle_boundary = Path("services/execution/lifecycle_boundary.py").read_text()
    live_adapter = Path("services/execution/live_exchange_adapter.py").read_text()
    order_manager = Path("services/execution/order_manager.py").read_text()
    live_reconciler = Path("services/execution/live_reconciler.py").read_text()

    assert "def cancel_order_via_boundary(" in lifecycle_boundary
    assert "def fetch_order_via_boundary(" in lifecycle_boundary
    assert "def fetch_my_trades_via_boundary(" in lifecycle_boundary

    assert "cancel_order_via_boundary(" in live_adapter
    assert "fetch_order_via_boundary(" in live_adapter
    assert "fetch_my_trades_via_boundary(" in live_adapter
    assert "self.ex.cancel_order(" not in live_adapter
    assert "self.ex.fetch_order(" not in live_adapter
    assert "self.ex.fetch_my_trades(" not in live_adapter

    assert "cancel_order_async_via_boundary(" in order_manager
    assert "await ex.cancel_order(" not in order_manager

    assert "ad.fetch_order(" in live_reconciler
    assert "ad.fetch_my_trades(" in live_reconciler
    assert "_adapter_for_reconcile_pass(" in live_reconciler
    assert "_system_guard_reconcile_mode()" in live_reconciler


def test_live_executor_reconcile_paths_use_boundary_fetches_with_shared_session() -> None:
    live_executor = Path("services/execution/live_executor.py").read_text()

    assert "fetch_order_via_boundary(" in live_executor
    assert "fetch_my_trades_via_boundary(" in live_executor
    assert "_open_reconcile_session(client)" in live_executor
    assert "client.fetch_open_orders(symbol=sym)" in live_executor
