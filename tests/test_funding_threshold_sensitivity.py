from __future__ import annotations

import json

from services.analytics.funding_threshold_sensitivity import run_funding_threshold_sensitivity


def _price_join_artifact(path) -> None:
    payload = {
        "artifact_type": "funding_context_price_join_v1",
        "dataset_hash": "source-hash",
        "fee_bps": 0.0,
        "slippage_bps": 0.0,
        "rows": [
            {
                "funding_rate_pct": -0.02,
                "entry_close": 100.0,
                "exit_close": 110.0,
            },
            {
                "funding_rate_pct": -0.006,
                "entry_close": 100.0,
                "exit_close": 99.0,
            },
            {
                "funding_rate_pct": 0.006,
                "entry_close": 100.0,
                "exit_close": 99.0,
            },
            {
                "funding_rate_pct": 0.06,
                "entry_close": 100.0,
                "exit_close": 90.0,
            },
        ],
    }
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_threshold_sensitivity_counts_explicit_threshold_grid(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src)

    out = run_funding_threshold_sensitivity(
        input_path=src,
        long_thresholds_pct=[0.05, 0.005],
        short_thresholds_pct=[-0.01, -0.005],
    )

    assert out["ok"] is True
    assert out["artifact_type"] == "funding_threshold_sensitivity_v1"
    assert out["research_only"] is True
    assert out["source_dataset_hash"] == "source-hash"
    assert out["funding_rate_pct_range"] == {"min": -0.02, "max": 0.06}
    by_pair = {
        (row["long_threshold_pct"], row["short_threshold_pct"]): row
        for row in out["grid_rows"]
    }
    assert by_pair[(0.05, -0.01)]["actionable_rows"] == 2
    assert by_pair[(0.05, -0.01)]["buy_rows"] == 1
    assert by_pair[(0.05, -0.01)]["sell_rows"] == 1
    assert by_pair[(0.005, -0.005)]["actionable_rows"] == 4
    assert out["summary"]["current_default_actionable_rows"] == 2
    assert "not_profitability_evidence" in out["limitations"]


def test_threshold_sensitivity_hash_is_deterministic(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src)

    first = run_funding_threshold_sensitivity(input_path=src)
    second = run_funding_threshold_sensitivity(input_path=src)

    assert first["dataset_hash"] == second["dataset_hash"]


def test_threshold_sensitivity_applies_cost_overrides(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src)

    free = run_funding_threshold_sensitivity(
        input_path=src,
        long_thresholds_pct=[0.05],
        short_thresholds_pct=[-0.01],
        fee_bps=0.0,
        slippage_bps=0.0,
    )
    costly = run_funding_threshold_sensitivity(
        input_path=src,
        long_thresholds_pct=[0.05],
        short_thresholds_pct=[-0.01],
        fee_bps=10.0,
        slippage_bps=5.0,
    )

    assert costly["grid_rows"][0]["avg_net_forward_return_pct"] < free["grid_rows"][0]["avg_net_forward_return_pct"]


def test_threshold_sensitivity_fails_closed_on_bad_thresholds(tmp_path):
    src = tmp_path / "price_join.json"
    _price_join_artifact(src)

    out = run_funding_threshold_sensitivity(
        input_path=src,
        long_thresholds_pct=[0.0],
        short_thresholds_pct=[-0.01],
    )

    assert out["ok"] is False
    assert out["reason"] == "invalid_threshold:long_threshold_pct"


def test_threshold_sensitivity_rejects_wrong_input_artifact(tmp_path):
    src = tmp_path / "other.json"
    src.write_text(json.dumps({"artifact_type": "something_else", "rows": []}), encoding="utf-8")

    out = run_funding_threshold_sensitivity(input_path=src)

    assert out["ok"] is False
    assert out["reason"] == "unsupported_input_artifact_type"


def test_threshold_sensitivity_cli_writes_json_artifact(tmp_path, capsys):
    from scripts.research import run_funding_threshold_sensitivity as cli

    src = tmp_path / "price_join.json"
    out_path = tmp_path / "sensitivity.json"
    _price_join_artifact(src)

    rc = cli.main(
        [
            "--input",
            str(src),
            "--output",
            str(out_path),
            "--long-thresholds-pct",
            "0.05",
            "--short-thresholds-pct",
            "-0.01",
            "--fail-if-not-ok",
        ]
    )

    assert rc == 0
    written = json.loads(out_path.read_text(encoding="utf-8"))
    printed = json.loads(capsys.readouterr().out)
    assert written["dataset_hash"] == printed["dataset_hash"]
    assert written["grid_rows"][0]["actionable_rows"] == 2


def test_threshold_sensitivity_cli_returns_2_when_requested_and_not_ok(tmp_path):
    from scripts.research import run_funding_threshold_sensitivity as cli

    rc = cli.main(["--input", str(tmp_path / "missing.json"), "--fail-if-not-ok"])

    assert rc == 2
