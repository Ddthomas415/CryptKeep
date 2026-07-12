from __future__ import annotations

import json
from pathlib import Path

from services.analytics.execution_cost_stack_report import build_execution_cost_stack_report


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def _shadow_record(**overrides):
    row = {
        "record_type": "fill",
        "timestamp": "2026-07-12T00:00:00+00:00",
        "record_subtype": "shadow_would_be_fill",
        "shadow_would_be_fill": True,
        "intent_id": "intent-1",
        "_stage": "shadow",
        "venue": "coinbase",
        "exchange": "coinbase",
        "symbol": "BTC/USD",
        "selected_strategy": "sma_200_trend",
        "side": "buy",
        "qty": 1.0,
        "reference_mid": 100.0,
        "bid": 99.9,
        "ask": 100.1,
        "spread_bps": 20.0,
        "modeled_fill_price": 100.05,
        "notional": 100.05,
        "fees_paid": 0.10005,
        "fee_bps": 10.0,
    }
    row.update(overrides)
    return row


def test_execution_cost_report_excludes_paper_fills(tmp_path):
    evidence_root = tmp_path / "evidence"
    _write_jsonl(
        evidence_root / "es_daily_trend_v1" / "fill_2026-07-12.jsonl",
        [
            {
                "record_type": "fill",
                "strategy_id": "es_daily_trend_v1",
                "timestamp": "2026-07-12T00:00:00+00:00",
                "side": "buy",
                "fill_price": 100.0,
                "pnl_usd": 12.0,
            }
        ],
    )

    report = build_execution_cost_stack_report(evidence_root=evidence_root, min_records=1)

    assert report["read_only"] is True
    assert report["policy"]["paper_fills_excluded"] is True
    assert report["status"] == "no_records"
    assert report["recommendation"] == "research_more"
    assert report["records_loaded"] == 0
    assert report["ignored_non_shadow_records"] == 1


def test_execution_cost_report_requires_fill_probability_path_for_recommendation(tmp_path):
    evidence_root = tmp_path / "evidence"
    _write_jsonl(
        evidence_root / "shadow_strategy" / "fill_2026-07-12.jsonl",
        [_shadow_record()],
    )

    report = build_execution_cost_stack_report(evidence_root=evidence_root, min_records=1)

    assert report["status"] == "insufficient_data"
    assert report["recommendation"] == "research_more"
    assert report["usable_records"] == 1
    assert report["summary"]["avg_taker_cost_bps"] == 15.0
    assert report["summary"]["avg_taker_fee_bps"] == 10.0
    assert report["summary"]["avg_spread_bps"] == 20.0
    assert report["summary"]["avg_maker_quote_cost_bps"] == 0.0
    assert report["summary"]["maker_fill_probability_estimate"] is None
    assert "subsequent_price_path" in " ".join(report["limitations"])
    assert report["source_artifact_hash"]
    assert report["source_report_hash"]


def test_execution_cost_report_can_score_path_backed_shadow_records(tmp_path):
    evidence_root = tmp_path / "evidence"
    _write_jsonl(
        evidence_root / "shadow_strategy" / "fill_2026-07-12.jsonl",
        [
            _shadow_record(intent_id="buy-1", subsequent_price_path=[{"low": 99.8, "high": 100.4}]),
            _shadow_record(
                intent_id="sell-1",
                side="sell",
                bid=99.9,
                ask=100.1,
                modeled_fill_price=99.95,
                subsequent_price_path=[{"low": 99.5, "high": 100.2}],
            ),
        ],
    )

    report = build_execution_cost_stack_report(
        evidence_root=evidence_root,
        min_records=2,
        min_fill_probability_records=2,
        min_fill_probability=0.5,
    )

    assert report["status"] == "ready"
    assert report["recommendation"] == "candidate_execution_policy_change"
    assert report["summary"]["maker_fill_probability_estimate"] == 1.0
    assert report["summary"]["maker_fill_probability_records"] == 2
    assert report["groups"][0]["venue"] == "coinbase"
    assert report["groups"][0]["symbol"] == "BTC/USD"
    assert report["groups"][0]["strategy"] == "sma_200_trend"


def test_execution_cost_report_cli_writes_artifact(tmp_path, capsys):
    from scripts.report_execution_cost_stack import main

    evidence_root = tmp_path / "evidence"
    output = tmp_path / "report.json"
    _write_jsonl(evidence_root / "shadow_strategy" / "fill_2026-07-12.jsonl", [_shadow_record()])

    rc = main(["--evidence-root", str(evidence_root), "--min-records", "1", "--output", str(output)])

    assert rc == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    stdout_payload = json.loads(capsys.readouterr().out)
    assert payload["report_type"] == "execution_cost_stack_report"
    assert stdout_payload["source_report_hash"] == payload["source_report_hash"]
    assert (tmp_path / "execution_cost_stack.latest.json").exists()
