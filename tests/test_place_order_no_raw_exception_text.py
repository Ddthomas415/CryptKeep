from pathlib import Path

def test_place_order_does_not_return_raw_exception_text() -> None:
    text = Path("services/execution/place_order.py").read_text()
    assert '"reason": str(exc)' not in text
