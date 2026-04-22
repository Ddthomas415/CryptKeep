"""
tests/test_es_daily_trend.py

Conformance tests for ES Daily Trend v1.

Every test maps to a specific threshold or rule in:
  docs/strategies/es_daily_trend_v1.md
  configs/strategies/es_daily_trend_v1.yaml

If a test fails, find the corresponding spec section and fix the
implementation — not the test.
"""
from __future__ import annotations

import math
import os
from pathlib import Path
import pytest


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _closes_above_sma(n: int = 210, margin: float = 5.0) -> list[float]:
    """Steady uptrend, final close well above 200-SMA."""
    closes = [100.0 + i * 0.3 for i in range(n)]
    return closes


def _closes_below_sma(n: int = 210) -> list[float]:
    """Uptrend then sharp drop — final close below 200-SMA."""
    closes = [100.0 + i * 0.3 for i in range(n)]
    closes[-1] = closes[-1] - 80
    return closes


def _ohlc(closes: list[float], spread: float = 1.0):
    highs = [c + spread for c in closes]
    lows  = [c - spread for c in closes]
    return highs, lows, closes


def test_es_daily_trend_has_no_console_print():
    source = Path("services/strategies/es_daily_trend.py").read_text(encoding="utf-8")
    assert "print(" not in source


# ---------------------------------------------------------------------------
# Signal — spec §1
# ---------------------------------------------------------------------------

class TestSignal:
    """Spec §1: price > 200-SMA → LONG; price ≤ 200-SMA → FLAT."""

    def test_long_when_above_sma(self):
        from services.strategies.es_daily_trend import compute_signal
        assert compute_signal(_closes_above_sma()) == "long"

    def test_flat_when_below_sma(self):
        from services.strategies.es_daily_trend import compute_signal
        assert compute_signal(_closes_below_sma()) == "flat"

    def test_flat_on_insufficient_history(self):
        from services.strategies.es_daily_trend import compute_signal
        assert compute_signal([100.0] * 50) == "flat"

    def test_flat_at_exactly_200_bars(self):
        from services.strategies.es_daily_trend import compute_signal
        # Exactly 200 bars — all equal → price == SMA → FLAT
        closes = [100.0] * 200
        assert compute_signal(closes) == "flat"

    def test_long_at_201_bars_above(self):
        from services.strategies.es_daily_trend import compute_signal
        closes = [100.0] * 200 + [101.0]
        assert compute_signal(closes) == "long"


# ---------------------------------------------------------------------------
# Regime filter — spec §2
# ---------------------------------------------------------------------------

class TestRegime:
    """Spec §2: ATR ratio thresholds gate entry."""

    def test_trending_regime_allows_entry(self):
        from services.strategies.es_daily_trend import regime_stability
        closes = _closes_above_sma(300)
        highs, lows, _ = _ohlc(closes, spread=0.8)
        result = regime_stability(highs, lows, closes)
        assert result["entry_allowed"] is True
        assert result["regime"] in ("trending", "borderline")

    def test_insufficient_data_blocks_entry(self):
        from services.strategies.es_daily_trend import regime_stability
        closes = [100.0] * 50
        highs = [c + 1 for c in closes]
        lows  = [c - 1 for c in closes]
        result = regime_stability(highs, lows, closes)
        assert result["entry_allowed"] is False
        assert result["regime"] == "insufficient_data"

    def test_high_vol_regime_blocks_entry(self):
        """ATR ratio > 2.5 → high_vol → entry blocked."""
        from services.strategies.es_daily_trend import regime_stability
        closes = [100.0] * 300
        # Inflate current bars to create huge ATR vs calm history
        highs = [100.0] * 300
        lows  = [100.0] * 300
        # Last 20 bars have 50-point spread → current ATR >> historical
        for i in range(280, 300):
            highs[i] = 150.0
            lows[i] = 50.0
        result = regime_stability(highs, lows, closes,
                                  trending_floor=0.80, high_vol_ceiling=2.5)
        assert result["regime"] == "high_vol"
        assert result["entry_allowed"] is False

    def test_regime_returns_atr_ratio(self):
        from services.strategies.es_daily_trend import regime_stability
        closes = _closes_above_sma(300)
        highs, lows, _ = _ohlc(closes)
        result = regime_stability(highs, lows, closes)
        assert result["atr_ratio"] is not None
        assert result["atr_ratio"] > 0


