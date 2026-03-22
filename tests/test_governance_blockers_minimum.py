import importlib
from typing import Any

import pytest


def _import(module_name: str):
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        pytest.fail(f"Could not import {module_name}: {exc}")


def _first_attr(module_names: list[str], attr_names: list[str]) -> Any:
    for module_name in module_names:
        try:
            mod = importlib.import_module(module_name)
        except Exception:
            continue
        for attr_name in attr_names:
            if hasattr(mod, attr_name):
                return getattr(mod, attr_name)
    pytest.fail(
        "Missing expected interface. "
        f"modules tried={module_names}, attrs tried={attr_names}"
    )


# -----------------------------
# 1. Terminal Invalidation (Campaign-Level)
# -----------------------------
def test_campaign_terminal_invalidation_on_drift(tmp_path, monkeypatch):
    svc = _import("services.analytics.paper_strategy_evidence_service")

    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setattr(
        svc,
        "_component_runtime",
        lambda name: {"name": name, "pid_alive": False, "pid": 0, "status": "not_started"},
    )
    monkeypatch.setattr(
        svc,
        "_ensure_component",
        lambda name, *, cfg: {"name": name, "started": True, "pid": 123, "status": "running"},
    )
    monkeypatch.setattr(
        svc,
        "_run_strategy_window",
        lambda *, cfg, strategy_name: {
            "strategy": str(strategy_name),
            "runtime_sec": 1.0,
            "stop_reason": "fingerprint_mismatch",
            "runner_status": "stopped",
            "enqueued_total": 0,
            "fills_delta": 0,
            "closed_trades_delta": 0,
            "net_realized_pnl_delta": 0.0,
            "fills_total": 0,
            "closed_trades_total": 0,
            "net_realized_pnl_total": 0.0,
            "latest_fill_ts": "",
        },
    )
    monkeypatch.setattr(
        svc,
        "run_strategy_evidence_cycle",
        lambda **kwargs: {"as_of": "2026-03-19T00:00:00Z", "aggregate_leaderboard": {"rows": []}, "decisions": []},
    )
    monkeypatch.setattr(
        svc,
        "persist_strategy_evidence",
        lambda report: {"ok": True, "latest_path": str(tmp_path / "strategy_evidence.latest.json")},
    )
    monkeypatch.setattr(
        svc,
        "write_decision_record",
        lambda report, *, artifact_path="": {"ok": True, "path": str(tmp_path / "decision_record.md"), "artifact_path": artifact_path},
    )
    monkeypatch.setattr(svc, "_wait_for_component_stop", lambda name, *, timeout_sec=10.0: True)
    monkeypatch.setattr(svc, "_stop_component", lambda name: {"ok": True, "component": name})

    out = svc.run_campaign(
        svc.PaperStrategyEvidenceServiceCfg(
            strategies=("ema_cross",),
            per_strategy_runtime_sec=1.0,
        )
    )

    status = out.get("status")
    terminal = out.get("is_terminal", False)

    assert status == "INVALID"
    assert terminal is True


# -----------------------------
# 2. Single Mutation Path (Negative Test)
# -----------------------------
def test_campaign_state_cannot_mutate_outside_governance(tmp_path, monkeypatch):
    svc = _import("services.analytics.paper_strategy_evidence_service")

    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))

    with pytest.raises(Exception):
        svc._write_status({"status": "PROMOTED"})


# -----------------------------
# 3. Claims Split Enforcement
# -----------------------------
def test_claims_guard_blocks_unapproved_claims():
    auth_caps_mod = _import("services.security.auth_capabilities")
    digest_builders_mod = _import("dashboard.services.digest.builders")
    view_data_mod = _import("dashboard.services.view_data")

    auth_capabilities = getattr(auth_caps_mod, "auth_capabilities", None)
    claim_boundaries = getattr(digest_builders_mod, "CLAIM_BOUNDARIES", None)
    update_settings_view = getattr(view_data_mod, "update_settings_view", None)

    assert callable(auth_capabilities)
    assert isinstance(claim_boundaries, list)
    assert callable(update_settings_view)

    # Isolate this test from prior auth-scope mutations.
    update_settings_view(
        {
            "security": {
                "auth_scope": "local_private_only",
                "remote_access_requires_mfa": True,
                "outer_access_control": "",
            }
        }
    )

    caps = auth_capabilities()

    assert caps["auth_scope"] == "local_private_only"
    assert caps["remote_access_hardened"] is False
    assert "not hardened" in caps["scope_detail"].lower()

    joined = " | ".join(str(x) for x in claim_boundaries).lower()
    assert "not live profitability proof" in joined
    assert "stock support is not proven" in joined
    assert "shorting is not fully validated" in joined


# -----------------------------
# 4. Persisted Auth-Scope Read-Back
# -----------------------------
def test_auth_scope_persistence_and_enforcement():
    view_data = _import("dashboard.services.view_data")
    runtime_guard = _import("services.security.auth_runtime_guard")

    update_settings_view = getattr(view_data, "update_settings_view", None)
    get_settings_view = getattr(view_data, "get_settings_view", None)
    auth_runtime_guard_status = getattr(runtime_guard, "auth_runtime_guard_status", None)

    assert callable(update_settings_view)
    assert callable(get_settings_view)
    assert callable(auth_runtime_guard_status)

    update_settings_view(
        {
            "security": {
                "auth_scope": "remote_public_candidate",
                "remote_access_requires_mfa": True,
                "outer_access_control": "cloudflare_access",
            }
        }
    )

    settings = get_settings_view()
    security = settings.get("security", {})

    assert security.get("auth_scope") == "remote_public_candidate"
    assert security.get("remote_access_requires_mfa") is True
    assert security.get("outer_access_control") == "cloudflare_access"

    status = auth_runtime_guard_status()
    assert status.get("auth_scope") == "remote_public_candidate"


# -----------------------------
# 5. Override Boundary Assertion
# -----------------------------
def test_override_escalation_rejected():
    bundles = _import("services.profiles.bundles")

    apply_bundle = getattr(bundles, "apply_bundle", None)
    assert callable(apply_bundle)

    base_cfg = {
        "risk": {"max_order_quote": 10.0},
        "strategy": {"trade_enabled": True},
    }

    dangerous_overrides = {
        "risk": {"max_order_quote": 10_000_000.0},
        "strategy": {"trade_enabled": True},
    }

    try:
        result = apply_bundle(base_cfg, "default", overrides=dangerous_overrides)
    except Exception:
        return

    assert result["risk"]["max_order_quote"] != 10_000_000.0
