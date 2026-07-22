from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "EVIDENCE_MODEL.md"


def _text() -> str:
    return DOC.read_text(encoding="utf-8", errors="replace")


def _flat_text() -> str:
    return " ".join(_text().split())


def test_evidence_model_defines_three_distinct_surfaces() -> None:
    text = _text()

    assert "Executable guard: `tests/test_evidence_model_guard.py`" in text
    assert "## Canonical: JSONL per-record evidence" in text
    assert "## Canonical: persisted paper fill history" in text
    assert "## Legacy: Leaderboard artifact" in text


def test_jsonl_evidence_is_canonical_for_schema_provenance_and_log_health() -> None:
    text = _text()

    assert ".cbp_state/data/evidence/<strategy_id>/" in text
    assert "services/strategies/evidence_logger.py" in text
    assert "scripts/check_promotion_gates.py" in text
    assert "services/strategies/campaign_summary.py" in text
    assert "configs/strategies/es_daily_trend_v1.yaml" in text
    assert "valid schema" in text
    assert "market-data provenance" in text
    assert "latest dated evidence window" in text


def test_latest_window_provenance_does_not_qualify_legacy_fills() -> None:
    text = _flat_text()

    assert (
        "Fresh latest-window provenance does not retroactively qualify older "
        "unstamped fills."
    ) in text
    assert "configured source, timeframe, venue, symbol" in text
    assert "explicit non-sample mode" in text


def test_unlabeled_ohlcv_calls_are_not_promotion_evidence() -> None:
    text = _text()

    assert "Signal calls with unlabeled OHLCV are not promotion evidence." in text
    assert "does not write a" in text
    assert "JSONL signal record" in text
    assert "public_ohlcv" in text
    assert "sample_ohlcv" in text
    assert "unknown provenance" in text


def test_persisted_paper_history_is_canonical_for_qualified_trade_metrics() -> None:
    text = _text()

    assert ".cbp_state/data/trade_journal.sqlite" in text
    assert "services/analytics/strategy_feedback.py" in text
    assert "paper-stage round-trip count" in text
    assert "realized expectancy" in text
    assert "JSONL first identifies the order IDs" in text
    assert "immutable prices, quantities, and fees" in text
    assert "only those qualified order IDs" in text


def test_unqualified_paper_history_remains_diagnostic_only() -> None:
    text = _text()

    assert "`check_promotion_gates.py --json` exposes qualified metrics" in text
    assert "`paper_history`" in text
    assert "`paper_history.all_history`" in text
    assert "diagnostics but cannot advance a promotion gate" in text
    assert "does not retroactively qualify historical records" in text


def test_legacy_leaderboard_is_not_direct_promotion_authority() -> None:
    text = _text()

    assert ".cbp_state/data/strategy_evidence/strategy_evidence.latest.json" in text
    assert "services/backtest/evidence_cycle.py" in text
    assert "paper_strategy_evidence_service.py" in text
    assert "not the direct promotion gate source" in text
    assert "historical leaderboard" in text
    assert 'result["evidence"]' in text
    assert 'result["jsonl_evidence"]' in text


def test_operator_rule_points_to_gate_script_and_surface_roles() -> None:
    text = _text()

    assert "Use `scripts/check_promotion_gates.py --json`" in text
    assert "`paper_history` answers" in text
    assert "`schema` and `provenance` answer" in text
    assert "`strategy_evidence.latest.json` is comparison context" in text
