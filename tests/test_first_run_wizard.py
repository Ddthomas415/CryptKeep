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
                "symbols": ["BTC/USD"],
                "extra_pairs": [],
            }
        },
    )

    out = frw.compute_first_run_status()

    assert out["cache"]["required_pairs_count"] == 1
    assert out["cache"]["missing_pairs_count"] == 0
    assert out["cache"]["missing_pairs"] == []


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

def test_run_preflight_now_uses_safe_defaults_when_preflight_missing(monkeypatch):
    captured = {}

    async def _run_preflight(*, venues, symbols, time_tolerance_ms, do_private_check):
        captured.update(
            {
                "venues": venues,
                "symbols": symbols,
                "time_tolerance_ms": time_tolerance_ms,
                "do_private_check": do_private_check,
            }
        )
        return {"ok": True}

    monkeypatch.setattr(frw, "load_user_yaml", lambda: {})
    monkeypatch.setattr(frw, "run_preflight", _run_preflight)

    out = frw.run_preflight_now()

    assert out["ok"] is True
    assert captured == {
        "venues": ["coinbase", "gateio"],
        "symbols": ["BTC/USD"],
        "time_tolerance_ms": 1500,
        "do_private_check": False,
    }


def test_populate_cache_now_includes_extra_pairs(monkeypatch):
    captured = {}

    async def _fetch_once(venue, req_pairs):
        captured["venue"] = venue
        captured["req_pairs"] = req_pairs
        return {"ok": True, "pairs": req_pairs}

    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {
            "market_data_poller": {
                "venue": "coinbase",
                "symbols": ["BTC/USD"],
                "extra_pairs": ["ETH/USD"],
            }
        },
    )
    monkeypatch.setattr(frw, "fetch_tickers_once", _fetch_once)

    out = frw.populate_cache_now()

    assert out["ok"] is True
    assert captured["venue"] == "coinbase"
    assert "BTC/USD" in captured["req_pairs"]
    assert "ETH/USD" in captured["req_pairs"]


def test_compute_first_run_status_ignores_snapshot_for_wrong_venue(monkeypatch, tmp_path):
    snapshot = tmp_path / "market_data_poller.latest.json"
    snapshot.write_text(
        json.dumps({"venue": "binance", "pairs": ["BTC/USD"]}),
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
                "symbols": ["BTC/USD"],
                "extra_pairs": [],
            }
        },
    )

    out = frw.compute_first_run_status()

    assert out["cache"]["missing_pairs_count"] == out["cache"]["required_pairs_count"]


def test_compute_first_run_status_handles_invalid_snapshot_json(monkeypatch, tmp_path):
    snapshot = tmp_path / "market_data_poller.latest.json"
    snapshot.write_text("{not-json", encoding="utf-8")

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
                "symbols": ["BTC/USD"],
                "extra_pairs": [],
            }
        },
    )

    out = frw.compute_first_run_status()

    assert out["cache"]["required_pairs_count"] >= 1


def test_merge_defaults_preserves_existing_nested_values():
    merged = frw.merge_defaults(
        {"risk": {"enable_live": True}},
        {"risk": {"enable_live": False, "max_trades_per_day": 3}},
    )

    assert merged["risk"]["enable_live"] is True
    assert merged["risk"]["max_trades_per_day"] == 3

def test_guided_setup_review_uses_current_user_config(monkeypatch):
    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {
            "symbols": ["ETH/USD", "BTC/USD"],
            "pipeline": {"exchange_id": "kraken", "strategy": "mean_reversion", "timeframe": "15m"},
            "execution": {"executor_mode": "live", "live_enabled": False},
            "risk": {
                "exchange_allowlist": ["kraken"],
                "symbol_allowlist": ["ETH/USD", "BTC/USD"],
                "max_notional": 100.0,
                "max_daily_loss_quote": 50.0,
                "max_total_notional": 400.0,
            },
        },
    )

    out = frw.guided_setup_review()

    assert out["exchange"] == "kraken"
    assert out["symbols"] == ["ETH/USD", "BTC/USD"]
    assert out["symbol_count"] == 2
    assert out["strategy"] == "mean_reversion"
    assert out["timeframe"] == "15m"
    assert out["executor_mode"] == "live"
    assert out["live_enabled"] is False
    assert out["checks"]["live_mode"] is True


def test_guided_setup_review_uses_defaults_when_config_empty(monkeypatch):
    monkeypatch.setattr(frw, "load_user_yaml", lambda: {})

    out = frw.guided_setup_review()

    assert out["exchange"] == "coinbase"
    assert out["symbols"] == ["BTC/USD"]
    assert out["symbol_count"] == 1
    assert out["executor_mode"] == "paper"
    assert out["live_enabled"] is False
    assert out["checks"]["paper_mode"] is True


def test_guided_setup_preflight_review_combines_summary_and_preflight(monkeypatch):
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "kraken", "symbol_count": 2})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": True, "ready": True})

    out = frw.guided_setup_preflight_review()

    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 2},
        "preflight": {"ok": True, "ready": True},
    }


def test_guided_setup_preflight_review_uses_live_preflight_payload(monkeypatch):
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "coinbase", "symbol_count": 1})
    monkeypatch.setattr(
        frw,
        "run_preflight_now",
        lambda: {"ok": False, "ready": False, "checks": {"market_data": "missing"}},
    )

    out = frw.guided_setup_preflight_review()

    assert out["summary"]["exchange"] == "coinbase"
    assert out["preflight"]["ok"] is False
    assert out["preflight"]["checks"]["market_data"] == "missing"


