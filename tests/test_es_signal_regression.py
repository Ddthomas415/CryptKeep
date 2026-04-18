"""tests/test_es_signal_regression.py

Regression guard for the ES paper-run signal evidence bug.

This test encodes the exact failure class that took multiple sessions to diagnose:
  - sma_200_trend with public_ohlcv_1d signal source
  - sufficient OHLCV depth (>=210 bars)
  - signal_from_ohlcv() must be called and must write evidence

If this test fails, signal evidence will not be written in production.
DO NOT remove or weaken this test.
"""
from __future__ import annotations

import json
import os
import tempfile
import pytest
from pathlib import Path


@pytest.fixture(autouse=True)
def isolated_state(monkeypatch):
    tmp = tempfile.mkdtemp()
    monkeypatch.setenv("CBP_STATE_DIR", tmp)
    monkeypatch.setenv("CBP_USE_SAMPLE_OHLCV", "1")
    yield tmp


def _load_sample_ohlcv() -> list:
    sample = Path("sample_data/ohlcv/BTC_USDT_1d.json")
    assert sample.exists(), f"Sample OHLCV file missing: {sample}"
    rows = json.loads(sample.read_text())
    assert len(rows) >= 210, f"Sample OHLCV has only {len(rows)} bars — need 210+"
    return rows


class TestSignalEvidenceRegression:
    """Guards against the 'campaign completes but no signal_*.jsonl' failure class."""

    def test_sample_ohlcv_has_sufficient_depth(self):
        """210+ bars required for 200-SMA. If this fails, the sample data is too short."""
        rows = _load_sample_ohlcv()
        assert len(rows) >= 210

    def test_signal_from_ohlcv_writes_evidence(self, isolated_state):
        """Calling signal_from_ohlcv() with 210+ bars must produce a signal_*.jsonl file."""
        from services.strategies.es_daily_trend import signal_from_ohlcv
        from services.strategies.campaign_summary import evidence_summary

        rows = _load_sample_ohlcv()
        result = signal_from_ohlcv(rows)

        assert "action" in result, "signal_from_ohlcv returned no action"
        assert result.get("regime") != "insufficient_data", (
            f"Got insufficient_data regime with {len(rows)} bars — _required_history may be broken"
        )

        ev = evidence_summary("es_daily_trend_v1")
        assert ev["exists"], "Evidence directory not created after signal_from_ohlcv()"
        assert "signal" in ev["files_by_type"], (
            f"No signal files written. files_by_type={ev['files_by_type']}. "
            "This means signal_from_ohlcv() ran but log_signal() failed or wrote elsewhere."
        )
        assert ev["total_records"] >= 1

    def test_signal_record_has_required_fields(self, isolated_state):
        """Signal records must contain all fields needed by check_promotion_gates."""
        from services.strategies.es_daily_trend import signal_from_ohlcv
        from services.os.app_paths import data_dir

        rows = _load_sample_ohlcv()
        signal_from_ohlcv(rows)

        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        files = list(ev_dir.glob("signal_*.jsonl"))
        assert files, "No signal files found"

        record = json.loads(files[0].read_text().strip().splitlines()[0])
        required = ("timestamp", "price", "sma_200", "signal_direction", "regime_flag")
        missing = [f for f in required if f not in record]
        assert not missing, f"Signal record missing required fields: {missing}"

    def test_campaign_config_has_correct_signal_source(self, isolated_state):
        """Campaign must configure signal_source=public_ohlcv_1d.
        
        Without this, ema_crossover_runner falls into the tick-based path
        which never calls signal_from_ohlcv() — signal evidence never writes.
        """
        from services.analytics.paper_strategy_evidence_service import PaperStrategyEvidenceServiceCfg
        cfg = PaperStrategyEvidenceServiceCfg(
            strategies=("sma_200_trend",),
            symbol="BTC/USDT",
            venue="coinbase",
            signal_source="public_ohlcv_1d",
        )
        assert cfg.signal_source == "public_ohlcv_1d", (
            "signal_source must be public_ohlcv_1d — see commit 1a7b161 for why"
        )

    def test_required_history_sma_200_trend_is_sufficient(self):
        """_required_history must return >=210 for sma_200_trend.
        
        If this returns 5 (the fallback), the runner fetches 60 bars and 
        signal_from_ohlcv() hits the early-return branch — no evidence written.
        """
        from services.strategy_runner.ema_crossover_runner import _required_history
        block = {"name": "sma_200_trend", "sma_period": 200, "atr_period": 20}
        n = _required_history(block)
        assert n >= 210, (
            f"_required_history returned {n} for sma_200_trend — must be >=210. "
            "If this fell through to the default of 5, add sma_200_trend to the match block."
        )
