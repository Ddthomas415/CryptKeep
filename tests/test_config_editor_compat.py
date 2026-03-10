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


def test_config_manager_ensure_preserves_existing_file(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        "pipeline:\n  exchange_id: kraken\nsymbols:\n  - SOL/USD\n",
        encoding="utf-8",
    )

    cm = ConfigManager(cfg_path=str(cfg_path))
    cfg = cm.ensure()

    assert cfg["pipeline"]["exchange_id"] == "kraken"
    assert cfg["symbols"] == ["SOL/USD"]
    assert "SOL/USD" in cfg_path.read_text(encoding="utf-8")


def test_config_manager_load_empty_file_returns_defaults(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text("", encoding="utf-8")

    cm = ConfigManager(cfg_path=str(cfg_path))
    cfg = cm.load()

    assert cfg["symbols"] == ["BTC/USD"]
    assert cfg["pipeline"]["exchange_id"] == "coinbase"
    assert cfg["execution"]["executor_mode"] == "paper"
    assert cfg["execution"]["live_enabled"] is False


def test_apply_risk_preset_safe_paper_overwrites_live_mode_flags():
    cfg = {
        "symbols": ["ADA/USD"],
        "pipeline": {"exchange_id": "kraken"},
        "execution": {"executor_mode": "live", "live_enabled": True},
        "risk": {"exchange_allowlist": ["coinbase"], "symbol_allowlist": ["BTC/USD"]},
    }

    out = apply_risk_preset(cfg, "safe_paper")

    assert out["execution"]["executor_mode"] == "paper"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["exchange_allowlist"] == ["kraken"]
    assert out["risk"]["symbol_allowlist"] == ["ADA/USD"]


def test_config_manager_load_missing_file_returns_defaults(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"

    cm = ConfigManager(cfg_path=str(cfg_path))
    cfg = cm.load()

    assert cfg["symbols"] == ["BTC/USD"]
    assert cfg["pipeline"]["exchange_id"] == "coinbase"
    assert cfg["execution"]["executor_mode"] == "paper"
    assert cfg["execution"]["live_enabled"] is False


def test_apply_risk_preset_live_locked_preserves_existing_risk_keys():
    cfg = {
        "symbols": ["BTC/USD"],
        "pipeline": {"exchange_id": "coinbase"},
        "execution": {"executor_mode": "paper", "live_enabled": False},
        "risk": {"max_notional": 25.0},
    }

    out = apply_risk_preset(cfg, "live_locked")

    assert out["execution"]["executor_mode"] == "live"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["max_notional"] == 100.0
    assert out["risk"]["exchange_allowlist"] == ["coinbase"]
    assert out["risk"]["symbol_allowlist"] == ["BTC/USD"]


def test_config_manager_ensure_load_round_trip_defaults(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"
    cm = ConfigManager(cfg_path=str(cfg_path))

    ensured = cm.ensure()
    loaded = cm.load()

    assert loaded["symbols"] == ensured["symbols"]
    assert loaded["pipeline"]["exchange_id"] == ensured["pipeline"]["exchange_id"]
    assert loaded["execution"]["executor_mode"] == ensured["execution"]["executor_mode"]
    assert loaded["execution"]["live_enabled"] == ensured["execution"]["live_enabled"]


def test_apply_risk_preset_live_locked_sets_expected_core_flags():
    cfg = {
        "symbols": ["ETH/USD"],
        "pipeline": {"exchange_id": "kraken"},
        "execution": {"executor_mode": "paper", "live_enabled": False},
        "risk": {},
    }

    out = apply_risk_preset(cfg, "live_locked")

    assert out["execution"]["executor_mode"] == "live"
    assert out["execution"]["live_enabled"] is False
    assert out["risk"]["exchange_allowlist"] == ["kraken"]
    assert out["risk"]["symbol_allowlist"] == ["ETH/USD"]
    assert out["risk"]["reject_if_price_unknown_for_exposure"] is True


def test_config_manager_load_keeps_existing_symbols_when_other_sections_missing(tmp_path):
    cfg_path = tmp_path / "config" / "trading.yaml"
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    cfg_path.write_text(
        "symbols:\n  - LTC/USD\n",
        encoding="utf-8",
    )

    cm = ConfigManager(cfg_path=str(cfg_path))
    cfg = cm.load()

    assert cfg["symbols"] == ["LTC/USD"]
    assert cfg["pipeline"]["exchange_id"] == "coinbase"
    assert cfg["execution"]["executor_mode"] == "paper"
    assert cfg["execution"]["live_enabled"] is False

from services.setup.config_manager import guided_setup_summary


def test_guided_setup_summary_uses_defaults_for_minimal_config():
    out = guided_setup_summary({})

    assert out["exchange"] == "coinbase"
    assert out["symbols"] == ["BTC/USD"]
    assert out["symbol_count"] == 1
    assert out["strategy"] == "ema"
    assert out["timeframe"] == "5m"
    assert out["executor_mode"] == "paper"
    assert out["live_enabled"] is False
    assert out["checks"]["has_symbols"] is True
    assert out["checks"]["has_exchange"] is True
    assert out["checks"]["paper_mode"] is True
    assert out["checks"]["live_mode"] is False
    assert out["checks"]["live_explicitly_enabled"] is False


def test_guided_setup_summary_reflects_live_locked_style_config():
    cfg = {
        "symbols": ["ETH/USD", "BTC/USD"],
        "pipeline": {
            "exchange_id": "kraken",
            "strategy": "mean_reversion",
            "timeframe": "15m",
        },
        "execution": {
            "executor_mode": "live",
            "live_enabled": False,
        },
        "risk": {
            "exchange_allowlist": ["kraken"],
            "symbol_allowlist": ["ETH/USD", "BTC/USD"],
            "max_notional": 100.0,
            "max_daily_loss_quote": 50.0,
            "max_total_notional": 400.0,
        },
    }

    out = guided_setup_summary(cfg)

    assert out["exchange"] == "kraken"
    assert out["symbols"] == ["ETH/USD", "BTC/USD"]
    assert out["symbol_count"] == 2
    assert out["strategy"] == "mean_reversion"
    assert out["timeframe"] == "15m"
    assert out["executor_mode"] == "live"
    assert out["live_enabled"] is False
    assert out["risk_preset_state"]["exchange_allowlist"] == ["kraken"]
    assert out["risk_preset_state"]["symbol_allowlist"] == ["ETH/USD", "BTC/USD"]
    assert out["risk_preset_state"]["max_notional"] == 100.0
    assert out["checks"]["paper_mode"] is False
    assert out["checks"]["live_mode"] is True
    assert out["checks"]["live_explicitly_enabled"] is False

