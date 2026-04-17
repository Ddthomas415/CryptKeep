"""tests/test_live_risk_gates.py

Tests for services/risk/live_risk_gates_phase82.py — the actual live halt enforcement.

This is the code that blocks orders in production. A bug here means:
- Trades that exceed the daily loss limit are not blocked
- Kill switch is ignored
- Notional cap is bypassed
"""
from __future__ import annotations
import pytest
import tempfile, os
from pathlib import Path

from services.risk.live_risk_gates_phase82 import (
    LiveRiskLimits, LiveGateDB, LiveRiskGates
)



def _make_gate(tmp_path: Path, **limit_kwargs) -> LiveRiskGates:
    db_path = str(tmp_path / "test_exec.sqlite")
    db = LiveGateDB(exec_db=db_path)
    # Explicitly set kill_switch_file to a nonexistent path so the file check
    # never fires unexpectedly. Tests that need to test the file path do so explicitly.
    limits = LiveRiskLimits(
        max_daily_loss_usd=limit_kwargs.get("max_daily_loss_usd", 100.0),
        max_notional_per_trade_usd=limit_kwargs.get("max_notional_per_trade_usd", 500.0),
        max_trades_per_day=limit_kwargs.get("max_trades_per_day", 5),
        max_position_notional_usd=limit_kwargs.get("max_position_notional_usd", 1000.0),
        kill_switch_file=str(tmp_path / "no_kill_switch_here.flag"),  # nonexistent
    )
    return LiveRiskGates(limits=limits, db=db)


def _intent(qty: float = 1.0, price: float = 100.0, side: str = "buy") -> dict:
    return {"qty": qty, "price": price, "side": side, "symbol": "BTC/USD"}


class TestDailyLossHalt:
    def test_below_daily_loss_allows_trade(self, tmp_path):
        gate = _make_gate(tmp_path, max_daily_loss_usd=100.0)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=-50.0)
        assert ok is True
        assert reason == "OK"

    def test_at_daily_loss_limit_blocks_trade(self, tmp_path):
        gate = _make_gate(tmp_path, max_daily_loss_usd=100.0)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=-100.0)
        assert ok is False
        assert "MAX_DAILY_LOSS" in reason

    def test_beyond_daily_loss_limit_blocks_trade(self, tmp_path):
        gate = _make_gate(tmp_path, max_daily_loss_usd=100.0)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=-200.0)
        assert ok is False
        assert "MAX_DAILY_LOSS" in reason

    def test_positive_pnl_allows_trade(self, tmp_path):
        gate = _make_gate(tmp_path, max_daily_loss_usd=100.0)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=50.0)
        assert ok is True


class TestNotionalCap:
    def test_below_notional_cap_allows_trade(self, tmp_path):
        gate = _make_gate(tmp_path, max_notional_per_trade_usd=500.0)
        # qty=1, price=100 → notional=100, cap=500
        ok, reason, _ = gate.check_live(it=_intent(qty=1.0, price=100.0), realized_pnl_usd=0.0)
        assert ok is True

    def test_above_notional_cap_blocks_trade(self, tmp_path):
        gate = _make_gate(tmp_path, max_notional_per_trade_usd=50.0)
        # qty=1, price=100 → notional=100, cap=50
        ok, reason, _ = gate.check_live(it=_intent(qty=1.0, price=100.0), realized_pnl_usd=0.0)
        assert ok is False
        assert "MAX_NOTIONAL_PER_TRADE" in reason


class TestMaxTradesPerDay:
    def test_below_trade_limit_allows(self, tmp_path):
        gate = _make_gate(tmp_path, max_trades_per_day=5)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=0.0)
        assert ok is True

    def test_at_trade_limit_blocks(self, tmp_path):
        gate = _make_gate(tmp_path, max_trades_per_day=0)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=0.0)
        assert ok is False
        assert "MAX_TRADES_PER_DAY" in reason


class TestKillSwitch:
    def test_killswitch_db_blocks_all_orders(self, tmp_path):
        gate = _make_gate(tmp_path)
        gate.db.set_killswitch(True)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=0.0)
        assert ok is False
        assert "KILL_SWITCH" in reason

    def test_killswitch_off_allows_orders(self, tmp_path):
        gate = _make_gate(tmp_path)
        gate.db.set_killswitch(True)
        gate.db.set_killswitch(False)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=0.0)
        assert ok is True

    def test_killswitch_file_blocks_when_present(self, tmp_path):
        kill_file = tmp_path / "kill.flag"
        kill_file.write_text("stop")
        db_path = str(tmp_path / "test.sqlite")
        db = LiveGateDB(exec_db=db_path)
        lim = LiveRiskLimits(
            max_daily_loss_usd=100.0,
            max_notional_per_trade_usd=500.0,
            max_trades_per_day=10,
            max_position_notional_usd=1000.0,
            kill_switch_file=str(kill_file),
        )
        gate = LiveRiskGates(limits=lim, db=db)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=0.0)
        assert ok is False
        assert "KILL_SWITCH" in reason

    def test_killswitch_file_absent_does_not_block(self, tmp_path):
        db_path = str(tmp_path / "test.sqlite")
        db = LiveGateDB(exec_db=db_path)
        lim = LiveRiskLimits(
            max_daily_loss_usd=100.0,
            max_notional_per_trade_usd=500.0,
            max_trades_per_day=10,
            max_position_notional_usd=1000.0,
            kill_switch_file=str(tmp_path / "nonexistent.flag"),
        )
        gate = LiveRiskGates(limits=lim, db=db)
        ok, reason, _ = gate.check_live(it=_intent(), realized_pnl_usd=0.0)
        assert ok is True


class TestLimitsConstruction:
    def test_from_dict_valid(self):
        cfg = {"risk": {"live": {
            "max_daily_loss_usd": 25.0,
            "max_notional_per_trade_usd": 25.0,
            "max_trades_per_day": 10,
            "max_position_notional_usd": 100.0,
        }}}
        lim = LiveRiskLimits.from_dict(cfg)
        assert lim is not None
        assert lim.max_daily_loss_usd == 25.0

    def test_from_dict_missing_field_returns_none(self):
        cfg = {"risk": {"live": {"max_daily_loss_usd": 25.0}}}
        lim = LiveRiskLimits.from_dict(cfg)
        assert lim is None

    def test_from_dict_zero_limit_returns_none(self):
        cfg = {"risk": {"live": {
            "max_daily_loss_usd": 0.0,  # zero — invalid
            "max_notional_per_trade_usd": 25.0,
            "max_trades_per_day": 10,
            "max_position_notional_usd": 100.0,
        }}}
        lim = LiveRiskLimits.from_dict(cfg)
        assert lim is None
