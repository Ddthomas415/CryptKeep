from __future__ import annotations

import json

from scripts import plan_multi_symbol_paper_campaigns as script


def test_plan_multi_symbol_paper_campaigns_json_no_write(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_multi_symbol_paper_campaign_plan",
        lambda **_kwargs: {
            "report_type": "multi_symbol_paper_campaign_plan",
            "status": "ok",
            "read_only": True,
            "summary": {"proposal_count": 1},
        },
    )
    monkeypatch.setattr(
        script,
        "write_multi_symbol_paper_campaign_plan",
        lambda _report: (_ for _ in ()).throw(AssertionError("must not write")),
    )

    assert script.main(["--symbols", "ETH/USDT", "SOL/USDT", "--json", "--no-write"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_type"] == "multi_symbol_paper_campaign_plan"
    assert payload["read_only"] is True


def test_plan_multi_symbol_paper_campaigns_writes_by_default(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _build(**_kwargs):
        return {
            "report_type": "multi_symbol_paper_campaign_plan",
            "status": "ok",
            "read_only": True,
            "summary": {
                "symbols_requested": 2,
                "symbols_fetched": 2,
                "ranked_candidate_count": 1,
                "proposal_count": 1,
                "rejected_count": 0,
            },
            "preflight_summary": {"passed": 1, "failed": 0},
        }

    def _write(report):
        seen["report"] = report
        return {"latest_json": "/tmp/latest.json", "latest_markdown": "/tmp/latest.md"}

    monkeypatch.setattr(script, "build_multi_symbol_paper_campaign_plan", _build)
    monkeypatch.setattr(script, "write_multi_symbol_paper_campaign_plan", _write)

    assert script.main(["--host", "laptop", "--symbols", "ETH/USDT", "SOL/USDT"]) == 0
    out = capsys.readouterr().out
    assert seen["report"]["report_type"] == "multi_symbol_paper_campaign_plan"
    assert "artifact_latest_json=/tmp/latest.json" in out
