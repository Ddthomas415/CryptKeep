"""tests/test_check_promotion_gates.py

Tests for scripts/check_promotion_gates.py — the promotion decision engine.

This is what tells the operator whether it's safe to promote. A bug here
means either: gates pass when they shouldn't, or gates fail spuriously.
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
