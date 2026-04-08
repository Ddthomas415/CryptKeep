from __future__ import annotations

from services.ai_copilot import policy


def test_policy_defaults_and_path_guards(tmp_path, monkeypatch):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    assert policy.DEFAULT_PROVIDER == "anthropic"
    assert policy.DEFAULT_MODEL == policy.COPILOT_MODEL
    assert policy.is_protected_path("services/execution/live_executor.py")
    assert policy.is_protected_path("./services/risk/risk_daily.py")
    assert not policy.is_protected_path("docs/AI_COPILOT_BOUNDARY.md")
    assert policy.requires_human_approval("config/trading.yaml")

    report_root = policy.report_root()
    config_path = policy.config_path()

    assert report_root.is_dir()
    assert config_path.parent.is_dir()
    assert report_root.name == "ai_reports"
    assert report_root.parent.name == "runtime"
    assert config_path.name == "ai_copilot.yaml"
    assert config_path.parent.name == "config"
    assert config_path.parent.parent.name == "runtime"
