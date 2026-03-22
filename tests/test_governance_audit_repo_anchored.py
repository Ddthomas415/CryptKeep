import importlib
from pathlib import Path

import pytest


def test_blocker_file_exists():
    assert Path("tests/test_governance_blockers_minimum.py").exists()


@pytest.mark.parametrize(
    "module_path",
    [
        "services.governance.deployment_truth",
        "services.governance.campaign_state",
        "services.governance.campaign_fingerprint",
        "services.governance.campaign_state_machine",
        "services.governance.campaign_validation",
        "services.governance.invalidation",
        "services.governance.decision_engine",
        "services.governance.claims_guard",
        "services.governance.operator_overrides",
    ],
)
def test_required_governance_modules_exist(module_path):
    mod = importlib.import_module(module_path)
    assert mod is not None


def test_run_campaign_interface_exists():
    from services.analytics.paper_strategy_evidence_service import run_campaign

    assert callable(run_campaign)


def test_write_status_interface_exists():
    from services.analytics.paper_strategy_evidence_service import _write_status

    assert callable(_write_status)


def test_auth_capabilities_interface_exists():
    from services.security.auth_capabilities import auth_capabilities

    assert callable(auth_capabilities)


def test_auth_runtime_guard_status_interface_exists():
    from services.security.auth_runtime_guard import auth_runtime_guard_status

    assert callable(auth_runtime_guard_status)


def test_claim_boundaries_interface_exists():
    from dashboard.services.digest.builders import CLAIM_BOUNDARIES

    assert isinstance(CLAIM_BOUNDARIES, list)
    assert len(CLAIM_BOUNDARIES) > 0


def test_apply_bundle_interface_exists():
    from services.profiles.bundles import apply_bundle

    assert callable(apply_bundle)


def test_default_auth_posture_local_private_only():
    from dashboard.services.view_data import update_settings_view, get_settings_view

    original = get_settings_view()
    original_security = dict(original.get("security", {}))

    try:
        update_settings_view(
            {
                "security": {
                    "auth_scope": "local_private_only",
                    "remote_access_requires_mfa": True,
                    "outer_access_control": "",
                }
            }
        )

        settings = get_settings_view()
        security = settings.get("security", {})

        assert security.get("auth_scope") == "local_private_only"
        assert security.get("remote_access_requires_mfa") is True
    finally:
        update_settings_view({"security": original_security})


def test_auth_capabilities_default_not_hardened():
    from dashboard.services.view_data import update_settings_view, get_settings_view
    from services.security.auth_capabilities import auth_capabilities

    original = get_settings_view()
    original_security = dict(original.get("security", {}))

    try:
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
        assert "not hardened" in str(caps["scope_detail"]).lower()
    finally:
        update_settings_view({"security": original_security})


def test_claim_boundaries_include_expected_guardrails():
    from dashboard.services.digest.builders import CLAIM_BOUNDARIES

    joined = " | ".join(str(x) for x in CLAIM_BOUNDARIES).lower()

    assert "not live profitability proof" in joined
    assert "stock support is not proven" in joined
    assert "shorting is not fully validated" in joined


def test_remote_candidate_readback_and_runtime_consumption():
    from dashboard.services.view_data import update_settings_view, get_settings_view
    from services.security.auth_runtime_guard import auth_runtime_guard_status

    original = get_settings_view()
    original_security = dict(original.get("security", {}))

    try:
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
        status = auth_runtime_guard_status()

        assert security.get("auth_scope") == "remote_public_candidate"
        assert security.get("remote_access_requires_mfa") is True
        assert security.get("outer_access_control") == "cloudflare_access"
        assert status.get("auth_scope") == "remote_public_candidate"
    finally:
        update_settings_view({"security": original_security})


def test_apply_bundle_real_schema_still_callable():
    from services.profiles.bundles import apply_bundle, BUNDLES

    base_cfg = {
        "risk": {"max_order_quote": 10.0},
        "strategy": {"trade_enabled": True},
    }

    bundle_name = next(iter(BUNDLES.keys()))
    result = apply_bundle(base_cfg, bundle_name, overrides={})

    assert isinstance(result, dict)
    assert "risk" in result
    assert "strategy" in result


def test_direct_origin_blocking():
    import pytest
    from services.security.direct_origin_guard import enforce_direct_origin_block

    with pytest.raises(PermissionError):
        enforce_direct_origin_block(
            auth_scope="remote_public_candidate",
            outer_access_control="cloudflare_access",
            headers={},
        )

    assert enforce_direct_origin_block(
        auth_scope="remote_public_candidate",
        outer_access_control="cloudflare_access",
        headers={"X-Authenticated-Proxy": "1"},
    ) is True


def test_replay_tooling():
    from services.backtest.signal_replay import replay_signals_on_ohlcv

    ohlcv = [
        [1000, 100.0, 101.0, 99.0, 100.0, 1.0],
        [2000, 110.0, 111.0, 109.0, 110.0, 1.0],
    ]
    signals = [
        {"ts_ms": 1000, "action": "buy"},
        {"ts_ms": 2000, "action": "sell"},
    ]

    out = replay_signals_on_ohlcv(
        ohlcv,
        signals,
        fee_bps=0.0,
        slippage_bps=0.0,
        initial_cash=10000.0,
    )

    assert out["initial_cash"] == 10000.0
    assert out["signals_used"] == 2
    assert len(out["trades"]) == 2
    assert len(out["equity"]) == 2
    assert out["final_equity"] == 11000.0
    assert out["realized_pnl_est"] == 1000.0


def test_phase4_campaign_output(tmp_path):
    from services.backtest.evidence_cycle import write_decision_record

    report = {
        "as_of": "2026-03-19T12:00:00Z",
        "symbol": "ETH/USDT",
        "aggregate_leaderboard": {"rows": []},
        "decisions": [],
        "windows": [],
        "window_count": 0,
        "initial_cash": 10000.0,
        "fee_bps": 10.0,
        "slippage_bps": 5.0,
    }

    artifact_path = str(tmp_path / "strategy_evidence.latest.json")
    Path(artifact_path).write_text('{"ok": true}', encoding="utf-8")

    out = write_decision_record(
        report,
        path=str(tmp_path / "decision_record.md"),
        artifact_path=artifact_path,
    )

    target = Path(out["path"])
    assert out["ok"] is True
    assert target.exists()
    text = target.read_text(encoding="utf-8")
    assert text.strip() != ""
    assert artifact_path in text
