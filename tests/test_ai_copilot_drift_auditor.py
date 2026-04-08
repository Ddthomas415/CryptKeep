from __future__ import annotations

import json
from pathlib import Path

from services.ai_copilot.drift_auditor import build_drift_report, write_drift_report


def test_build_drift_report_detects_expected_repo_mismatch():
    report = build_drift_report()

    assert report["severity"] == "ok"
    issue_blob = "\n".join(report["issues"])
    exchange_check = next(item for item in report["checks"] if item["name"] == "exchange_support_drift")
    assert exchange_check["ok"] is True
    assert "gateio" in exchange_check["preflight_supported"]
    assert "gateio" in exchange_check["dashboard_venues"]
    assert "exchange_support_drift" not in issue_blob
    fallback_check = next(item for item in report["checks"] if item["name"] == "dashboard_fallback_truth")
    assert fallback_check["ok"] is True
    assert fallback_check["summary_fallback_labeled"] is True
    assert "dashboard_fallback_truth" not in issue_blob
    universe_check = next(item for item in report["checks"] if item["name"] == "default_universe_drift")
    assert universe_check["ok"] is True
    assert universe_check["dashboard_watchlist_assets"] == ["BTC", "ETH"]
    assert "default_universe_drift" not in issue_blob


def test_write_drift_report_writes_files(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    report = build_drift_report()
    paths = write_drift_report(report, stem="drift_audit_test")

    json_path = Path(paths["json_path"])
    markdown_path = Path(paths["markdown_path"])

    assert json_path.exists()
    assert markdown_path.exists()

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert payload["severity"] == "ok"
    markdown = markdown_path.read_text(encoding="utf-8")
    assert "# CryptKeep Drift Audit" in markdown
    assert "No concrete repo drift was detected" in markdown
