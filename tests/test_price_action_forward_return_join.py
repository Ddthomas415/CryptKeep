from __future__ import annotations

import json

from services.analytics.price_action_context_labels import build_price_action_context_labels
from services.analytics.price_action_forward_return_join import build_price_action_forward_return_join


BASE_TS = 1_700_000_000_000


def _row(idx: int, o: float, h: float, l: float, c: float, v: float = 10.0) -> list[float]:
    return [BASE_TS + idx * 60_000, o, h, l, c, v]


def _label_artifact() -> dict:
    rows = [
        _row(0, 100.0, 101.0, 99.0, 100.0),
        _row(1, 101.0, 102.0, 98.0, 99.0),
        _row(2, 98.5, 102.0, 98.0, 101.5),  # bullish engulfing
        _row(3, 102.0, 104.0, 101.5, 103.5),
        _row(4, 103.5, 105.0, 103.0, 104.5),
    ]
    return build_price_action_context_labels(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        rows=rows,
        swing_lookback=3,
        range_lookback=3,
    )


def test_forward_return_join_summarizes_labels_against_baseline() -> None:
    labels = _label_artifact()
    report = build_price_action_forward_return_join(
        label_artifact=labels,
        horizon_bars=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        min_label_count=1,
    )

    assert report["ok"] is True
    assert report["research_only"] is True
    assert report["not_strategy_config"] is True
    assert report["not_campaign_evidence"] is True
    assert report["not_promotion_evidence"] is True
    assert report["not_profitability_evidence"] is True
    assert report["label_artifact_hash"] == labels["artifact_hash"]
    assert report["dataset_hash"] == labels["dataset_hash"]
    assert report["joined_rows"] == 4
    assert len(report["artifact_hash"]) == 64
    assert report["baseline"]["count"] == 4
    assert "engulfing_candle:bullish" in report["label_summaries"]
    engulfing = report["label_summaries"]["engulfing_candle:bullish"]
    assert engulfing["count"] == 1
    assert engulfing["meets_min_count"] is True
    assert engulfing["avg_forward_return_long_pct"] > 0.0
    assert engulfing["avg_forward_return_short_pct"] < 0.0
    assert "requires_out_of_sample_review_before_strategy_use" in report["limitations"]


def test_forward_return_join_applies_costs_to_long_and_short_returns() -> None:
    labels = _label_artifact()
    no_cost = build_price_action_forward_return_join(label_artifact=labels, horizon_bars=1, fee_bps=0.0, slippage_bps=0.0)
    with_cost = build_price_action_forward_return_join(label_artifact=labels, horizon_bars=1, fee_bps=10.0, slippage_bps=5.0)

    assert with_cost["baseline"]["avg_forward_return_long_pct"] < no_cost["baseline"]["avg_forward_return_long_pct"]
    assert with_cost["baseline"]["avg_forward_return_short_pct"] < no_cost["baseline"]["avg_forward_return_short_pct"]


def test_forward_return_join_rejects_wrong_or_failed_label_artifact() -> None:
    wrong = build_price_action_forward_return_join(label_artifact={"artifact_type": "other", "ok": True})
    failed = build_price_action_forward_return_join(
        label_artifact={
            "artifact_type": "price_action_context_labels_v1",
            "ok": False,
            "reason": "archive_missing",
            "artifact_hash": "abc",
            "dataset_hash": "def",
        }
    )

    assert wrong["ok"] is False
    assert wrong["reason"] == "unsupported_label_artifact"
    assert failed["ok"] is False
    assert failed["reason"] == "archive_missing"


def test_forward_return_join_cli_writes_artifact(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_forward_return_join as cli

    labels_path = tmp_path / "labels.json"
    out_path = tmp_path / "join.json"
    labels_path.write_text(json.dumps(_label_artifact()), encoding="utf-8")

    rc = cli.main(
        [
            "--labels",
            str(labels_path),
            "--horizon-bars",
            "1",
            "--min-label-count",
            "1",
            "--output",
            str(out_path),
            "--fail-if-not-ok",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    written = json.loads(out_path.read_text(encoding="utf-8"))
    assert rc == 0
    assert printed == written
    assert printed["artifact_type"] == "price_action_forward_return_join_v1"


def test_forward_return_join_cli_returns_2_when_requested_and_not_ok(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_forward_return_join as cli

    labels_path = tmp_path / "labels.json"
    labels_path.write_text(json.dumps({"artifact_type": "other", "ok": True}), encoding="utf-8")

    rc = cli.main(["--labels", str(labels_path), "--fail-if-not-ok"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["reason"] == "unsupported_label_artifact"
