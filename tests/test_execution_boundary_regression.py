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
