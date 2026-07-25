from __future__ import annotations

import json

from services.analytics.price_action_context_labels import build_price_action_context_labels
from services.analytics.price_action_forward_return_join import build_price_action_forward_return_join
from services.analytics.price_action_stability_report import build_price_action_stability_report


BASE_TS = 1_700_000_000_000


def _row(idx: int, close: float) -> list[float]:
    return [BASE_TS + idx * 60_000, close - 0.2, close + 0.5, close - 0.5, close, 10.0]


def _forward_artifact() -> dict:
    rows: list[list[float]] = []
    # Build three repeated windows with one bullish engulfing-like label before
    # a positive forward move in each window.
    closes = [
        100.0, 99.0, 101.0, 102.0,
        102.0, 101.0, 103.0, 104.0,
        104.0, 103.0, 105.0, 106.0,
    ]
    for idx, close in enumerate(closes):
        rows.append(_row(idx, close))
    # Make the engulfing bars wide enough for the label detector.
    rows[2] = [BASE_TS + 2 * 60_000, 98.5, 102.0, 98.0, 101.0, 10.0]
    rows[6] = [BASE_TS + 6 * 60_000, 100.5, 104.0, 100.0, 103.0, 10.0]
    rows[10] = [BASE_TS + 10 * 60_000, 102.5, 106.0, 102.0, 105.0, 10.0]
    labels = build_price_action_context_labels(
        venue="coinbase",
        symbol="BTC/USD",
        timeframe="1m",
        rows=rows,
        swing_lookback=2,
        range_lookback=2,
    )
    return build_price_action_forward_return_join(
        label_artifact=labels,
        horizon_bars=1,
        fee_bps=0.0,
        slippage_bps=0.0,
        min_label_count=1,
    )


def test_stability_report_splits_windows_and_summarizes_label_consistency() -> None:
    forward = _forward_artifact()
    report = build_price_action_stability_report(
        forward_return_artifact=forward,
        window_size_rows=4,
        min_windows=3,
        min_label_count=1,
        consistency_threshold=0.6,
    )

    assert report["ok"] is True
    assert report["research_only"] is True
    assert report["not_strategy_config"] is True
    assert report["not_campaign_evidence"] is True
    assert report["not_promotion_evidence"] is True
    assert report["not_profitability_evidence"] is True
    assert report["forward_return_artifact_hash"] == forward["artifact_hash"]
    assert len(report["artifact_hash"]) == 64
    assert report["window_count"] == 3
    assert "swing_failure:bullish" in report["label_stability"]
    swing_failure = report["label_stability"]["swing_failure:bullish"]
    assert swing_failure["windows_meeting_min_count"] == 3
    assert swing_failure["meets_min_windows"] is True
    assert swing_failure["dominant_observed_side"] == "long"
    assert swing_failure["stable_observation"] is True
    assert "not_strategy_selection" in report["limitations"]


def test_stability_report_rejects_wrong_or_failed_forward_artifact() -> None:
    wrong = build_price_action_stability_report(forward_return_artifact={"artifact_type": "other", "ok": True})
    failed = build_price_action_stability_report(
        forward_return_artifact={
            "artifact_type": "price_action_forward_return_join_v1",
            "ok": False,
            "reason": "unsupported_label_artifact",
            "artifact_hash": "abc",
            "dataset_hash": "def",
        }
    )

    assert wrong["ok"] is False
    assert wrong["reason"] == "unsupported_forward_return_artifact"
    assert failed["ok"] is False
    assert failed["reason"] == "unsupported_label_artifact"


def test_stability_report_cli_writes_artifact(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_stability_report as cli

    forward_path = tmp_path / "forward.json"
    output = tmp_path / "stability.json"
    forward_path.write_text(json.dumps(_forward_artifact()), encoding="utf-8")

    rc = cli.main(
        [
            "--forward-returns",
            str(forward_path),
            "--window-size-rows",
            "4",
            "--min-windows",
            "3",
            "--min-label-count",
            "1",
            "--output",
            str(output),
            "--fail-if-not-ok",
        ]
    )

    printed = json.loads(capsys.readouterr().out)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert rc == 0
    assert printed == written
    assert printed["artifact_type"] == "price_action_stability_report_v1"


def test_stability_report_cli_returns_2_when_requested_and_not_ok(tmp_path, capsys) -> None:
    from scripts.research import run_price_action_stability_report as cli

    forward_path = tmp_path / "forward.json"
    forward_path.write_text(json.dumps({"artifact_type": "other", "ok": True}), encoding="utf-8")

    rc = cli.main(["--forward-returns", str(forward_path), "--fail-if-not-ok"])

    payload = json.loads(capsys.readouterr().out)
    assert rc == 2
    assert payload["ok"] is False
    assert payload["reason"] == "unsupported_forward_return_artifact"