def test_guided_setup_apply_saves_patch_and_returns_review_and_preflight(monkeypatch):
    saved = {}

    monkeypatch.setattr(frw, "load_user_yaml", lambda: {"symbols": ["BTC/USD"], "execution": {"executor_mode": "paper", "live_enabled": False}})
    monkeypatch.setattr(frw, "save_user_yaml", lambda cfg: saved.setdefault("cfg", cfg))
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "kraken", "symbol_count": 2})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": True, "ready": True})

    out = frw.guided_setup_apply(
        {
            "symbols": ["ETH/USD", "BTC/USD"],
            "pipeline": {"exchange_id": "kraken"},
        }
    )

    assert saved["cfg"]["symbols"] == ["ETH/USD", "BTC/USD"]
    assert saved["cfg"]["pipeline"]["exchange_id"] == "kraken"
    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 2},
        "preflight": {"ok": True, "ready": True},
    }


def test_guided_setup_apply_without_patch_round_trips_existing_config(monkeypatch):
    saved = {}
    monkeypatch.setattr(frw, "load_user_yaml", lambda: {"symbols": ["BTC/USD"]})
    monkeypatch.setattr(frw, "save_user_yaml", lambda cfg: saved.setdefault("cfg", cfg))
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "coinbase", "symbol_count": 1})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": False, "ready": False})

    out = frw.guided_setup_apply()

    assert saved["cfg"]["symbols"] == ["BTC/USD"]
    assert out["summary"]["exchange"] == "coinbase"
    assert out["preflight"]["ok"] is False


def test_guided_setup_apply_preset_saves_preset_result(monkeypatch):
    saved = {}

    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {
            "symbols": ["ETH/USD"],
            "pipeline": {"exchange_id": "kraken"},
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "risk": {},
        },
    )
    monkeypatch.setattr(frw, "save_user_yaml", lambda cfg: saved.setdefault("cfg", cfg))
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "kraken", "symbol_count": 1})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": True, "ready": True})

    out = frw.guided_setup_apply_preset("live_locked")

    assert saved["cfg"]["execution"]["executor_mode"] == "live"
    assert saved["cfg"]["execution"]["live_enabled"] is False
    assert saved["cfg"]["risk"]["exchange_allowlist"] == ["kraken"]
    assert saved["cfg"]["risk"]["symbol_allowlist"] == ["ETH/USD"]
    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 1},
        "preflight": {"ok": True, "ready": True},
    }


def test_guided_setup_apply_preset_keeps_review_flow_when_unknown(monkeypatch):
    saved = {}

    monkeypatch.setattr(
        frw,
        "load_user_yaml",
        lambda: {
            "symbols": ["BTC/USD"],
            "pipeline": {"exchange_id": "coinbase"},
            "execution": {"executor_mode": "paper", "live_enabled": False},
            "risk": {"max_notional": 77.0},
        },
    )
    monkeypatch.setattr(frw, "save_user_yaml", lambda cfg: saved.setdefault("cfg", cfg))
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "coinbase", "symbol_count": 1})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": False, "ready": False})

    out = frw.guided_setup_apply_preset("unknown_preset_name")

    assert saved["cfg"]["risk"]["max_notional"] == 77.0
    assert out["summary"]["exchange"] == "coinbase"
    assert out["preflight"]["ok"] is False


def test_guided_setup_state_combines_summary_preflight_and_status(monkeypatch):
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "kraken", "symbol_count": 2})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": True, "ready": True})
    monkeypatch.setattr(frw, "compute_first_run_status", lambda: {"config_ok": True, "cache": {"missing_pairs_count": 0}})

    out = frw.guided_setup_state()

    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 2},
        "preflight": {"ok": True, "ready": True},
        "status": {"config_ok": True, "cache": {"missing_pairs_count": 0}},
    }


def test_guided_setup_state_preserves_failing_preflight_and_status(monkeypatch):
    monkeypatch.setattr(frw, "guided_setup_review", lambda: {"exchange": "coinbase", "symbol_count": 1})
    monkeypatch.setattr(frw, "run_preflight_now", lambda: {"ok": False, "ready": False})
    monkeypatch.setattr(frw, "compute_first_run_status", lambda: {"config_ok": False, "kill_switch_armed": True})

    out = frw.guided_setup_state()

    assert out["summary"]["exchange"] == "coinbase"
    assert out["preflight"]["ok"] is False
    assert out["status"]["config_ok"] is False
    assert out["status"]["kill_switch_armed"] is True


def test_guided_setup_apply_state_returns_full_state_after_apply(monkeypatch):
    monkeypatch.setattr(frw, "guided_setup_apply", lambda patch=None: {"ok": True})
    monkeypatch.setattr(
        frw,
        "guided_setup_state",
        lambda: {
            "summary": {"exchange": "kraken", "symbol_count": 2},
            "preflight": {"ok": True, "ready": True},
            "status": {"config_ok": True},
        },
    )

    out = frw.guided_setup_apply_state(
        {"symbols": ["ETH/USD", "BTC/USD"], "pipeline": {"exchange_id": "kraken"}}
    )

    assert out == {
        "summary": {"exchange": "kraken", "symbol_count": 2},
        "preflight": {"ok": True, "ready": True},
        "status": {"config_ok": True},
    }


def test_guided_setup_apply_state_without_patch_still_returns_state(monkeypatch):
    monkeypatch.setattr(frw, "guided_setup_apply", lambda patch=None: {"ok": True})
    monkeypatch.setattr(
        frw,
        "guided_setup_state",
        lambda: {
            "summary": {"exchange": "coinbase", "symbol_count": 1},
            "preflight": {"ok": False, "ready": False},
            "status": {"config_ok": False},
        },
    )

    out = frw.guided_setup_apply_state()

    assert out["summary"]["exchange"] == "coinbase"
    assert out["preflight"]["ok"] is False
    assert out["status"]["config_ok"] is False

