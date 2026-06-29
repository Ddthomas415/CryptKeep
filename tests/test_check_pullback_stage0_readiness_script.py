from __future__ import annotations

import json

from scripts import check_pullback_stage0_readiness as script


def test_check_pullback_stage0_readiness_json_no_write(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_pullback_stage0_readiness",
        lambda **_kwargs: {
            "report_type": "pullback_stage0_readiness",
            "status": "ready_for_operator_stage0",
            "ready": True,
            "read_only": True,
            "blocking_checks": [],
        },
    )
    monkeypatch.setattr(
        script,
        "write_pullback_stage0_readiness",
        lambda _report: (_ for _ in ()).throw(AssertionError("must not write")),
    )

    assert script.main(["--json", "--no-write"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_type"] == "pullback_stage0_readiness"
    assert payload["read_only"] is True


def test_check_pullback_stage0_readiness_writes_by_default(monkeypatch, capsys) -> None:
    seen: dict[str, object] = {}

    def _build(**_kwargs):
        return {
            "report_type": "pullback_stage0_readiness",
            "status": "ready_for_operator_stage0",
            "ready": True,
            "read_only": True,
            "strategy": "pullback_recovery",
            "session_strategy_id": "pullback_recovery_default",
            "state_dir": ".cbp_state_challengers/pullback_recovery_default",
            "blocking_checks": [],
            "proof_command": {"shell": "CBP_STATE_DIR=... run"},
        }

    def _write(report):
        seen["report"] = report
        return {"latest_json": "/tmp/latest.json", "latest_markdown": "/tmp/latest.md"}

    monkeypatch.setattr(script, "build_pullback_stage0_readiness", _build)
    monkeypatch.setattr(script, "write_pullback_stage0_readiness", _write)

    assert script.main([]) == 0
    out = capsys.readouterr().out
    assert seen["report"]["report_type"] == "pullback_stage0_readiness"
    assert "artifact_latest_json=/tmp/latest.json" in out
