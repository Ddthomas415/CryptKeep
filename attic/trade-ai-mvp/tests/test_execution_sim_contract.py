import asyncio

import pytest
from fastapi import HTTPException

pytest.importorskip("sqlalchemy")

from services.execution_sim import app as execution_sim_app
from shared.schemas.paper import PaperOrderCreateRequest


def test_execution_sim_rejects_order_when_paper_trading_disabled(monkeypatch):
    monkeypatch.setattr(execution_sim_app.settings, "paper_trading_enabled", False)
    req = PaperOrderCreateRequest(symbol="SOL-USD", side="buy", order_type="market", quantity=1.0)
    with pytest.raises(HTTPException) as err:
        asyncio.run(execution_sim_app.submit_paper_order(req))
    assert err.value.status_code == 403
    assert err.value.detail == "paper trading disabled"


def test_execution_sim_symbol_normalization():
    assert execution_sim_app._normalize_symbol("sol") == "SOL-USD"
    assert execution_sim_app._normalize_symbol("eth/usd") == "ETH-USD"
    assert execution_sim_app._normalize_symbol("BTC-USD") == "BTC-USD"


def test_execution_sim_requested_action_classifier():
    assert (
        execution_sim_app._requested_action_for_order(
            side="buy",
            current_qty=execution_sim_app.Decimal("1"),
            order_qty=execution_sim_app.Decimal("0.2"),
        )
        == "open_position"
    )


def test_execution_sim_parse_dt_cursor_valid():
    out = execution_sim_app._parse_dt_cursor("2026-03-10T21:00:00Z")
    assert out.isoformat().startswith("2026-03-10T21:00:00")


def test_execution_sim_parse_dt_cursor_invalid():
    with pytest.raises(HTTPException) as err:
        execution_sim_app._parse_dt_cursor("not-a-time")
    assert err.value.status_code == 400


def test_execution_sim_normalize_rollup_interval():
    assert execution_sim_app._normalize_rollup_interval("hourly") == "hourly"
    assert execution_sim_app._normalize_rollup_interval("daily") == "daily"
    with pytest.raises(HTTPException) as err:
        execution_sim_app._normalize_rollup_interval("weekly")
    assert err.value.status_code == 400


def test_execution_sim_bucket_start():
    ts = execution_sim_app.datetime(2026, 3, 10, 21, 47, 33, tzinfo=execution_sim_app.timezone.utc)
    hourly = execution_sim_app._bucket_start(ts, "hourly")
    daily = execution_sim_app._bucket_start(ts, "daily")
    assert hourly.isoformat() == "2026-03-10T21:00:00+00:00"
    assert daily.isoformat() == "2026-03-10T00:00:00+00:00"


def test_execution_sim_drawdown_metrics():
    peak, trough, dd_usd, dd_pct = execution_sim_app._drawdown_metrics(
        [
            execution_sim_app.Decimal("100"),
            execution_sim_app.Decimal("120"),
            execution_sim_app.Decimal("90"),
            execution_sim_app.Decimal("110"),
        ]
    )
    assert peak == execution_sim_app.Decimal("120")
    assert trough == execution_sim_app.Decimal("90")
    assert dd_usd == execution_sim_app.Decimal("30")
    assert dd_pct > execution_sim_app.Decimal("20")


def test_execution_sim_return_pct():
    out = execution_sim_app._return_pct(execution_sim_app.Decimal("100"), execution_sim_app.Decimal("125"))
    assert out == execution_sim_app.Decimal("25")
    assert execution_sim_app._return_pct(execution_sim_app.Decimal("0"), execution_sim_app.Decimal("125")) is None


def test_execution_sim_equity_returns_and_hit_rate():
    equities = [
        execution_sim_app.Decimal("100"),
        execution_sim_app.Decimal("110"),
        execution_sim_app.Decimal("105"),
        execution_sim_app.Decimal("120"),
    ]
    returns = execution_sim_app._equity_returns(equities)
    assert len(returns) == 3
    hit_rate = execution_sim_app._hit_rate(returns)
    assert hit_rate is not None
    assert hit_rate > execution_sim_app.Decimal("60")


def test_execution_sim_sharpe_proxy():
    returns = [
        execution_sim_app.Decimal("0.01"),
        execution_sim_app.Decimal("0.015"),
        execution_sim_app.Decimal("-0.002"),
        execution_sim_app.Decimal("0.008"),
    ]
    sharpe = execution_sim_app._sharpe_proxy(returns)
    assert sharpe is not None
    assert sharpe > execution_sim_app.Decimal("0")


