import json
from pathlib import Path

from services.analytics import funding_stage0_proof_verifier as verifier


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")


def test_funding_stage0_baseline_records_counts_without_starting_campaigns(tmp_path: Path) -> None:
    report = verifier.build_funding_stage0_baseline(repo_root=tmp_path, expected_commit="abc123")

    assert report["report_type"] == verifier.BASELINE_REPORT_TYPE
    assert report["expected_commit"] == "abc123"
    assert report["read_only"] is True
    assert report["safety"]["collector_invoked"] is False


def test_funding_stage0_verification_passes_with_matching_baseline(tmp_path: Path) -> None:
    baseline = {
        "generated_at": "2026-07-11T20:00:00+00:00",
        "expected_commit": "abc123",
        "canonical_journal": {"count": 0},
    }
    state_root = tmp_path / verifier.STATE_DIR_REL
    evidence_dir = state_root / "data" / "evidence" / verifier.SESSION_STRATEGY_ID
    _write_jsonl(
        evidence_dir / "session_2026-07-11.jsonl",
        [
            {
                "record_type": "session",
                "phase": "end",
                "campaign_status": "completed",
                "timestamp": "2026-07-11T20:20:00+00:00",
                "_commit": "abc123",
                "reconciliation_result": "pass",
                "critical_error": False,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_timeframe": "5m",
                "ohlcv_venue": verifier.VENUE,
                "ohlcv_symbol": verifier.SYMBOL,
                "strategy_id": verifier.SESSION_STRATEGY_ID,
                "_strategy_id": verifier.SESSION_STRATEGY_ID,
            }
        ],
    )
    _write_json(
        state_root / "runtime" / "flags" / "strategy_runner.status.json",
        {
            "strategy_preset": verifier.SESSION_STRATEGY_ID,
            "signal_source": verifier.SIGNAL_SOURCE,
            "signal_ok": True,
            "signal_reason": "funding_neutral",
            "strategy_context_ok": True,
            "strategy_context_reason": "funding_context_ready",
            "strategy_context_source": verifier.CONTEXT_SOURCE,
            "strategy_context_symbol": verifier.CONTEXT_SYMBOL,
            "strategy_context_venue": verifier.CONTEXT_VENUE,
            "strategy_context_capture_ts": "2026-07-11T19:00:00+00:00",
            "strategy_context_snapshot_id": "snapshot-1",
        },
    )
    _write_json(
        state_root / "runtime" / "health" / "paper_strategy_evidence.json",
        {"status": "completed", "reason": "completed"},
    )

    report = verifier.build_funding_stage0_verification(repo_root=tmp_path, baseline=baseline)

    assert report["status"] == "passed"
    assert report["blocking_checks"] == []


def test_funding_stage0_verification_rejects_missing_context(tmp_path: Path) -> None:
    baseline = {
        "generated_at": "2026-07-11T20:00:00+00:00",
        "expected_commit": "abc123",
        "canonical_journal": {"count": 0},
    }
    state_root = tmp_path / verifier.STATE_DIR_REL
    evidence_dir = state_root / "data" / "evidence" / verifier.SESSION_STRATEGY_ID
    _write_jsonl(
        evidence_dir / "session_2026-07-11.jsonl",
        [
            {
                "record_type": "session",
                "phase": "end",
                "campaign_status": "completed",
                "timestamp": "2026-07-11T20:20:00+00:00",
                "_commit": "abc123",
                "reconciliation_result": "pass",
                "critical_error": False,
                "market_data_source": "public_ohlcv",
                "ohlcv_sample_mode": False,
                "ohlcv_timeframe": "5m",
                "ohlcv_venue": verifier.VENUE,
                "ohlcv_symbol": verifier.SYMBOL,
                "strategy_id": verifier.SESSION_STRATEGY_ID,
                "_strategy_id": verifier.SESSION_STRATEGY_ID,
            }
        ],
    )
    _write_json(
        state_root / "runtime" / "flags" / "strategy_runner.status.json",
        {
            "strategy_preset": verifier.SESSION_STRATEGY_ID,
            "signal_source": verifier.SIGNAL_SOURCE,
            "signal_ok": False,
            "signal_reason": "missing_funding_context",
            "strategy_context_ok": False,
        },
    )
    _write_json(
        state_root / "runtime" / "health" / "paper_strategy_evidence.json",
        {"status": "completed", "reason": "completed"},
    )

    report = verifier.build_funding_stage0_verification(repo_root=tmp_path, baseline=baseline)

    assert report["status"] == "failed"
    assert any(check["name"] == "strategy_status_funding_context" for check in report["blocking_checks"])


def test_write_funding_stage0_baseline_only_writes_report_artifacts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(verifier, "data_dir", lambda: tmp_path)
    report = verifier.build_funding_stage0_baseline(repo_root=tmp_path, expected_commit="abc123")

    paths = verifier.write_funding_stage0_baseline(report)

    assert Path(paths["latest_json"]).exists()
    assert Path(paths["latest_markdown"]).exists()
    assert Path(paths["latest_json"]).parent == tmp_path / "funding_stage0_verification"
