from __future__ import annotations

import importlib


def _reload_paths(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_config_editor_compat_helpers_delegate(monkeypatch, tmp_path):
    _reload_paths(monkeypatch, tmp_path)

    import services.admin.config_editor as config_editor
    import services.admin.kill_switch as kill_switch
    import services.admin.state_report as state_report

    importlib.reload(config_editor)
    importlib.reload(kill_switch)
    importlib.reload(state_report)

    armed = config_editor.set_armed(True)
    assert armed.get("armed") is True

    health = config_editor.read_health("missing_service")
    assert isinstance(health, dict)

    monkeypatch.setattr(
        state_report,
        "maybe_auto_update_state_on_snapshot",
        lambda tag="": {"ok": True, "tag": str(tag)},
    )
    updated = config_editor.maybe_auto_update_state_on_snapshot({"tag": "test_tag"})
    assert updated == {"ok": True, "tag": "test_tag"}
from pathlib import Path

from services.setup.config_manager import ConfigManager, apply_risk_preset


def test_config_manager_ensure_creates_default_file(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"
    cm = ConfigManager(cfg_path=str(cfg_path))

    cfg = cm.ensure()

    assert cfg_path.exists()
    assert cfg["symbols"] == ["BTC/USD"]
    assert cfg["pipeline"]["exchange_id"] == "coinbase"
    assert cfg["execution"]["executor_mode"] == "paper"
    assert cfg["execution"]["live_enabled"] is False


def test_apply_risk_preset_safe_paper_sets_safe_defaults():
    cfg = {
        "symbols": ["ETH/USD"],
        "pipeline": {"exchange_id": "kraken"},
        "execution": {"executor_mode": "live", "live_enabled": True},
        "risk": {},
    }

    out = apply_risk_preset(cfg, "safe_paper")

    assert out["execution"]["executor_mode"] == "paper"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["exchange_allowlist"] == ["kraken"]
    assert out["risk"]["symbol_allowlist"] == ["ETH/USD"]
    assert out["risk"]["max_notional"] == 50.0


def test_apply_risk_preset_live_locked_keeps_live_disabled_unless_user_enables():
    cfg = {
        "symbols": ["BTC/USD"],
        "pipeline": {"exchange_id": "coinbase"},
        "execution": {"executor_mode": "paper", "live_enabled": False},
        "risk": {},
    }

    out = apply_risk_preset(cfg, "live_locked")

    assert out["execution"]["executor_mode"] == "live"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["exchange_allowlist"] == ["coinbase"]
    assert out["risk"]["symbol_allowlist"] == ["BTC/USD"]
    assert out["risk"]["reject_if_price_unknown_for_exposure"] is True

def test_apply_risk_preset_paper_relaxed_zeros_limits():
    cfg = {
        "symbols": ["BTC/USD"],
        "pipeline": {"exchange_id": "coinbase"},
        "execution": {"executor_mode": "live", "live_enabled": True},
        "risk": {"max_notional": 123.0, "max_total_notional": 456.0},
    }

    out = apply_risk_preset(cfg, "paper_relaxed")

    assert out["execution"]["executor_mode"] == "paper"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["min_notional"] == 0.0
    assert out["risk"]["max_notional"] == 0.0
    assert out["risk"]["max_intents_per_day"] == 0
    assert out["risk"]["max_daily_loss_quote"] == 0.0
    assert out["risk"]["max_position_notional_per_symbol"] == 0.0
    assert out["risk"]["max_total_notional"] == 0.0


def test_config_manager_load_merges_partial_file_with_defaults(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        "pipeline:\n  exchange_id: kraken\nsymbols:\n  - ETH/USD\n",
        encoding="utf-8",
    )

    cm = ConfigManager(cfg_path=str(cfg_path))
    cfg = cm.load()

    assert cfg["pipeline"]["exchange_id"] == "kraken"
    assert cfg["symbols"] == ["ETH/USD"]
    assert cfg["execution"]["executor_mode"] == "paper"
    assert cfg["execution"]["live_enabled"] is False
    assert "risk" in cfg


def test_apply_risk_preset_safe_paper_falls_back_to_defaults_when_missing_fields():
    cfg = {
        "symbols": [],
        "pipeline": {},
        "execution": {},
        "risk": {},
    }

    out = apply_risk_preset(cfg, "safe_paper")

    assert out["execution"]["executor_mode"] == "paper"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["exchange_allowlist"] == ["coinbase"]
    assert out["risk"]["symbol_allowlist"] == ["BTC/USD"]


def test_apply_risk_preset_unknown_preset_leaves_existing_values():
    cfg = {
        "symbols": ["SOL/USD"],
        "pipeline": {"exchange_id": "kraken"},
        "execution": {"executor_mode": "paper", "live_enabled": False},
        "risk": {"max_notional": 77.0},
    }

    out = apply_risk_preset(cfg, "unknown_preset_name")

    assert out["execution"]["executor_mode"] == "paper"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["max_notional"] == 77.0
    assert out["pipeline"]["exchange_id"] == "kraken"
    assert out["symbols"] == ["SOL/USD"]