def test_execution_sim_phase3_window_gate():
    monkey_days = execution_sim_app.settings.paper_min_performance_days
    monkey_points = execution_sim_app.settings.paper_min_performance_points
    execution_sim_app.settings.paper_min_performance_days = 7
    execution_sim_app.settings.paper_min_performance_points = 24
    try:
        ok, reason = execution_sim_app._phase3_window_gate(observed_days=8.0, observed_points=30)
        assert ok is True
        assert reason == "window_requirements_met"
        ok, reason = execution_sim_app._phase3_window_gate(observed_days=2.0, observed_points=30)
        assert ok is False
        assert reason == "insufficient_paper_days"
        ok, reason = execution_sim_app._phase3_window_gate(observed_days=8.0, observed_points=10)
        assert ok is False
        assert reason == "insufficient_paper_points"
    finally:
        execution_sim_app.settings.paper_min_performance_days = monkey_days
        execution_sim_app.settings.paper_min_performance_points = monkey_points


def test_execution_sim_metrics_text_contains_rejection_and_histogram():
    execution_sim_app._METRICS["paper_order_attempt_total"] = 0
    execution_sim_app._METRICS["paper_order_submit_total"] = 0
    execution_sim_app._METRICS["paper_order_reject_total"] = {}
    execution_sim_app._METRICS["paper_order_latency_seconds"] = []

    execution_sim_app._record_order_attempt()
    execution_sim_app._record_order_attempt()
    execution_sim_app._record_order_submit()
    execution_sim_app._record_order_reject("paper trading disabled")
    execution_sim_app._record_order_latency(0.12)
    execution_sim_app._record_order_latency(0.28)

    text = execution_sim_app._metrics_text()
    assert "paper_order_attempt_total 2" in text
    assert "paper_order_submit_total 1" in text
    assert 'paper_order_reject_total{reason="paper_trading_disabled"} 1' in text
    assert 'paper_order_latency_seconds_bucket{le="0.25"} 1' in text
    assert "paper_order_latency_seconds_count 2" in text


def test_execution_sim_metrics_endpoint_returns_text():
    resp = execution_sim_app.metrics()
    assert resp.status_code == 200
    assert b"paper_order_attempt_total" in resp.body


def test_execution_sim_replay_run_helper():
    prices = [
        execution_sim_app.Decimal("100"),
        execution_sim_app.Decimal("101"),
        execution_sim_app.Decimal("103"),
        execution_sim_app.Decimal("102"),
        execution_sim_app.Decimal("104"),
    ]
    gross, dd, trades = execution_sim_app._replay_run(prices=prices, entry_bps=50.0, hold_steps=1)
    assert trades >= 1
    assert gross is not None
    assert dd is not None


def test_execution_sim_order_request_supports_attribution_fields():
    req = PaperOrderCreateRequest(
        symbol="SOL-USD",
        side="buy",
        order_type="market",
        quantity=1.0,
        signal_source="regime_model_v1",
        rationale="Breakout + volume confirmation",
        catalyst_tags=["governance", "roadmap"],
    )
    assert req.signal_source == "regime_model_v1"
    assert req.rationale.startswith("Breakout")
    assert req.catalyst_tags == ["governance", "roadmap"]


def test_execution_sim_benchmark_basket_no_data():
    class _NoRows:
        def scalar_one_or_none(self):
            return None

    class _DummyDB:
        def execute(self, stmt):
            _ = stmt
            return _NoRows()

    name, ret = execution_sim_app._benchmark_basket_return_pct(
        _DummyDB(),
        start_ts=execution_sim_app.datetime(2026, 3, 10, 0, 0, tzinfo=execution_sim_app.timezone.utc),
        end_ts=execution_sim_app.datetime(2026, 3, 10, 1, 0, tzinfo=execution_sim_app.timezone.utc),
    )
    assert name is None
    assert ret is None


def test_execution_sim_requested_action_classifier_for_sell():
    assert (
        execution_sim_app._requested_action_for_order(
            side="sell",
            current_qty=execution_sim_app.Decimal("1"),
            order_qty=execution_sim_app.Decimal("0.2"),
        )
        == "reduce_position"
    )
    assert (
        execution_sim_app._requested_action_for_order(
            side="sell",
            current_qty=execution_sim_app.Decimal("0"),
            order_qty=execution_sim_app.Decimal("0.2"),
        )
        == "open_position"
    )
