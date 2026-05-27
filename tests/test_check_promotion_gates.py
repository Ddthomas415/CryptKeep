"""tests/test_check_promotion_gates.py

Tests for scripts/check_promotion_gates.py — the promotion decision engine.

This is what tells the operator whether it's safe to promote. A bug here
means either: gates pass when they shouldn't, or gates fail spuriously.
"""
from __future__ import annotations
import json
import sqlite3
import pytest
from pathlib import Path
from datetime import datetime, timezone


@pytest.fixture(autouse=True)
def isolate(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_evidence(ev_dir: Path, record_type: str, record: dict) -> None:
    from services.strategies.evidence_logger import EvidenceLogger
    logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
    getattr(logger, f"log_{record_type}")(**record)


class TestGateOutput:
    def test_json_output_is_valid_and_complete(self, tmp_path):
        from scripts.check_promotion_gates import run_check
        result = run_check()
        # Must be JSON-serializable
        json.dumps(result, default=str)
        for key in ("strategy_id", "stage", "ready", "summary", "gates", "schema"):
            assert key in result, f"missing key: {key}"

    def test_no_evidence_gives_fail_on_evidence_gate(self, tmp_path):
        from scripts.check_promotion_gates import run_check
        result = run_check()
        gate = next(g for g in result["gates"] if "evidence logs" in g["label"].lower())
        assert gate["passed"] is False

    def test_summary_counts_match_gates(self, tmp_path):
        from scripts.check_promotion_gates import run_check
        result = run_check()
        gates = result["gates"]
        s = result["summary"]
        assert s["pass"] == sum(1 for g in gates if g["passed"] is True)
        assert s["fail"] == sum(1 for g in gates if g["passed"] is False)
        assert s["unknown"] == sum(1 for g in gates if g["passed"] is None)
        assert s["total"] == len(gates)


class TestSchemaValidation:
    def test_valid_signal_schema_passes(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        ev_dir.mkdir(parents=True, exist_ok=True)
        from services.strategies.evidence_logger import EvidenceLogger
        EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir).log_signal(
            timestamp=_now(), price=5000.0, sma_200=4800.0,
            atr_ratio=1.2, signal_direction="long", regime_flag="trending",
        )
        from scripts.check_promotion_gates import run_check
        result = run_check()
        assert result["schema"]["signal"]["ok"] is True

    def test_missing_required_fields_fails_schema(self, tmp_path):
        from scripts.check_promotion_gates import _validate_schema
        records = [{"timestamp": "2026-01-01", "price": 100.0}]
        required = ["timestamp", "price", "sma_200", "atr_ratio", "signal_direction", "regime_flag"]
        result = _validate_schema(records, required, "signal")
        assert result["ok"] is False
        assert result["bad_records"] == 1
        missing = {m["field"] for m in result["missing_fields"]}
        assert "sma_200" in missing

    def test_all_fields_present_passes_schema(self, tmp_path):
        from scripts.check_promotion_gates import _validate_schema
        records = [{
            "timestamp": "2026-01-01", "price": 100.0, "sma_200": 90.0,
            "atr_ratio": 1.1, "signal_direction": "long", "regime_flag": "trending",
        }]
        required = ["timestamp", "price", "sma_200", "atr_ratio", "signal_direction", "regime_flag"]
        result = _validate_schema(records, required, "signal")
        assert result["ok"] is True

    def test_present_null_fields_still_pass_schema(self, tmp_path):
        from scripts.check_promotion_gates import _validate_schema
        records = [{
            "timestamp": "2026-01-01",
            "price": 100.0,
            "sma_200": None,
            "atr_ratio": None,
            "signal_direction": "flat",
            "regime_flag": "insufficient_data",
        }]
        required = ["timestamp", "price", "sma_200", "atr_ratio", "signal_direction", "regime_flag"]
        result = _validate_schema(records, required, "signal")
        assert result["ok"] is True
        assert result["bad_records"] == 0
        assert result["missing_fields"] == []


class TestGateLogic:
    def _ev_dir(self):
        from services.os.app_paths import data_dir
        d = data_dir() / "evidence" / "es_daily_trend_v1"
        d.mkdir(parents=True, exist_ok=True)
        return d

    def test_regime_block_detected(self, tmp_path):
        ev_dir = self._ev_dir()
        from services.strategies.evidence_logger import EvidenceLogger
        EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir).log_signal(
            timestamp=_now(), price=5000.0, sma_200=4800.0,
            atr_ratio=0.5, signal_direction="flat", regime_flag="chop",
        )
        from scripts.check_promotion_gates import _load_all_evidence, _any_regime_block
        evidence = _load_all_evidence(ev_dir)
        assert _any_regime_block(evidence["signal"]) is True

    def test_no_regime_block_when_all_trending(self, tmp_path):
        ev_dir = self._ev_dir()
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
        for _ in range(3):
            logger.log_signal(
                timestamp=_now(), price=5000.0, sma_200=4800.0,
                atr_ratio=1.2, signal_direction="long", regime_flag="trending",
            )
        from scripts.check_promotion_gates import _load_all_evidence, _any_regime_block
        evidence = _load_all_evidence(ev_dir)
        assert _any_regime_block(evidence["signal"]) is False

    def test_kill_switch_gate_passes_when_logged(self, tmp_path):
        ev_dir = self._ev_dir()
        from services.strategies.evidence_logger import EvidenceLogger
        EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir).log_session(
            regime_at_open="trending", halts_triggered=[],
            manual_overrides=[], reconciliation_result="pass",
            drawdown_from_peak=0.0, kill_switch_tested=True,
        )
        from scripts.check_promotion_gates import _load_all_evidence, _kill_switch_tested
        evidence = _load_all_evidence(ev_dir)
        assert _kill_switch_tested(evidence["session"]) is True

    def test_kill_switch_status_requires_recent_test(self, tmp_path):
        from scripts.check_promotion_gates import _kill_switch_test_status

        stale = _kill_switch_test_status(
            [{"timestamp": "2026-05-01T00:00:00+00:00", "kill_switch_tested": True}],
            {"ops": {"kill_switch_test_frequency": "weekly"}},
            reference_ts=datetime.fromisoformat("2026-05-10T00:00:00+00:00"),
        )
        fresh = _kill_switch_test_status(
            [{"timestamp": "2026-05-04T00:00:00+00:00", "kill_switch_tested": True}],
            {"ops": {"kill_switch_test_frequency": "weekly"}},
            reference_ts=datetime.fromisoformat("2026-05-10T00:00:00+00:00"),
        )

        assert stale["ok"] is False
        assert stale["max_age_days"] == 7
        assert fresh["ok"] is True

    def test_days_of_operation_unique_dates(self, tmp_path):
        ev_dir = self._ev_dir()
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
        # All sessions logged today → only 1 unique day
        for _ in range(5):
            logger.log_session(
                regime_at_open="trending", halts_triggered=[],
                manual_overrides=[], reconciliation_result="pass",
                drawdown_from_peak=0.0,
            )
        from scripts.check_promotion_gates import _load_all_evidence, _days_of_operation
        evidence = _load_all_evidence(ev_dir)
        days = _days_of_operation(evidence["session"])
        assert days == 1

    def test_paper_gate_uses_trade_journal_for_round_trips_and_expectancy(self, tmp_path):
        from services.os.app_paths import data_dir
        from scripts.check_promotion_gates import run_check

        journal = data_dir() / "trade_journal.sqlite"
        journal.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(str(journal))
        try:
            con.execute(
                """
                CREATE TABLE journal_fills (
                  fill_id TEXT PRIMARY KEY,
                  journal_ts TEXT NOT NULL,
                  strategy_id TEXT,
                  fill_ts TEXT NOT NULL,
                  venue TEXT NOT NULL,
                  symbol TEXT NOT NULL,
                  side TEXT NOT NULL,
                  qty REAL NOT NULL,
                  price REAL NOT NULL,
                  fee REAL NOT NULL,
                  fee_currency TEXT NOT NULL
                )
                """
            )
            rows = []
            for idx in range(7):
                rows.append((
                    f"buy-{idx}",
                    f"2026-05-{idx + 1:02d}T00:00:00+00:00",
                    "sma_200_trend",
                    f"2026-05-{idx + 1:02d}T00:00:00+00:00",
                    "coinbase",
                    "BTC/USDT",
                    "buy",
                    1.0,
                    100.0,
                    0.0,
                    "USD",
                ))
                rows.append((
                    f"sell-{idx}",
                    f"2026-05-{idx + 1:02d}T01:00:00+00:00",
                    "sma_200_trend",
                    f"2026-05-{idx + 1:02d}T01:00:00+00:00",
                    "coinbase",
                    "BTC/USDT",
                    "sell",
                    1.0,
                    110.0,
                    0.0,
                    "USD",
                ))
            con.executemany(
                "INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                rows,
            )
            con.commit()
        finally:
            con.close()

        result = run_check(stage_override="paper")
        round_trip_gate = next(g for g in result["gates"] if "round trips" in g["label"])
        expectancy_gate = next(g for g in result["gates"] if "Expectancy" in g["label"])

        assert result["paper_history"]["fills"] == 14
        assert result["paper_history"]["closed_trades"] == 7
        assert "7 round trips recorded from trade_journal_sqlite" in round_trip_gate["detail"]
        assert expectancy_gate["passed"] is True
        assert expectancy_gate["detail"] == "avg pnl/round trip = $10.00 from trade_journal_sqlite"
        assert result["retirement"]["source"] == "trade_journal_sqlite"
        assert result["retirement"]["triggers_fired"] == []

    def test_latest_session_health_ignores_resolved_old_critical_errors(self, tmp_path):
        from scripts.check_promotion_gates import _latest_session_health

        result = _latest_session_health([
            {"timestamp": "2026-05-01T00:00:00+00:00", "critical_error": True},
            {"timestamp": "2026-05-02T00:00:00+00:00", "critical_error": False},
        ])

        assert result["ok"] is True
        assert result["window_date"] == "2026-05-02"
        assert result["critical_error_count"] == 0

    def test_latest_session_health_fails_current_critical_errors(self, tmp_path):
        from scripts.check_promotion_gates import _latest_session_health

        result = _latest_session_health([
            {"timestamp": "2026-05-01T00:00:00+00:00", "critical_error": False},
            {"timestamp": "2026-05-02T00:00:00+00:00", "critical_error": True},
        ])

        assert result["ok"] is False
        assert result["window_date"] == "2026-05-02"
        assert result["critical_error_count"] == 1

    def test_latest_evidence_log_presence_uses_latest_window(self, tmp_path):
        from scripts.check_promotion_gates import _latest_evidence_log_presence

        result = _latest_evidence_log_presence({
            "signal": [
                {"timestamp": "2026-05-01T00:00:00+00:00"},
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
            "order": [
                {"timestamp": "2026-05-01T00:00:00+00:00"},
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
            "fill": [
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
            "session": [
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
        })

        assert result["ok"] is True
        assert result["window_date"] == "2026-05-02"
        assert result["counts"] == {"signal": 1, "order": 1, "fill": 1, "session": 1}
        assert result["detail"] == "window:2026-05-02 signal:1 order:1 fill:1 session:1"

    def test_latest_evidence_log_presence_allows_no_trade_window(self, tmp_path):
        from scripts.check_promotion_gates import _latest_evidence_log_presence

        result = _latest_evidence_log_presence({
            "signal": [
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
            "order": [],
            "fill": [],
            "session": [
                {
                    "timestamp": "2026-05-02T00:00:00+00:00",
                    "phase": "end",
                    "campaign_status": "completed",
                },
            ],
        })

        assert result["ok"] is True
        assert result["trade_evidence_expected"] is False
        assert result["no_trade_window"] is True
        assert result["detail"] == "window:2026-05-02 signal:1 order:0 fill:0 session:1 no_trade_window:true"

    def test_latest_evidence_log_presence_fails_incomplete_trade_window(self, tmp_path):
        from scripts.check_promotion_gates import _latest_evidence_log_presence

        result = _latest_evidence_log_presence({
            "signal": [
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
            "order": [
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
            "fill": [],
            "session": [
                {"timestamp": "2026-05-02T00:00:00+00:00"},
            ],
        })

        assert result["ok"] is False
        assert result["trade_evidence_expected"] is True
        assert result["no_trade_window"] is False
        assert result["hint"] == "order/fill evidence is incomplete for latest trade window"


class TestEvidenceProvenance:
    def test_provenance_summary_flags_missing_source(self, tmp_path):
        from scripts.check_promotion_gates import _evidence_provenance_summary
        evidence = {
            "signal": [{"record_type": "signal"}],
            "order": [],
            "fill": [],
            "session": [],
        }
        result = _evidence_provenance_summary(evidence)
        assert result["ok"] is False
        assert result["missing"] == 1

    def test_provenance_summary_reports_unknown_source_breakdown(self, tmp_path):
        from scripts.check_promotion_gates import _evidence_provenance_summary, _provenance_gate_detail
        evidence = {
            "signal": [
                {"record_type": "signal", "market_data_source": "unknown_ohlcv"},
                {"record_type": "signal", "market_data_source": "unknown_ohlcv"},
                {"record_type": "signal", "market_data_source": "custom_feed"},
            ],
            "order": [],
            "fill": [],
            "session": [],
        }

        result = _evidence_provenance_summary(evidence)
        detail = _provenance_gate_detail({**result, "window_date": "2026-05-26"})

        assert result["unknown"] == 3
        assert result["unknown_sources"] == {"custom_feed": 1, "unknown_ohlcv": 2}
        assert result["by_type"]["signal"]["unknown_sources"] == {"custom_feed": 1, "unknown_ohlcv": 2}
        assert "unknown_sources:custom_feed=1,unknown_ohlcv=2" in detail

    def test_provenance_summary_flags_sample_source(self, tmp_path):
        from scripts.check_promotion_gates import _evidence_provenance_summary
        evidence = {
            "signal": [{
                "record_type": "signal",
                "market_data_source": "sample_ohlcv",
                "ohlcv_sample_mode": True,
            }],
            "order": [],
            "fill": [],
            "session": [],
        }
        result = _evidence_provenance_summary(evidence)
        assert result["ok"] is False
        assert result["sample"] == 1

    def test_provenance_summary_passes_public_source(self, tmp_path):
        from scripts.check_promotion_gates import _evidence_provenance_summary
        evidence = {
            record_type: [{
                "record_type": record_type,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
            }]
            for record_type in ("signal", "order", "fill", "session")
        }
        result = _evidence_provenance_summary(evidence)
        assert result["ok"] is True
        assert result["public"] == 4
        assert result["missing"] == 0
        assert result["sample"] == 0
        assert result["unknown"] == 0

    def test_promotion_provenance_uses_latest_dated_window(self, tmp_path):
        from scripts.check_promotion_gates import (
            _evidence_provenance_summary,
            _promotion_provenance_summary,
        )
        evidence = {
            "signal": [
                {"record_type": "signal", "timestamp": "2026-05-01T00:00:00+00:00"},
                {
                    "record_type": "signal",
                    "timestamp": "2026-05-02T00:00:00+00:00",
                    "market_data_source": "public_ohlcv",
                    "ohlcv_sample_mode": False,
                },
            ],
            "order": [{
                "record_type": "order",
                "timestamp": "2026-05-02T00:00:00+00:00",
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
            }],
            "fill": [{
                "record_type": "fill",
                "timestamp": "2026-05-02T00:00:00+00:00",
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
            }],
            "session": [{
                "record_type": "session",
                "timestamp": "2026-05-02T00:00:00+00:00",
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
            }],
        }

        all_time = _evidence_provenance_summary(evidence)
        latest = _promotion_provenance_summary(evidence)

        assert all_time["missing"] == 1
        assert latest["ok"] is True
        assert latest["window"] == "latest_date"
        assert latest["window_date"] == "2026-05-02"
        assert latest["public"] == 4
        assert latest["missing"] == 0

    def test_paper_gate_blocks_legacy_unstamped_evidence(self, tmp_path):
        from services.os.app_paths import data_dir
        from services.strategies.evidence_logger import EvidenceLogger
        from scripts.check_promotion_gates import run_check
        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
        logger.log_signal(
            timestamp=_now(), price=5000.0, sma_200=4800.0,
            atr_ratio=1.1, signal_direction="long", regime_flag="trending",
        )
        result = run_check(stage_override="paper")
        gate = next(g for g in result["gates"] if "provenance" in g["label"].lower())
        assert gate["passed"] is False
        assert result["provenance"]["missing"] == 1


class TestSlippageBaseline:
    def test_no_fills_returns_unknown(self, tmp_path):
        from scripts.check_promotion_gates import _slippage_within_baseline
        result = _slippage_within_baseline([])
        assert result["ok"] is None

    def test_insufficient_fills_returns_unknown(self, tmp_path):
        from scripts.check_promotion_gates import _slippage_within_baseline
        fills = [{"slippage_pct": 0.1}] * 3  # fewer than 5
        result = _slippage_within_baseline(fills)
        assert result["ok"] is None

    def test_low_slippage_passes(self, tmp_path):
        from scripts.check_promotion_gates import _slippage_within_baseline
        fills = [{"slippage_pct": 0.05}] * 20
        result = _slippage_within_baseline(fills)
        assert result["ok"] is True

    def test_high_slippage_fails(self, tmp_path):
        from scripts.check_promotion_gates import _slippage_within_baseline
        fills = [{"slippage_pct": 1.5}] * 20  # way above 0.10 baseline × 1.5
        result = _slippage_within_baseline(fills)
        assert result["ok"] is False