# ---------------------------------------------------------------------------
# Stop calculation — spec §1 (stop: 2×ATR)
# ---------------------------------------------------------------------------

class TestStop:
    """Spec §1: hard stop = entry_price − 2 × ATR(20)."""

    def test_stop_below_entry_for_long(self):
        from services.strategies.es_daily_trend import compute_stop
        stop = compute_stop(entry_price=4500.0, current_atr=20.0)
        assert stop == 4500.0 - 2.0 * 20.0

    def test_stop_distance_is_two_atr(self):
        from services.strategies.es_daily_trend import compute_stop
        entry, atr = 5000.0, 25.0
        stop = compute_stop(entry, atr, atr_multiplier=2.0)
        assert abs((entry - stop) - 2 * atr) < 1e-9

    def test_short_side_raises(self):
        """v1 is long/flat only. Short side must raise."""
        from services.strategies.es_daily_trend import compute_stop
        with pytest.raises(ValueError, match="not supported"):
            compute_stop(5000.0, 20.0, side="short")


# ---------------------------------------------------------------------------
# Position sizing — spec §3
# ---------------------------------------------------------------------------

class TestSizing:
    """Spec §3: 0.5% capital at risk at stop; max 10% notional."""

    def test_capital_at_risk_is_half_pct(self):
        """With 0.5% risk and known stop distance, verify capital at risk."""
        from services.strategies.es_daily_trend import compute_position_size
        capital = 100_000.0
        # entry=200, stop=190, dist=10, units=500/10=50, notional=10000=max_notional_pct
        # At exactly 10% notional: not capped, capital_at_risk = 50*10 = 500
        result = compute_position_size(capital, entry_price=200.0, stop_price=190.0)
        assert not result["capped"]
        assert abs(result["capital_at_risk_usd"] - 500.0) < 1.0

    def test_max_notional_cap_applies(self):
        """Position capped at 10% notional when formula overshoots."""
        from services.strategies.es_daily_trend import compute_position_size
        capital = 100_000.0
        # Tiny stop → enormous position → should be capped
        result = compute_position_size(capital, entry_price=5000.0, stop_price=4999.0,
                                       max_notional_pct=10.0)
        assert result["capped"] is True
        assert result["notional"] <= capital * 0.10 + 1.0

    def test_zero_stop_distance_returns_zero(self):
        from services.strategies.es_daily_trend import compute_position_size
        result = compute_position_size(100_000.0, entry_price=5000.0, stop_price=5000.0)
        assert result["contracts"] == 0

    def test_contracts_is_floor_of_units(self):
        """Contracts must be whole numbers."""
        from services.strategies.es_daily_trend import compute_position_size
        result = compute_position_size(100_000.0, entry_price=5000.0, stop_price=4800.0)
        assert result["contracts"] == math.floor(result["contracts"])


# ---------------------------------------------------------------------------
# Full decision — kernel integration
# ---------------------------------------------------------------------------

