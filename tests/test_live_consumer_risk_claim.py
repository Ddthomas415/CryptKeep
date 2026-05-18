from __future__ import annotations

from datetime import datetime, timezone


def test_live_intent_consumer_risk_check_and_claim_uses_atomic_claim(monkeypatch):
    import services.execution.live_intent_consumer as consumer

    seen: dict[str, object] = {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    class FakeQueue:
        def get_state(self, key: str):
            return today if key == "risk:day" else "0"

        def set_state(self, key: str, value: str):
            raise AssertionError("set_state should not be used by atomic claim path")

        def atomic_risk_claim(self, *, max_trades: int, max_notional: float, notional_est: float):
            seen.update(
                {
                    "max_trades": max_trades,
                    "max_notional": max_notional,
                    "notional_est": notional_est,
                }
            )
            return True, None

    monkeypatch.setattr(
        consumer,
        "live_risk_cfg",
        lambda: {
            "max_trades_per_day": 3,
            "max_daily_notional_quote": 250.0,
            "min_order_notional_quote": 10.0,
        },
    )

    ok, reason = consumer._risk_check_and_claim(FakeQueue(), 25.0)

    assert (ok, reason) == (True, None)
    assert seen == {
        "max_trades": 3,
        "max_notional": 250.0,
        "notional_est": 25.0,
    }


def test_intent_consumer_risk_check_and_claim_uses_atomic_claim(monkeypatch):
    import services.execution.intent_consumer as consumer

    seen: dict[str, object] = {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    class FakeQueue:
        def get_state(self, key: str):
            return today if key == "risk:day" else "0"

        def set_state(self, key: str, value: str):
            raise AssertionError("set_state should not be used by atomic claim path")

        def atomic_risk_claim(self, *, max_trades: int, max_notional: float, notional_est: float):
            seen.update(
                {
                    "max_trades": max_trades,
                    "max_notional": max_notional,
                    "notional_est": notional_est,
                }
            )
            return True, None

    monkeypatch.setattr(
        consumer,
        "live_risk_cfg",
        lambda: {
            "max_trades_per_day": 4,
            "max_daily_notional_quote": 300.0,
            "min_order_notional_quote": 10.0,
        },
    )

    ok, reason = consumer._risk_check_and_claim(FakeQueue(), 35.0)

    assert (ok, reason) == (True, None)
    assert seen == {
        "max_trades": 4,
        "max_notional": 300.0,
        "notional_est": 35.0,
    }
