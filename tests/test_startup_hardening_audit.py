from __future__ import annotations

import json

from services.runtime import startup_hardening_audit as svc


def test_startup_hardening_audit_identifies_current_topology() -> None:
    report = svc.build_startup_hardening_audit()

    assert report["report_type"] == "startup_hardening_audit"
    assert report["read_only"] is True
    assert report["gap_status"] in {"insufficient_evidence", "gap_not_reproduced"}
    assert report["gap_reproduced"] is False
    assert report["safety"]["services_started"] is False
    assert report["safety"]["services_stopped"] is False
    assert report["safety"]["orders_routed"] is False

    facts = report["machine_facts"]
    assert "pipeline" in facts["service_constants"]["all_services"]
    commands = {row["service"]: row for row in facts["start_commands"]}
    assert commands["pipeline"]["script_path"] == "scripts/compat/run_pipeline_loop.py"
    assert commands["intent_consumer"]["safe_wrapper"] is True
    assert commands["reconciler"]["script_path"] == "scripts/run_live_reconciler_safe.py"
    assert {row["service"] for row in facts["unwrapped_start_commands"]} == {
        "pipeline",
        "ops_signal_adapter",
        "ops_risk_gate",
    }
    assert facts["pipeline"]["first_config_required_raise_line"] < facts["pipeline"]["first_status_write_call_line"]
    assert facts["pipeline"]["config_required_raise_before_first_status_write"] is True


def test_startup_hardening_audit_writes_only_audit_artifacts(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    report = svc.build_startup_hardening_audit()
    paths = svc.write_startup_hardening_audit(report)

    latest_json = tmp_path / "runtime" / "startup_audits" / "startup_hardening_audit.latest.json"
    latest_md = tmp_path / "runtime" / "startup_audits" / "startup_hardening_audit.latest.md"
    assert paths["latest_json"] == str(latest_json)
    assert paths["latest_markdown"] == str(latest_md)
    assert json.loads(latest_json.read_text(encoding="utf-8"))["report_type"] == "startup_hardening_audit"
    assert "Startup Hardening Audit" in latest_md.read_text(encoding="utf-8")

    assert not (tmp_path / "runtime" / "pipeline.pid").exists()
    assert not (tmp_path / "runtime" / "flags" / "pipeline.status.json").exists()


def test_startup_hardening_audit_has_required_boundaries() -> None:
    report = svc.build_startup_hardening_audit()

    assert "do_not_start_services_from_this_report" in report["do_not_touch"]
    assert "do_not_stop_services_from_this_report" in report["do_not_touch"]
    assert "do_not_change_startup_scripts" in report["do_not_touch"]
    assert "do_not_enable_live_execution" in report["do_not_touch"]
    assert report["safety"]["startup_scripts_modified"] is False
    assert report["safety"]["live_execution_enabled"] is False
