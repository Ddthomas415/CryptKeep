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


def test_external_provider_allowlist_defaults_to_supported_providers():
    out = policy.parse_external_provider_allowlist(None)

    assert out == {
        "ok": True,
        "providers": ["anthropic", "openai", "google"],
        "source": "default_supported",
    }
    assert policy.external_provider_policy("OpenAI")["ok"] is True


def test_external_provider_allowlist_can_disable_or_narrow():
    disabled = policy.parse_external_provider_allowlist("none")
    assert disabled == {"ok": True, "providers": [], "source": "env_disabled"}
    assert policy.external_provider_policy("openai", allowlist_raw="none") == {
        "ok": False,
        "provider": "openai",
        "reason": "provider_not_allowed:openai",
        "allowed_providers": [],
        "policy_source": "env_disabled",
    }

    narrowed = policy.external_provider_policy("openai", allowlist_raw="anthropic, google")
    assert narrowed == {
        "ok": False,
        "provider": "openai",
        "reason": "provider_not_allowed:openai",
        "allowed_providers": ["anthropic", "google"],
        "policy_source": "env",
    }


def test_external_provider_allowlist_fails_closed_on_garbage():
    assert policy.parse_external_provider_allowlist("anthropic,,openai") == {
        "ok": False,
        "providers": [],
        "source": "env",
        "reason": "blank_provider",
    }
    assert policy.external_provider_policy("anthropic", allowlist_raw="anthropic,unknown") == {
        "ok": False,
        "provider": "anthropic",
        "reason": "invalid_provider_allowlist:unsupported_provider_in_allowlist:unknown",
        "allowed_providers": [],
        "policy_source": "env",
    }
