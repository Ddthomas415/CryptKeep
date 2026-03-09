from __future__ import annotations

import json

from services.admin import first_run_wizard as frw



def test_apply_safe_defaults_persists_and_arms_kill_switch(monkeypatch):
    calls: dict[str, object] = {}

    def _set_armed(state: bool, note: str = "") -> dict:
        calls["set_armed"] = (state, note)
        return {"armed": bool(state), "note": note}

    def _save(cfg, dry_run=False):
        calls["save"] = (cfg, dry_run)
        return True, "Saved"

    monkeypatch.setattr(frw, "ensure_user_yaml_exists", lambda: True)
    monkeypatch.setattr(frw, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {
            "risk": {"enable_live": True, "max_trades_per_day": 2},
            "market_data_poller": {"venue": "binance"},
        },
    )
    monkeypatch.setattr(frw, "kill_state", lambda: {"armed": False, "note": "before"})
    monkeypatch.setattr(frw, "set_armed", _set_armed)
    monkeypatch.setattr(frw, "save_user_yaml", _save)

    out = frw.apply_safe_defaults(dry_run=False)

    saved_cfg, dry_run = calls["save"]
    assert out["ok"] is True
    assert dry_run is False
    assert calls["set_armed"] == (True, "first_run_defaults")
    assert saved_cfg["risk"]["enable_live"] is False
    assert saved_cfg["risk"]["max_trades_per_day"] == 2
    assert saved_cfg["preflight"]["venues"] == ["coinbase", "gateio"]
    assert saved_cfg["safety"]["auto_disable_live_on_start"] is True
    assert out["kill_switch"]["armed"] is True



def test_apply_safe_defaults_dry_run_does_not_mutate_kill_switch(monkeypatch):
    calls: dict[str, object] = {"set_armed": 0}

    def _set_armed(state: bool, note: str = "") -> dict:
        calls["set_armed"] = int(calls["set_armed"]) + 1
        return {"armed": bool(state), "note": note}

    def _save(cfg, dry_run=False):
        calls["save"] = dry_run
        return True, "Dry run OK"

    monkeypatch.setattr(frw, "ensure_user_yaml_exists", lambda: True)
    monkeypatch.setattr(frw, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(frw, "load_user_yaml", lambda: {})
    monkeypatch.setattr(frw, "kill_state", lambda: {"armed": False, "note": "current"})
    monkeypatch.setattr(frw, "set_armed", _set_armed)
    monkeypatch.setattr(frw, "save_user_yaml", _save)

    out = frw.apply_safe_defaults(dry_run=True)

    assert out["ok"] is True
    assert calls["save"] is True
    assert calls["set_armed"] == 0
    assert out["kill_switch"] == {"armed": False, "note": "current"}



def test_run_preflight_now_forwards_supported_options(monkeypatch):
    captured: dict[str, object] = {}

    async def _run_preflight(*, venues, symbols, time_tolerance_ms, do_private_check):
        captured.update(
            {
                "venues": venues,
                "symbols": symbols,
                "time_tolerance_ms": time_tolerance_ms,
                "do_private_check": do_private_check,
            }
        )
        return {"ok": True, "venues": venues, "symbols": symbols}

    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {"preflight": {"venues": ["Coinbase"], "symbols": ["ETH/USD"], "time_tolerance_ms": 987, "private_check": True}},
    )
    monkeypatch.setattr(frw, "run_preflight", _run_preflight)

    out = frw.run_preflight_now()

    assert out["ok"] is True
    assert captured == {
        "venues": ["coinbase"],
        "symbols": ["ETH/USD"],
        "time_tolerance_ms": 987,
        "do_private_check": True,
    }


def test_compute_first_run_status_uses_snapshot_based_cache_audit(monkeypatch, tmp_path):
    snapshot = tmp_path / "market_data_poller.latest.json"
    snapshot.write_text(
        json.dumps(
            {
                "venue": "coinbase",
                "pairs": ["BTC/USD"],
                "ticks": [{"symbol": "BTC/USD"}],
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(frw, "MARKET_DATA_SNAPSHOT", snapshot)
    monkeypatch.setattr(frw, "ensure_user_yaml_exists", lambda: True)
    monkeypatch.setattr(frw, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(frw, "kill_state", lambda: {"armed": True, "note": "default"})
    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {
            "market_data_poller": {
                "venue": "coinbase",
                "symbols": ["BTC/USD", "ETH/USD"],
                "extra_pairs": [],
            }
        },
    )

    out = frw.compute_first_run_status()

    assert out["cache"]["required_pairs_count"] == 2
    assert out["cache"]["missing_pairs_count"] == 1
    assert out["cache"]["missing_pairs"] == ["ETH/USD"]


def test_compute_first_run_status_reports_normalized_live_enabled(monkeypatch, tmp_path):
    snapshot = tmp_path / "market_data_poller.latest.json"
    snapshot.write_text(json.dumps({"venue": "coinbase", "pairs": ["BTC/USD"]}), encoding="utf-8")

    monkeypatch.setattr(frw, "MARKET_DATA_SNAPSHOT", snapshot)
    monkeypatch.setattr(frw, "ensure_user_yaml_exists", lambda: True)
    monkeypatch.setattr(frw, "ensure_kill_default", lambda: None)
    monkeypatch.setattr(frw, "kill_state", lambda: {"armed": True, "note": "default"})
    monkeypatch.setattr(frw, "load_user_yaml", lambda: {"live": {"enabled": True}})

    out = frw.compute_first_run_status()

    assert out["live_enabled"] is True
    assert out["risk_enable_live"] is True
