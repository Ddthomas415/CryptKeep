from __future__ import annotations

import json

from scripts import verify_pullback_stage0_proof as script


def test_verify_pullback_stage0_record_baseline_json_no_write(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_pullback_stage0_baseline",
        lambda **_kwargs: {
            "report_type": "pullback_stage0_baseline",
            "read_only": True,
            "expected_commit": "abc123",
        },
    )
    monkeypatch.setattr(
        script,
        "write_pullback_stage0_baseline",
        lambda _report: (_ for _ in ()).throw(AssertionError("must not write")),
    )

    assert script.main(["--record-baseline", "--json", "--no-write"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["report_type"] == "pullback_stage0_baseline"
    assert payload["read_only"] is True


def test_verify_pullback_stage0_default_returns_nonzero_until_passed(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        script,
        "build_pullback_stage0_verification",
        lambda **_kwargs: {
            "report_type": "pullback_stage0_verification",
            "status": "incomplete",
            "passed": False,
            "read_only": True,
            "blocking_checks": [{"name": "baseline_loaded"}],
        },
    )
    monkeypatch.setattr(script, "write_pullback_stage0_verification", lambda report: {})

    assert script.main(["--json", "--no-write"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "incomplete"
    assert payload["passed"] is False