class TestDecide:
    """The decide() function must gate on signal, regime, and kernel."""

    def test_no_contracts_in_paper_stage(self):
        """Kernel in paper stage → zero contracts always."""
        from services.strategies.es_daily_trend import decide
        closes = _closes_above_sma(300)
        highs, lows, _ = _ohlc(closes)
        result = decide(closes, highs, lows, total_capital=100_000.0)
        assert result["sizing"]["contracts"] == 0
        assert result["kernel_stage"] == "paper"

    def test_signal_logged_even_when_blocked(self):
        """Signal value must always be present, regardless of blocking."""
        from services.strategies.es_daily_trend import decide
        closes = _closes_above_sma(300)
        highs, lows, _ = _ohlc(closes)
        result = decide(closes, highs, lows)
        assert result["signal"] in ("long", "flat")
        assert result["regime"]["regime"] is not None

    def test_flat_signal_never_allows_new_risk(self):
        from services.strategies.es_daily_trend import decide
        closes = _closes_below_sma(300)
        highs, lows, _ = _ohlc(closes)
        result = decide(closes, highs, lows)
        assert result["signal"] == "flat"
        assert result["new_risk_allowed"] is False
        assert result["sizing"]["contracts"] == 0

    def test_result_contains_all_required_fields(self):
        """Every decision must include the evidence fields required by spec §5."""
        from services.strategies.es_daily_trend import decide
        closes = _closes_above_sma(300)
        highs, lows, _ = _ohlc(closes)
        result = decide(closes, highs, lows)
        required = {"strategy_id", "signal", "sma_200", "regime",
                    "kernel_action", "kernel_stage", "new_risk_allowed",
                    "stop_price", "sizing", "reasons"}
        assert required.issubset(result.keys())

    def test_capped_live_max_one_contract(self):
        """In capped_live stage, kernel caps allocation to ≤ 1 contract."""
        from services.control.deployment_stage import promote
        from services.strategies.es_daily_trend import decide, STRATEGY_ID
        # Promote to capped_live
        promote(STRATEGY_ID, reason="test"); promote(STRATEGY_ID, reason="test")
        closes = _closes_above_sma(300)
        highs, lows, _ = _ohlc(closes)
        result = decide(closes, highs, lows,
                        total_capital=10_000_000.0,  # large capital to test cap
                        kernel_metrics={
                            "slippage_p95": 0.1, "fill_rate": 0.99,
                            "recon_drift": 0.0, "dd_duration_days": 0,
                            "regime_stability": 0.9, "alert_count": 0,
                        })
        assert result["sizing"]["contracts"] <= 1


# ---------------------------------------------------------------------------
# Config conformance — all threshold values exist and are within valid ranges
# ---------------------------------------------------------------------------

class TestConfigConformance:
    """Verify configs/strategies/es_daily_trend_v1.yaml is internally consistent."""

    def _load_config(self):
        import yaml
        from pathlib import Path
        p = Path("configs/strategies/es_daily_trend_v1.yaml")
        return yaml.safe_load(p.read_text())

    def test_config_loads(self):
        cfg = self._load_config()
        assert cfg["strategy"]["id"] == "es_daily_trend_v1"

    def test_sma_period_is_200(self):
        cfg = self._load_config()
        assert cfg["strategy"]["signal"]["sma_period"] == 200

    def test_risk_within_framework_bounds(self):
        """capital_at_risk must be in 0.25–1.0% per DECISION_FRAMEWORK.md."""
        cfg = self._load_config()
        risk_pct = cfg["risk"]["capital_at_risk_per_trade_pct"]
        assert 0.25 <= risk_pct <= 1.0

    def test_daily_halt_within_framework_bounds(self):
        """daily_loss_halt must be in 1–3% per DECISION_FRAMEWORK.md."""
        cfg = self._load_config()
        halt_pct = cfg["risk"]["daily_loss_halt_pct"]
        assert 1.0 <= halt_pct <= 3.0

    def test_stage_is_paper(self):
        """Strategy must start in paper stage."""
        cfg = self._load_config()
        assert cfg["strategy"]["stage"] == "paper"

    def test_no_short_constraint(self):
        """v1 must have no_short=True per spec §8."""
        cfg = self._load_config()
        assert cfg["constraints"]["no_short"] is True

    def test_single_instrument_constraint(self):
        cfg = self._load_config()
        assert cfg["constraints"]["single_instrument"] is True

    def test_capped_live_min_weeks_is_8(self):
        """Low-frequency system: min 8 weeks per spec §6."""
        cfg = self._load_config()
        assert cfg["risk"]["capped_live"]["min_weeks"] >= 8

    def test_regime_trending_floor_above_chop_ceiling(self):
        """trending_floor must be strictly greater than chop_ceiling."""
        cfg = self._load_config()
        r = cfg["regime"]["thresholds"]
        assert r["trending_floor"] > r["chop_ceiling"]

    def test_halve_size_at_is_half_of_max_drawdown(self):
        """halve_size_at must be 50% of max_drawdown per spec §3."""
        cfg = self._load_config()
        max_dd = cfg["risk"]["max_drawdown_pct"]
        halve_at = cfg["risk"]["drawdown_rules"]["halve_size_at_pct"]
        assert abs(halve_at - max_dd * 0.5) < 0.1
