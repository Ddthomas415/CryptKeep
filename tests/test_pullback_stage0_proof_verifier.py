from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from services.analytics import pullback_stage0_proof_verifier as verifier


def _journal(path: Path, *, count: int, strategy_id: str = "pullback_recovery_default") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as con:
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
        for idx in range(count):
            con.execute(
                """
                INSERT INTO journal_fills(
                  fill_id, journal_ts, strategy_id, order_id, fill_ts, venue, symbol,
                  side, qty, price, fee, fee_currency
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    f"fill-{idx}",
                    f"2026-06-29T19:0{idx}:00+00:00",
                    strategy_id,
                    f"order-{idx}",
                    f"2026-06-29T19:0{idx}:00+00:00",
                    "coinbase",
                    "BTC/USDT",
                    "buy",
                    1.0,
                    100.0,
                    0.0,
                    "USD",
                ),
            )


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_session(path: Path, *, commit: str, timestamp: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "record_type": "session",
                "timestamp": timestamp,
                "phase": "end",
                "campaign_status": "completed",
                "reconciliation_result": "pass",
                "critical_error": False,
                "ops_checks_passed": True,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_timeframe": "5m",
                "ohlcv_venue": "coinbase",
                "ohlcv_symbol": "BTC/USDT",
                "strategy_id": "pullback_recovery_default",
                "_strategy_id": "pullback_recovery_default",
                "_commit": commit,
            }
        )
        + "\n",
        encoding="utf-8",
    )


def _proof_state(root: Path, *, commit: str) -> None:
    state = root / ".cbp_state_challengers" / "pullback_recovery_default"
    _write_session(
        state / "data" / "evidence" / "pullback_recovery_default" / "session_2026-06-29.jsonl",
        commit=commit,
        timestamp="2026-06-29T19:30:00+00:00",
    )
    _write_json(
        state / "runtime" / "flags" / "strategy_runner.status.json",
        {
            "strategy_id": "pullback_recovery",
            "strategy_preset": "pullback_recovery_default",
            "signal_source": "public_ohlcv_5m",
        },
    )
    _write_json(
        state / "runtime" / "health" / "paper_strategy_evidence.json",
        {"status": "completed", "reason": "completed"},
    )


def test_pullback_stage0_baseline_records_counts_without_starting_campaigns(tmp_path: Path) -> None:
    _journal(tmp_path / ".cbp_state" / "data" / "trade_journal.sqlite", count=3)
    _journal(
        tmp_path
        / ".cbp_state_challengers"
        / "pullback_recovery_default"
        / "data"
        / "trade_journal.sqlite",
        count=1,
    )

    report = verifier.build_pullback_stage0_baseline(repo_root=tmp_path, expected_commit="abc123")

    assert report["report_type"] == verifier.BASELINE_REPORT_TYPE
    assert report["expected_commit"] == "abc123"
    assert report["canonical_journal"]["count"] == 3
    assert report["challenger_journal"]["count"] == 1
    assert all(report["safety"][key] is False for key in report["safety"])


def test_pullback_stage0_verification_passes_with_matching_baseline(tmp_path: Path) -> None:
    _journal(tmp_path / ".cbp_state" / "data" / "trade_journal.sqlite", count=3)
    _proof_state(tmp_path, commit="abc123")
    baseline = {
        "generated_at": "2026-06-29T19:00:00+00:00",
        "expected_commit": "abc123",
        "canonical_journal": {"count": 3},
    }

    report = verifier.build_pullback_stage0_verification(repo_root=tmp_path, baseline=baseline)

    assert report["status"] == "passed"
    assert report["passed"] is True
    assert report["blocking_checks"] == []


def test_pullback_stage0_verification_requires_baseline(tmp_path: Path) -> None:
    _proof_state(tmp_path, commit="abc123")

    report = verifier.build_pullback_stage0_verification(repo_root=tmp_path, baseline={})

    assert report["status"] == "incomplete"
    assert report["passed"] is False
    assert any(check["name"] == "baseline_loaded" for check in report["blocking_checks"])


def test_write_pullback_stage0_baseline_only_writes_report_artifacts(
    monkeypatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    report = verifier.build_pullback_stage0_baseline(repo_root=tmp_path, expected_commit="abc123")

    paths = verifier.write_pullback_stage0_baseline(report)

    latest = (
        tmp_path
        / "data"
        / "pullback_stage0_verification"
        / "pullback_stage0_baseline.latest.json"
    )
    assert paths["latest_json"] == str(latest)
    assert json.loads(latest.read_text(encoding="utf-8"))["report_type"] == (
        verifier.BASELINE_REPORT_TYPE
    )
    assert not (tmp_path / "runtime" / "flags").exists()
