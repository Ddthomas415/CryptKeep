"""tests/test_evidence_logger.py — Evidence logger and gate checker tests."""
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


# ---------------------------------------------------------------------------
# EvidenceLogger
# ---------------------------------------------------------------------------

class TestEvidenceLogger:
    def test_log_signal_writes_jsonl(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        logger.log_signal(
            timestamp=_now(), price=5000.0, sma_200=4800.0,
            atr_ratio=1.2, signal_direction="long", regime_flag="trending",
        )
        files = list((tmp_path / "ev").glob("signal_*.jsonl"))
        assert len(files) == 1
        rec = json.loads(files[0].read_text().strip())
        assert rec["signal_direction"] == "long"
        assert rec["regime_flag"] == "trending"
        assert rec["price"] == 5000.0

    def test_log_order_writes_jsonl(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        logger.log_order(
            timestamp=_now(), order_type="market", size=1.0,
            intended_price=5000.0, stop_level=4900.0, capital_at_risk_usd=500.0,
        )
        files = list((tmp_path / "ev").glob("order_*.jsonl"))
        assert len(files) == 1
        rec = json.loads(files[0].read_text().strip())
        assert rec["capital_at_risk_usd"] == 500.0
        assert rec["stop_level"] == 4900.0

    def test_log_fill_includes_pnl(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        logger.log_fill(
            timestamp=_now(), fill_price=5005.0,
            slippage_points=5.0, slippage_pct=0.1, fees_paid=2.50,
            pnl_usd=150.0, side="sell",
        )
        files = list((tmp_path / "ev").glob("fill_*.jsonl"))
        assert len(files) == 1
        rec = json.loads(files[0].read_text().strip())
        assert rec["pnl_usd"] == 150.0
        assert rec["slippage_pct"] == 0.1

    def test_log_session_writes_all_required_fields(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        logger.log_session(
            regime_at_open="trending", halts_triggered=[],
            manual_overrides=[], reconciliation_result="pass",
            drawdown_from_peak=0.02,
        )
        files = list((tmp_path / "ev").glob("session_*.jsonl"))
        assert len(files) == 1
        rec = json.loads(files[0].read_text().strip())
        required = ["regime_at_open", "halts_triggered", "manual_overrides",
                    "reconciliation_result", "drawdown_from_peak"]
        for f in required:
            assert f in rec, f"missing field: {f}"

    def test_log_drawdown_calculates_pct(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        logger.log_drawdown(
            peak_equity=100_000.0, trough_equity=88_000.0,
            duration_days=14, action_taken="halved",
        )
        files = list((tmp_path / "ev").glob("drawdown_*.jsonl"))
        rec = json.loads(files[0].read_text().strip())
        assert abs(rec["drawdown_pct"] - 12.0) < 0.01

    def test_multiple_signals_append_to_same_file(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        for i in range(5):
            logger.log_signal(
                timestamp=_now(), price=5000.0 + i, sma_200=4800.0,
                atr_ratio=1.0, signal_direction="long", regime_flag="trending",
            )
        files = list((tmp_path / "ev").glob("signal_*.jsonl"))
        assert len(files) == 1
        records = [json.loads(l) for l in files[0].read_text().strip().splitlines()]
        assert len(records) == 5

    def test_record_type_tag_is_set(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("test_strat", log_dir=tmp_path / "ev")
        logger.log_signal(
            timestamp=_now(), price=5000.0, sma_200=4800.0,
            atr_ratio=1.0, signal_direction="flat", regime_flag="chop",
        )
        files = list((tmp_path / "ev").glob("signal_*.jsonl"))
        rec = json.loads(files[0].read_text().strip())
        assert rec["record_type"] == "signal"

    def test_strategy_id_is_tagged(self, tmp_path):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("my_strategy", log_dir=tmp_path / "ev")
        logger.log_signal(
            timestamp=_now(), price=100.0, sma_200=90.0,
            atr_ratio=1.0, signal_direction="long", regime_flag="trending",
        )
        files = list((tmp_path / "ev").glob("signal_*.jsonl"))
        rec = json.loads(files[0].read_text().strip())
        assert rec["strategy_id"] == "my_strategy"


# ---------------------------------------------------------------------------
# check_promotion_gates
# ---------------------------------------------------------------------------

class TestPromotionGateChecker:
    def _write_signal(self, ev_dir: Path, regime: str = "trending", n: int = 1):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
        for _ in range(n):
            logger.log_signal(
                timestamp=_now(), price=5000.0, sma_200=4800.0,
                atr_ratio=1.1, signal_direction="long", regime_flag=regime,
            )

    def _write_session(self, ev_dir: Path, **kwargs):
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
        logger.log_session(
            regime_at_open=kwargs.get("regime_at_open", "trending"),
            halts_triggered=kwargs.get("halts_triggered", []),
            manual_overrides=kwargs.get("manual_overrides", []),
            reconciliation_result=kwargs.get("reconciliation_result", "pass"),
            drawdown_from_peak=kwargs.get("drawdown_from_peak", 0.0),
            kill_switch_tested=kwargs.get("kill_switch_tested", False),
        )

    def test_no_evidence_gives_fail_on_evidence_gate(self, tmp_path):
        from scripts.check_promotion_gates import run_check
        result = run_check()
        gate = next(g for g in result["gates"] if "evidence logs" in g["label"].lower())
        assert gate["passed"] is False

    def test_with_signal_evidence_schema_passes(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        self._write_signal(ev_dir, n=3)

        from scripts.check_promotion_gates import run_check
        result = run_check()
        assert result["schema"]["signal"]["ok"] is True
        assert result["schema"]["signal"]["total"] == 3

    def test_regime_block_detected_from_signal_logs(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        self._write_signal(ev_dir, regime="chop", n=1)

        from scripts.check_promotion_gates import _load_all_evidence, _any_regime_block
        evidence = _load_all_evidence(ev_dir)
        assert _any_regime_block(evidence["signal"]) is True

    def test_kill_switch_gate_passes_when_logged(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        self._write_session(ev_dir, kill_switch_tested=True)

        from scripts.check_promotion_gates import _load_all_evidence, _kill_switch_tested
        evidence = _load_all_evidence(ev_dir)
        assert _kill_switch_tested(evidence["session"]) is True

    def test_json_output_is_valid(self, tmp_path):
        from scripts.check_promotion_gates import run_check
        result = run_check()
        # Must be JSON serializable
        json.dumps(result, default=str)
        assert "stage" in result
        assert "gates" in result
        assert "schema" in result
        assert "ready" in result

    def test_schema_validation_detects_missing_fields(self, tmp_path):
        from services.os.app_paths import data_dir
        from scripts.check_promotion_gates import _validate_schema
        records = [{"timestamp": "2026-01-01", "price": 100.0}]  # missing required fields
        required = ["timestamp", "price", "sma_200", "atr_ratio",
                    "signal_direction", "regime_flag"]
        result = _validate_schema(records, required, "signal")
        assert result["ok"] is False
        assert result["bad_records"] == 1

    def test_days_of_operation_counts_unique_dates(self, tmp_path):
        from services.os.app_paths import data_dir
        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        from services.strategies.evidence_logger import EvidenceLogger
        logger = EvidenceLogger("es_daily_trend_v1", log_dir=ev_dir)
        # Same date — only counts as 1 day
        for _ in range(3):
            logger.log_session(
                regime_at_open="trending", halts_triggered=[],
                manual_overrides=[], reconciliation_result="pass",
                drawdown_from_peak=0.0,
            )
        from scripts.check_promotion_gates import _load_all_evidence, _days_of_operation
        evidence = _load_all_evidence(ev_dir)
        days = _days_of_operation(evidence["session"])
        assert days == 1  # all same day
