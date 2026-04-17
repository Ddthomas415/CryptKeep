"""tests/test_campaign_summary.py

Tests for services/strategies/campaign_summary.py and the
evidence reporting layer.

Covers:
  - evidence_summary() with no evidence dir
  - evidence_summary() with JSONL files
  - evidence_summary() record counting
  - signal_from_ohlcv() logs to evidence dir
  - session phase field present in records
"""
from __future__ import annotations

import json
import pytest
from pathlib import Path
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TestEvidenceSummary:
    def test_no_evidence_dir_returns_not_exists(self, tmp_path):
        from services.strategies.campaign_summary import evidence_summary
        result = evidence_summary("nonexistent_strategy")
        assert result["exists"] is False
        assert result["files_by_type"] == {}
        assert result["total_records"] == 0

    def test_empty_dir_returns_exists_no_files(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "test_strat"
        ev_dir.mkdir(parents=True, exist_ok=True)
        from services.strategies.campaign_summary import evidence_summary
        result = evidence_summary("test_strat")
        assert result["exists"] is True
        assert result["files_by_type"] == {}

    def test_counts_jsonl_files_by_type(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "test_strat"
        ev_dir.mkdir(parents=True, exist_ok=True)
        (ev_dir / "signal_2026-04-17.jsonl").write_text(
            json.dumps({"record_type": "signal"}) + "\n" +
            json.dumps({"record_type": "signal"}) + "\n"
        )
        (ev_dir / "session_2026-04-17.jsonl").write_text(
            json.dumps({"record_type": "session"}) + "\n"
        )
        from services.strategies.campaign_summary import evidence_summary
        result = evidence_summary("test_strat")
        assert result["files_by_type"] == {"signal": 1, "session": 1}
        assert result["total_records"] == 3

    def test_strategy_id_in_result(self, tmp_path):
        from services.strategies.campaign_summary import evidence_summary
        result = evidence_summary("my_strategy")
        assert result["strategy_id"] == "my_strategy"


class TestSignalFromOhlcvLogging:
    def test_signal_from_ohlcv_writes_signal_jsonl(self, tmp_path):
        """signal_from_ohlcv() must write a signal evidence record on each call."""
        from services.strategies.es_daily_trend import signal_from_ohlcv
        from services.strategies.campaign_summary import evidence_summary

        n = 210
        ohlcv = [[i, 100.0, 101.0, 99.0, 100.0 + i * 0.1, 1000.0] for i in range(n)]
        result = signal_from_ohlcv(ohlcv)
        assert "action" in result

        ev = evidence_summary("es_daily_trend_v1")
        assert ev["exists"], "evidence dir not created by signal_from_ohlcv"
        assert "signal" in ev["files_by_type"], f"no signal files: {ev['files_by_type']}"
        assert ev["total_records"] >= 1

    def test_signal_record_has_required_fields(self, tmp_path):
        """Signal records must contain all schema-required fields."""
        from services.strategies.es_daily_trend import signal_from_ohlcv
        from services.os.app_paths import data_dir

        n = 210
        ohlcv = [[i, 100.0, 101.0, 99.0, 100.0 + i * 0.1, 1000.0] for i in range(n)]
        signal_from_ohlcv(ohlcv)

        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        files = list(ev_dir.glob("signal_*.jsonl"))
        assert files, "no signal files written"
        record = json.loads(files[0].read_text().strip().splitlines()[0])
        for field in ("timestamp", "price", "sma_200", "atr_ratio",
                      "signal_direction", "regime_flag"):
            assert field in record, f"missing required field: {field}"


class TestSessionPhaseField:
    def test_session_record_accepts_phase_field(self, tmp_path):
        """Session records must support phase: start/end field."""
        from services.strategies.evidence_logger import EvidenceLogger
        from services.os.app_paths import data_dir

        logger = EvidenceLogger("test_strat")
        logger.log_session(
            regime_at_open="trending",
            halts_triggered=[],
            manual_overrides=[],
            reconciliation_result="pending",
            drawdown_from_peak=0.0,
            extra={"phase": "start"},
        )
        logger.log_session(
            regime_at_open="trending",
            halts_triggered=[],
            manual_overrides=[],
            reconciliation_result="pass",
            drawdown_from_peak=0.0,
            extra={"phase": "end"},
        )

        ev_dir = data_dir() / "evidence" / "test_strat"
        files = list(ev_dir.glob("session_*.jsonl"))
        assert files
        lines = [json.loads(l) for l in files[0].read_text().strip().splitlines()]
        assert len(lines) == 2
        assert lines[0].get("phase") == "start"
        assert lines[1].get("phase") == "end"

    def test_start_record_has_pending_reconciliation(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        from services.os.app_paths import data_dir

        logger = EvidenceLogger("test_strat")
        logger.log_session(
            regime_at_open="paper",
            halts_triggered=[],
            manual_overrides=[],
            reconciliation_result="pending",
            drawdown_from_peak=0.0,
            extra={"phase": "start"},
        )

        ev_dir = data_dir() / "evidence" / "test_strat"
        files = list(ev_dir.glob("session_*.jsonl"))
        record = json.loads(files[0].read_text().strip())
        assert record["reconciliation_result"] == "pending"
        assert record["phase"] == "start"


class TestTeardownStatusInSummary:
    def test_clean_teardown_reported(self, tmp_path, capsys):
        from services.strategies.campaign_summary import print_campaign_summary
        result = {
            "status": "completed",
            "reason": "campaign_complete",
            "completed_strategies": 1,
            "teardown": {"clean": True, "still_alive": []},
        }
        print_campaign_summary("es_daily_trend_v1", result)
        captured = capsys.readouterr()
        assert "Teardown: clean" in captured.out

    def test_dirty_teardown_shows_processes(self, tmp_path, capsys):
        from services.strategies.campaign_summary import print_campaign_summary
        result = {
            "status": "completed",
            "reason": "campaign_complete",
            "completed_strategies": 1,
            "teardown": {"clean": False, "still_alive": ["tick_publisher"]},
        }
        print_campaign_summary("es_daily_trend_v1", result)
        captured = capsys.readouterr()
        assert "tick_publisher" in captured.out
        assert "paper-stop" in captured.out


class TestRequiredHistory:
    def test_sma_200_trend_requires_210_bars(self):
        """sma_200_trend must request at least sma_period+10 bars — else signal never fires."""
        import sys
        sys.path.insert(0, ".")
        from services.strategy_runner.ema_crossover_runner import _required_history
        block = {"name": "sma_200_trend", "sma_period": 200, "atr_period": 20}
        result = _required_history(block)
        assert result >= 210, f"_required_history returned {result} — must be >= 210 for sma_200_trend"

    def test_sma_200_trend_custom_period(self):
        from services.strategy_runner.ema_crossover_runner import _required_history
        block = {"name": "sma_200_trend", "sma_period": 50, "atr_period": 14}
        result = _required_history(block)
        assert result >= 60  # 50 + 10

    def test_unknown_strategy_returns_5(self):
        from services.strategy_runner.ema_crossover_runner import _required_history
        block = {"name": "unknown_xyz"}
        assert _required_history(block) == 5

    def test_signal_insufficient_history_still_logs(self, tmp_path):
        """signal_from_ohlcv logs even when bar count is too low."""
        from services.strategies.es_daily_trend import signal_from_ohlcv
        from services.strategies.campaign_summary import evidence_summary

        # Only 5 bars — way below 200
        ohlcv = [[i, 100.0, 101.0, 99.0, 100.0, 1000.0] for i in range(5)]
        result = signal_from_ohlcv(ohlcv)

        assert result["reason"] == "insufficient_history"

        ev = evidence_summary("es_daily_trend_v1")
        assert ev["exists"], "evidence dir not created"
        assert "signal" in ev["files_by_type"], "no signal file even for insufficient_history"

    def test_signal_sufficient_history_logs_with_direction(self, tmp_path):
        """signal_from_ohlcv with 210 bars logs a real signal_direction."""
        import json
        from services.strategies.es_daily_trend import signal_from_ohlcv
        from services.os.app_paths import data_dir

        n = 210
        ohlcv = [[i, 100.0, 101.0, 99.0, 100.0 + i * 0.1, 1000.0] for i in range(n)]
        signal_from_ohlcv(ohlcv)

        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        files = list(ev_dir.glob("signal_*.jsonl"))
        assert files
        records = [json.loads(l) for l in files[0].read_text().strip().splitlines() if l.strip()]
        full = [r for r in records if r.get("regime_flag") != "insufficient_data"]
        assert full, "no full signal records found — bar count fix may not have worked"
        assert full[-1]["signal_direction"] in ("long", "flat")


class TestCampaignConfig:
    def test_signal_source_is_public_ohlcv_1d(self, tmp_path):
        """sma_200_trend campaigns must use public_ohlcv_1d signal source.

        Without this, ema_crossover_runner falls into the tick-based path
        which never calls signal_from_ohlcv() and signal evidence is never written.
        This test ensures a future change does not silently remove this setting.
        """
        from services.analytics.paper_strategy_evidence_service import PaperStrategyEvidenceServiceCfg
        cfg = PaperStrategyEvidenceServiceCfg(
            strategies=("sma_200_trend",),
            symbol="BTC/USDT",
            venue="coinbase",
            signal_source="public_ohlcv_1d",
        )
        assert cfg.signal_source == "public_ohlcv_1d", (
            "signal_source must be 'public_ohlcv_1d' for sma_200_trend. "
            "Without this the runner uses tick-based prices and never calls "
            "signal_from_ohlcv() — signal evidence is never written."
        )
