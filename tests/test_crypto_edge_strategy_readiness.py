from __future__ import annotations

import json

from services.analytics.crypto_edge_strategy_readiness import build_crypto_edge_strategy_readiness


def _rows_by_strategy(report: dict) -> dict[str, dict]:
    return {str(row["strategy"]): dict(row) for row in report["strategies"]}


def test_crypto_edge_strategy_readiness_classifies_current_context_strategies() -> None:
    report = build_crypto_edge_strategy_readiness()
    rows = _rows_by_strategy(report)

    assert report["ok"] is True
    assert report["read_only"] is True
    assert report["not_campaign_evidence"] is True
    assert report["not_promotion_evidence"] is True
    assert set(rows) == {"funding_extreme", "open_interest_shift", "order_book_imbalance"}

    funding = rows["funding_extreme"]
    assert funding["module_exists"] is True
    assert funding["registry_executable"] is True
    assert funding["config_supported"] is True
    assert funding["config_only"] is False
    assert funding["preset_exists"] is True
    assert funding["preset_validation_ok"] is True
    assert funding["status"] == "stage0_wired_research_only"
    assert "promotion qualification remains high-risk" in " ".join(funding["known_blockers"])

    oi = rows["open_interest_shift"]
    assert oi["module_exists"] is True
    assert oi["registry_executable"] is False
    assert oi["config_supported"] is True
    assert oi["config_only"] is True
    assert oi["preset_exists"] is True
    assert oi["preset_trade_enabled"] is False
    assert oi["preset_validation_ok"] is True
    assert oi["status"] == "config_only_research_placeholder"

    depth = rows["order_book_imbalance"]
    assert depth["module_exists"] is True
    assert depth["registry_executable"] is False
    assert depth["config_supported"] is False
    assert depth["preset_exists"] is False
    assert depth["status"] == "signal_module_unregistered"
    assert "streaming depth" in " ".join(depth["known_blockers"])


def test_crypto_edge_strategy_readiness_status_counts_are_derived() -> None:
    report = build_crypto_edge_strategy_readiness()

    assert report["row_count"] == 3
    assert report["status_counts"] == {
        "config_only_research_placeholder": 1,
        "signal_module_unregistered": 1,
        "stage0_wired_research_only": 1,
    }


def test_crypto_edge_strategy_readiness_cli_prints_and_optionally_writes_json(tmp_path, capsys) -> None:
    from scripts.research import run_crypto_edge_strategy_readiness as cli

    output = tmp_path / "readiness.json"
    rc = cli.main(["--output", str(output)])

    assert rc == 0
    printed = json.loads(capsys.readouterr().out)
    written = json.loads(output.read_text(encoding="utf-8"))
    assert printed == written
    assert printed["artifact_type"] == "crypto_edge_strategy_readiness_v1"
    assert printed["limitations"]
