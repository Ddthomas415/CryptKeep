from __future__ import annotations

import json
import sqlite3

from services.signals.candidate_outcomes import (
    build_candidate_outcome_report,
    write_candidate_outcome_report,
)
from services.signals.candidate_store import write_candidates


def _write_fills(tmp_path, rows: list[tuple[str, str, str, float]]) -> None:
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    db = data_dir / "trade_journal.sqlite"
    con = sqlite3.connect(str(db))
    con.execute(
        "CREATE TABLE fills (symbol TEXT, side TEXT, status TEXT, realized_pnl REAL)"
    )
    con.executemany(
        "INSERT INTO fills (symbol, side, status, realized_pnl) VALUES (?, ?, ?, ?)",
        rows,
    )
    con.commit()
    con.close()


def test_candidate_outcome_report_marks_empty_history_insufficient(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    report = build_candidate_outcome_report()

    assert report["status"] == "insufficient_candidate_history"
    assert report["summary"]["insufficient_history"] is True
    assert report["summary"]["candidates_reviewed"] == 0
    assert report["safety"]["read_only"] is True
    assert report["safety"]["candidate_advisor_enabled"] is False
    assert report["safety"]["orders_routed"] is False


def test_candidate_outcome_report_marks_history_without_outcomes(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    write_candidates(
        [
            {
                "symbol": "BTC/USDT",
                "composite_score": 72.0,
                "trade_type": "swing_trade",
                "preferred_strategy": "pullback_recovery",
            }
        ],
        scan_id="scan-1",
    )

    report = build_candidate_outcome_report(limit=5, top_n=1)

    assert report["status"] == "no_candidate_outcome_data"
    assert report["summary"]["snapshots_reviewed"] == 1
    assert report["summary"]["candidates_reviewed"] == 1
    assert report["summary"]["candidates_with_outcome_data"] == 0
    assert report["summary"]["no_outcome_count"] == 1


def test_candidate_outcome_report_summarizes_matching_closed_outcomes(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    write_candidates(
        [
            {
                "symbol": "BTC/USDT",
                "composite_score": 80.0,
                "trade_type": "swing_trade",
                "preferred_strategy": "pullback_recovery",
            },
            {
                "symbol": "ETH/USDT",
                "composite_score": 60.0,
                "trade_type": "quick_flip",
                "preferred_strategy": "momentum",
            },
        ],
        scan_id="scan-1",
    )
    _write_fills(
        tmp_path,
        [
            ("BTC/USDT", "sell", "closed", 10.0),
            ("ETH/USDT", "sell", "closed", -5.0),
        ],
    )

    report = build_candidate_outcome_report(limit=5, top_n=2)

    assert report["status"] == "ok"
    assert report["summary"]["candidates_reviewed"] == 2
    assert report["summary"]["candidates_with_outcome_data"] == 2
    assert report["summary"]["top_rank"]["closed_trades"] == 1
    assert report["summary"]["top_rank"]["net_pnl"] == 10.0
    assert report["summary"]["top_rank"]["win_rate_pct"] == 100.0
    assert report["summary"]["non_top_rank"]["closed_trades"] == 1
    assert report["summary"]["non_top_rank"]["net_pnl"] == -5.0
    assert report["rows"][0]["verdict"] == "positive_top_rank"
    assert report["rows"][1]["verdict"] == "negative"


def test_candidate_outcome_report_writes_latest_and_dated_artifacts(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = build_candidate_outcome_report()

    paths = write_candidate_outcome_report(report)

    latest = tmp_path / "data" / "candidate_outcomes" / "candidate_outcomes.latest.json"
    assert paths["latest"] == str(latest)
    assert latest.exists()
    assert json.loads(latest.read_text(encoding="utf-8"))["report_type"] == "candidate_outcomes"
    assert paths["dated"].endswith(".json")
