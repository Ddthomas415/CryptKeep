"""tests/test_check_promotion_gates.py

Tests for scripts/check_promotion_gates.py — the promotion decision engine.

This is what tells the operator whether it's safe to promote. A bug here
means either: gates pass when they shouldn't, or gates fail spuriously.
"""
from __future__ import annotations
import json
import sqlite3
import pytest
import yaml
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

    def test_passed_gate_suppresses_remediation_hint(self, tmp_path):
        from scripts.check_promotion_gates import _gate

        passed = _gate("already done", True, "ok", "fix this")
        failed = _gate("not done", False, "bad", "fix this")
        unknown = _gate("unknown", None, "unknown", "check this")

        assert passed["hint"] == ""
        assert failed["hint"] == "fix this"
        assert unknown["hint"] == "check this"

    def test_json_output_surfaces_blocking_backtest_comparison(self, tmp_path):
        from scripts.check_promotion_gates import run_check

        result = run_check(stage_override="paper")

        assert result["manual_review_required"] is True
        assert result["machine_ready"] is False
        review = result["manual_review"]
        assert review["required"] is True
        assert any(
            item["id"] == "win_rate_avg_win_loss_vs_backtest"
            and item["status"] == "machine_blocking"
            and "win_rate" in item["reason"]
            for item in review["outstanding_items"]
        )

    def test_backtest_expectation_item_passes_when_configured_metrics_match(self, tmp_path):
        from scripts.check_promotion_gates import _paper_manual_review_status

        result = _paper_manual_review_status(
            {
                "closed_trades": 10,
                "fills": 20,
                "win_rate": 0.50,
                "avg_win": 12.0,
                "avg_loss": -9.0,
                "net_realized_pnl": 30.0,
                "expectancy_per_closed_trade": 3.0,
            },
            [],
            {
                "promotion": {
                    "paper": {
                        "backtest_expectations": {
                            "source": "unit-test-baseline",
                            "tolerance_pct": 25.0,
                            "win_rate": 0.50,
                            "avg_win": 10.0,
                            "avg_loss": -8.0,
                        }
                    }
                }
            },
        )

        assert result["required"] is False
        item = result["items"][0]
        assert item["status"] == "machine_checked"
        assert all(comparison["passed"] is True for comparison in item["comparisons"])

    def test_backtest_expectation_item_blocks_when_configured_metrics_miss(self, tmp_path):
        from scripts.check_promotion_gates import _paper_manual_review_status

        result = _paper_manual_review_status(
            {
                "closed_trades": 10,
                "fills": 20,
                "win_rate": 0.25,
                "avg_win": 12.0,
                "avg_loss": -9.0,
                "net_realized_pnl": 30.0,
                "expectancy_per_closed_trade": 3.0,
            },
            [],
            {
                "promotion": {
                    "paper": {
                        "backtest_expectations": {
                            "source": "unit-test-baseline",
                            "tolerance_pct": 25.0,
                            "win_rate": 0.50,
                            "avg_win": 10.0,
                            "avg_loss": -8.0,
                        }
                    }
                }
            },
        )

        assert result["required"] is True
        item = result["outstanding_items"][0]
        assert item["status"] == "machine_blocking"
        assert any(
            comparison["metric"] == "win_rate" and comparison["passed"] is False
            for comparison in item["comparisons"]
        )

    def test_backtest_expectation_item_compares_normalized_trade_returns(self):
        from scripts.check_promotion_gates import _paper_manual_review_status

        result = _paper_manual_review_status(
            {
                "closed_trades": 10,
                "fills": 20,
                "win_rate": 0.25,
                "avg_win_return_pct": 8.0,
                "avg_loss_return_pct": -4.0,
                "net_realized_pnl": 30.0,
                "expectancy_per_closed_trade": 3.0,
            },
            [],
            {
                "promotion": {
                    "paper": {
                        "backtest_expectations": {
                            "source": "unit-test-normalized-baseline",
                            "metric_basis": "net_return_pct",
                            "tolerance_pct": 25.0,
                            "win_rate": 0.25,
                            "avg_win_return_pct": 10.0,
                            "avg_loss_return_pct": -5.0,
                        }
                    }
                }
            },
        )

        assert result["required"] is False
        item = result["items"][0]
        assert item["baseline"]["metric_basis"] == "net_return_pct"
        assert [comparison["metric"] for comparison in item["comparisons"]] == [
            "win_rate",
            "avg_win_return_pct",
            "avg_loss_return_pct",
        ]
        assert all(comparison["passed"] is True for comparison in item["comparisons"])


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

    def test_paper_gate_does_not_count_unprovenanced_trade_journal_history(self, tmp_path):
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

        assert result["paper_history"]["fills"] == 0
        assert result["paper_history"]["closed_trades"] == 0
        assert result["paper_history"]["all_history_fills"] == 14
        assert result["paper_history"]["all_history_closed_trades"] == 7
        assert result["paper_history"]["qualification"]["qualified_evidence_fills"] == 0
        assert "0 round trips recorded" in round_trip_gate["detail"]
        assert "(0/10, 10 remaining)" in round_trip_gate["detail"]
        assert expectancy_gate["passed"] is None
        assert result["retirement"]["source"] == "jsonl_provenance+trade_journal_sqlite"
        assert result["retirement"]["triggers_fired"] == []

    def test_paper_gate_counts_only_round_trips_with_matching_provenance(self, tmp_path):
        from services.os.app_paths import data_dir
        from scripts.check_promotion_gates import run_check

        ev_dir = data_dir() / "evidence" / "es_daily_trend_v1"
        ev_dir.mkdir(parents=True, exist_ok=True)
        fills = []
        for idx, side in enumerate(("buy", "sell")):
            fills.append({
                "record_type": "fill",
                "timestamp": f"2026-05-01T0{idx}:00:00+00:00",
                "side": side,
                "size": 1.0,
                "order_id": f"order-{side}",
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_timeframe": "1d",
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "BTC/USDT",
            })
        (ev_dir / "fill_2026-05-01.jsonl").write_text(
            "\n".join(json.dumps(row) for row in fills) + "\n",
            encoding="utf-8",
        )

        journal = data_dir() / "trade_journal.sqlite"
        con = sqlite3.connect(str(journal))
        try:
            con.execute(
                """
                CREATE TABLE journal_fills (
                  fill_id TEXT PRIMARY KEY,
                  journal_ts TEXT NOT NULL,
                  strategy_id TEXT,
                  order_id TEXT NOT NULL,
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
            con.executemany(
                "INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                [
                    ("fill-buy", fills[0]["timestamp"], "sma_200_trend", "order-buy", fills[0]["timestamp"], "coinbase", "BTC/USDT", "buy", 1.0, 100.0, 0.1, "USD"),
                    ("fill-sell", fills[1]["timestamp"], "sma_200_trend", "order-sell", fills[1]["timestamp"], "coinbase", "BTC/USDT", "sell", 1.0, 110.0, 0.1, "USD"),
                ],
            )
            con.commit()
        finally:
            con.close()

        result = run_check(stage_override="paper")
        round_trip_gate = next(g for g in result["gates"] if "round trips" in g["label"])

        assert result["paper_history"]["fills"] == 2
        assert result["paper_history"]["closed_trades"] == 1
        assert result["paper_history"]["all_history_closed_trades"] == 1
        assert result["paper_history"]["qualification"]["unqualified_evidence_fills"] == 0
        assert "(1/10, 9 remaining)" in round_trip_gate["detail"]

    def test_paper_gate_rejects_round_trip_with_wrong_timeframe(self, tmp_path):
        from services.control.paper_evidence_qualification import qualify_paper_history
        from scripts.check_promotion_gates import CONFIG_PATH

        journal = tmp_path / "trade_journal.sqlite"
        con = sqlite3.connect(str(journal))
        try:
            con.execute(
                """
                CREATE TABLE journal_fills (
                  fill_id TEXT PRIMARY KEY,
                  journal_ts TEXT NOT NULL,
                  order_id TEXT NOT NULL,
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
            con.executemany(
                "INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    ("fill-buy", "2026-05-01T00:00:00+00:00", "order-buy", "2026-05-01T00:00:00+00:00", "coinbase", "BTC/USDT", "buy", 1.0, 100.0, 0.1, "USD"),
                    ("fill-sell", "2026-05-01T01:00:00+00:00", "order-sell", "2026-05-01T01:00:00+00:00", "coinbase", "BTC/USDT", "sell", 1.0, 110.0, 0.1, "USD"),
                ],
            )
            con.commit()
        finally:
            con.close()

        fills = [
            {
                "timestamp": f"2026-05-01T0{idx}:00:00+00:00",
                "side": side,
                "size": 1.0,
                "order_id": f"order-{side}",
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_timeframe": "1m",
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "BTC/USDT",
            }
            for idx, side in enumerate(("buy", "sell"))
        ]
        config = yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8"))

        result = qualify_paper_history(
            evidence_fills=fills,
            config=config,
            journal_path=str(journal),
        )

        assert result["closed_trades"] == 0
        assert result["qualification"]["unqualified_evidence_fills"] == 2
        assert result["qualification"]["unqualified_reason_counts"] == {
            "ohlcv_timeframe_mismatch": 2
        }

    def test_paper_gate_does_not_bridge_across_unqualified_trade_legs(self, tmp_path):
        from services.control.paper_evidence_qualification import qualify_paper_history
        from scripts.check_promotion_gates import CONFIG_PATH

        journal = tmp_path / "trade_journal.sqlite"
        con = sqlite3.connect(str(journal))
        try:
            con.execute(
                """
                CREATE TABLE journal_fills (
                  fill_id TEXT PRIMARY KEY,
                  journal_ts TEXT NOT NULL,
                  order_id TEXT NOT NULL,
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
            con.executemany(
                "INSERT INTO journal_fills VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                [
                    (f"fill-{idx}", f"2026-05-01T0{idx}:00:00+00:00", f"order-{idx}", f"2026-05-01T0{idx}:00:00+00:00", "coinbase", "BTC/USDT", side, 1.0, price, 0.1, "USD")
                    for idx, (side, price) in enumerate(
                        (("buy", 100.0), ("sell", 101.0), ("buy", 102.0), ("sell", 103.0))
                    )
                ],
            )
            con.commit()
        finally:
            con.close()

        fills = []
        for idx, side in enumerate(("buy", "sell", "buy", "sell")):
            fill = {
                "timestamp": f"2026-05-01T0{idx}:00:00+00:00",
                "side": side,
                "size": 1.0,
                "order_id": f"order-{idx}",
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_timeframe": "1d",
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "BTC/USDT",
            }
            if idx in {1, 2}:
                fill.pop("market_data_source")
            fills.append(fill)

        result = qualify_paper_history(
            evidence_fills=fills,
            config=yaml.safe_load(CONFIG_PATH.read_text(encoding="utf-8")),
            journal_path=str(journal),
        )

        assert result["closed_trades"] == 0
        assert result["qualification"]["provenance_qualified_evidence_fills"] == 2
        assert result["qualification"]["qualified_evidence_fills"] == 0
        assert result["qualification"]["completed_evidence_round_trips"] == 0

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

    def test_paper_threshold_gates_report_remaining_counts(self, tmp_path):
        from scripts.check_promotion_gates import evaluate_paper_gates

        evidence = {
            "signal": [{"timestamp": "2026-05-02T00:00:00+00:00", "market_data_source": "public_ohlcv"}],
            "order": [],
            "fill": [],
            "session": [{"timestamp": "2026-05-02T00:00:00+00:00", "market_data_source": "public_ohlcv"}],
        }
        sessions = [
            {"timestamp": f"2026-05-{day:02d}T00:00:00+00:00"}
            for day in range(1, 23)
        ]
        paper_history = {
            "ok": True,
            "source": "trade_journal_sqlite",
            "fills": 14,
            "closed_trades": 7,
            "expectancy_per_closed_trade": 5.0,
        }

        gates = evaluate_paper_gates(evidence, sessions, evidence["signal"], evidence["fill"], paper_history)
        day_gate = next(g for g in gates if g["label"] == "30 calendar days of operation")
        round_trip_gate = next(g for g in gates if g["label"] == "10+ completed round trips")

        assert day_gate["detail"] == "22/30 days recorded (8 remaining)"
        assert "(7/10, 3 remaining)" in round_trip_gate["detail"]


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


class TestShadowGateMarketQuality:
    def test_shadow_gate_accepts_spread_bps_signal_evidence(self):
        from scripts.check_promotion_gates import evaluate_shadow_gates

        gates = evaluate_shadow_gates(
            {},
            [{"timestamp": "2026-05-01T00:00:00+00:00", "ops_checks_passed": True}],
            [{"timestamp": "2026-05-01T00:00:00+00:00", "spread_bps": 4.2}],
            [],
        )

        gate = next(g for g in gates if g["label"] == "All signals logged with spread/depth data")
        assert gate["passed"] is True

    def test_shadow_gate_blocks_signals_without_spread_or_depth(self):
        from scripts.check_promotion_gates import evaluate_shadow_gates

        gates = evaluate_shadow_gates(
            {},
            [{"timestamp": "2026-05-01T00:00:00+00:00", "ops_checks_passed": True}],
            [{"timestamp": "2026-05-01T00:00:00+00:00", "price": 100.0}],
            [],
        )

        gate = next(g for g in gates if g["label"] == "All signals logged with spread/depth data")
        assert gate["passed"] is False
