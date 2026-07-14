from __future__ import annotations

from datetime import datetime, timezone
import importlib

import pytest


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

    def _live_risk_cfg(**kwargs):
        seen["live_risk_cfg_kwargs"] = dict(kwargs)
        return {
            "max_trades_per_day": 3,
            "max_daily_notional_quote": 250.0,
            "min_order_notional_quote": 10.0,
        }

    monkeypatch.setattr(consumer, "live_risk_cfg", _live_risk_cfg)

    ok, reason = consumer._risk_check_and_claim(FakeQueue(), 25.0)

    assert (ok, reason) == (True, None)
    assert seen == {
        "live_risk_cfg_kwargs": {"strict": True},
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

    def _live_risk_cfg(**kwargs):
        seen["live_risk_cfg_kwargs"] = dict(kwargs)
        return {
            "max_trades_per_day": 4,
            "max_daily_notional_quote": 300.0,
            "min_order_notional_quote": 10.0,
        }

    monkeypatch.setattr(consumer, "live_risk_cfg", _live_risk_cfg)

    ok, reason = consumer._risk_check_and_claim(FakeQueue(), 35.0)

    assert (ok, reason) == (True, None)
    assert seen == {
        "live_risk_cfg_kwargs": {"strict": True},
        "max_trades": 4,
        "max_notional": 300.0,
        "notional_est": 35.0,
    }


@pytest.mark.parametrize(
    "module_name",
    [
        "services.execution.live_intent_consumer",
        "services.execution.intent_consumer",
    ],
)
def test_intent_consumers_use_decimal_notional_at_min_order_boundary(module_name, monkeypatch):
    consumer = importlib.import_module(module_name)
    seen: dict[str, object] = {}
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    class FakeQueue:
        def get_state(self, key: str):
            return today if key == "risk:day" else "0"

        def reset_risk_state_for_day(self, day: str):
            raise AssertionError("risk state should not reset for current day")

        def atomic_risk_claim(self, **kwargs):
            seen.update(kwargs)
            return True, None

    def _live_risk_cfg(**kwargs):
        seen["live_risk_cfg_kwargs"] = dict(kwargs)
        return {
            "max_trades_per_day": 0,
            "max_daily_notional_quote": "1.0",
            "min_order_notional_quote": "0.07",
        }

    monkeypatch.setattr(consumer, "live_risk_cfg", _live_risk_cfg)

    notional_est = consumer._intent_notional_estimate(
        {"qty": "0.1", "limit_price": "0.7"},
        {},
    )
    ok, reason = consumer._risk_check_and_claim(FakeQueue(), notional_est)

    assert (ok, reason) == (True, None)
    assert seen["live_risk_cfg_kwargs"] == {"strict": True}
    assert seen["max_trades"] == 0
    assert seen["max_notional"] == "1.0"
    assert str(seen["notional_est"]) == "0.07"


def test_live_intent_consumer_risk_check_fails_closed_on_config_load_error(monkeypatch):
    import services.execution.live_intent_consumer as consumer

    calls: list[str] = []

    class FakeQueue:
        def get_state(self, key: str):
            calls.append(f"get_state:{key}")
            raise AssertionError("risk state should not be read when config is untrusted")

        def reset_risk_state_for_day(self, day: str):
            calls.append(f"reset:{day}")
            raise AssertionError("risk state should not be reset when config is untrusted")

        def atomic_risk_claim(self, **kwargs):
            calls.append("atomic_risk_claim")
            raise AssertionError("atomic claim should not run when config is untrusted")

    def _raise_config_load_error(**kwargs):
        assert kwargs == {"strict": True}
        raise consumer.ConfigLoadError("config_load_failed:/tmp/user.yaml:ScannerError:bad")

    monkeypatch.setattr(consumer, "live_risk_cfg", _raise_config_load_error)

    ok, reason = consumer._risk_check_and_claim(FakeQueue(), 25.0)

    assert (ok, reason) == (False, "risk:config_load_failed")
    assert calls == []


def test_intent_consumer_risk_check_fails_closed_on_config_load_error(monkeypatch):
    import services.execution.intent_consumer as consumer

    calls: list[str] = []

    class FakeQueue:
        def get_state(self, key: str):
            calls.append(f"get_state:{key}")
            raise AssertionError("risk state should not be read when config is untrusted")

        def reset_risk_state_for_day(self, day: str):
            calls.append(f"reset:{day}")
            raise AssertionError("risk state should not be reset when config is untrusted")

        def atomic_risk_claim(self, **kwargs):
            calls.append("atomic_risk_claim")
            raise AssertionError("atomic claim should not run when config is untrusted")

    def _raise_config_load_error(**kwargs):
        assert kwargs == {"strict": True}
        raise consumer.ConfigLoadError("config_load_failed:/tmp/user.yaml:ScannerError:bad")

    monkeypatch.setattr(consumer, "live_risk_cfg", _raise_config_load_error)

    ok, reason = consumer._risk_check_and_claim(FakeQueue(), 35.0)

    assert (ok, reason) == (False, "risk:config_load_failed")
    assert calls == []
