"""Audit reproductions of current behavior, not acceptance tests for a repair."""

import inspect
import smtplib
import sqlite3
import ssl

import pytest

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.backtest.ohlcv_archive import normalize_ohlcv_rows
from services.execution.runner_decision import select_exit_decision
from services.feature_gate import proba_gate
from services.risk.exposure_controls import summarize_exposure
from services.risk.position_scaling import evaluate_scale_in
from services.risk import system_health


@pytest.mark.parametrize("strategy", ["breakout", "ema_cross", "mean_reversion_rsi"])
@pytest.mark.parametrize("position_aware", [True, False])
def test_held_buy_depends_on_upstream_guard(strategy, position_aware):
    cfg = dict(strategy_id=strategy, position_aware=position_aware,
               stop_loss_pct=3, take_profit_pct=6, trailing_stop_pct=2,
               max_bars_hold=60)
    result = select_exit_decision(
        cfg=cfg, signal={"action": "buy", "ok": True}, decision="buy",
        changed=True, pos_qty=1, entry_price=100, trailing_peak_price=102,
        bars_held=1, current_price=102,
    )
    assert result["action"] == (None if position_aware else "buy")


def test_disabled_scaling_does_not_identify_a_scale():
    result = evaluate_scale_in(
        position_summary={"has_position": True, "pnl_pct": 2}, adds_used=99,
        limits={"enable_position_scaling": False},
    )
    assert result["ok"] is False
    assert result["is_scale"] is False


def test_paper_row_without_percent_fields_reports_zero_exposure():
    result = summarize_exposure(
        positions=[{"symbol": "X/USD", "qty": 100, "avg_price": 200}],
        strategy_name="breakout",
    )
    assert result["concurrent_positions"] == 1
    assert result["total_exposure_pct"] == 0
    assert result["per_symbol_pct"] == {"X/USD": 0}


@pytest.mark.parametrize("raw,buy,sell", [(None, False, False), ("nan", True, False)])
def test_opt_in_probability_gate_missing_and_nan(monkeypatch, raw, buy, sell):
    monkeypatch.delenv("CBP_FUSED_PROBA", raising=False)
    if raw is not None:
        monkeypatch.setenv("CBP_FUSED_PROBA", raw)
    assert proba_gate(scope="audit", side="buy", use_fused=True).ok is buy
    assert proba_gate(scope="audit", side="sell", use_fused=True).ok is sell
    assert proba_gate(scope="audit", side="sell", use_fused=False).ok is True


@pytest.mark.parametrize("close", [0, -1])
def test_archive_keeps_finite_nonpositive_close(close):
    rows = [[1700000000000, 1, 1, 1, close, 1]]
    assert normalize_ohlcv_rows(rows)[0][4] == close
    assert normalize_ohlcv_rows([[1700000000000, 1, 1, 1, float("nan"), 1]]) == []


def test_missing_daily_table_silences_accounting_check(tmp_path, monkeypatch):
    path = tmp_path / "synthetic.sqlite"
    with sqlite3.connect(path) as con:
        con.execute("CREATE TABLE canonical_fills (venue TEXT, fill_id TEXT)")
        con.execute("INSERT INTO canonical_fills VALUES ('synthetic', 'one')")
    monkeypatch.setattr(system_health, "_exec_db", lambda: str(path))
    assert system_health._check_accounting_invariant() is None


def test_local_stdlib_default_starttls_context_is_unverified():
    assert "ssl._create_stdlib_context()" in inspect.getsource(smtplib.SMTP.starttls)
    context = ssl._create_stdlib_context()
    assert context.verify_mode == ssl.CERT_NONE
    assert context.check_hostname is False


def test_journal_gross_win_can_be_net_loss_with_open_buy_fee():
    result = fifo_pnl_from_fills([
        dict(symbol="X", side="buy", qty=1, price=100, fee=.5, fill_ts="1"),
        dict(symbol="X", side="sell", qty=1, price=100.25, fee=.5, fill_ts="2"),
        dict(symbol="Y", side="buy", qty=1, price=50, fee=.25, fill_ts="3"),
    ])
    assert result["summary"]["win_rate"] == 1
    assert result["closed_trades"][0]["net_pnl"] == -.75
    assert result["summary"]["net_realized_pnl"] == -1


def test_daily_loss_failure_is_not_propagated_by_sink(tmp_path, monkeypatch):
    from services.journal import fill_sink
    from services.risk.risk_daily import RiskDailyDB

    flags = []
    monkeypatch.setattr(fill_sink, "_write_risk_sink_failed", lambda *args: flags.append(args))

    def fail_inside_transaction(*args, **kwargs):
        raise sqlite3.OperationalError("synthetic write failure")

    monkeypatch.setattr(RiskDailyDB, "_apply_pnl_conn", fail_inside_transaction)
    path = str(tmp_path / "execution.sqlite")
    sink = fill_sink.CanonicalFillSink(exec_db=path)
    result = sink.on_fill(dict(
        venue="synthetic", fill_id="one", symbol="X/USD", side="sell",
        qty=1, price=99, realized_pnl_usd=-1, fee_usd=.5,
        ts="2026-11-05T00:00:00Z",
    ))
    assert result == {"ok": True}
    assert flags == []
    with sqlite3.connect(path) as con:
        assert con.execute("SELECT COUNT(*) FROM risk_daily_fills").fetchone()[0] == 0


def test_nan_stability_keeps_allocator_base_weight(monkeypatch):
    from services.control import allocator

    monkeypatch.setattr(allocator, "get_current_stage", lambda _: allocator.Stage.CAPPED_LIVE)
    monkeypatch.setattr(allocator, "max_allocation_frac", lambda _: .25)
    assert allocator.compute_allocation("synthetic", regime_stability=float("nan")) == .1
    assert allocator.compute_allocation("synthetic", regime_stability=0) == 0
