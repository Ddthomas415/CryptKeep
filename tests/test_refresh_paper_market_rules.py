"""Synthetic public metadata, private temporary configs/caches; no HTTP/account access."""
from dataclasses import replace
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3

import pytest

from tests.test_paper_cash_entry import rules

ROOT = Path(__file__).resolve().parents[1]


def config():
    return {"execution": {"live_enabled": False}, "live_execution": {"armed": False},
            "paper_trading": {"enabled": True, "quote_currency": "USD", "require_fresh_snapshot_quotes": True,
                              "use_ccxt_fallback": False},
            "strategy_runner": {"venue": "coinbase", "symbols": ["BTC/USD"],
                                "paper_entry_sizing": "available_cash_v1", "auto_select_best_venue": False,
                                "position_aware": True, "sell_full_position": True, "order_type": "market"},
            "api_key": "SYNTHETIC-private-never-output"}


@pytest.fixture
def rig(tmp_path, monkeypatch):
    source = Path(os.environ.get("CBP_RULE_REFRESH_BEFORE_SOURCE") or ROOT / "scripts/refresh_market_rules.py")
    spec = importlib.util.spec_from_file_location("_paper_metadata_command", source)
    command = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(command)
    monkeypatch.setattr(command, "default_exec_db", lambda: pytest.fail("paper mode used ambient DB"))
    monkeypatch.setattr(socket.socket, "connect", lambda *a: pytest.fail("real network attempted"))
    state = tmp_path / "paper-account"
    for folder in (state / "runtime/config", state / "data"):
        folder.mkdir(parents=True)
    (state / "runtime/config/user.yaml").write_text(json.dumps(config()))
    calls = []

    def fetch(db, venue, symbol, **options):
        from services.markets.cache_sqlite import upsert
        calls.append((db, venue, symbol))
        result = rules(symbol.replace("-", "/"))
        upsert(db, result)
        return result

    monkeypatch.setattr(command, "fetch_and_cache", fetch)
    return command, state, calls, fetch


def invoke(rig, *, symbols="BTC-USD", venue="coinbase", state=None):
    command, default_state, _, _ = rig
    return command.main(["--paper-state-dir", str(default_state if state is None else state),
                         "--venue", venue, "--symbols", symbols])


def set_config(rig, edit):
    path = rig[1] / "runtime/config/user.yaml"
    cfg = json.loads(path.read_text())
    edit(cfg)
    path.write_text(json.dumps(cfg))


def test_explicit_state_bypasses_all_ambient_databases_and_is_readable_by_sizer(rig, monkeypatch, capsys, tmp_path):
    from services.execution.paper_cash_entry import _cached_rules
    for key in ("EXEC_DB_PATH", "CBP_DB_PATH", "CBP_STATE_DIR"):
        monkeypatch.setenv(key, str(tmp_path / (key + "-must-stay-absent")))
    assert invoke(rig) == 0
    output = json.loads(capsys.readouterr().out)
    db = rig[1] / "data/execution.sqlite"
    assert output["ok"] and output["exec_db"] == str(db)
    assert rig[2] == [(str(db), "coinbase", "BTC-USD")]
    read, _ = _cached_rules("coinbase", "BTC/USD", datetime.now(timezone.utc).isoformat(), cache_path=db)
    assert read == rules()
    assert not list(tmp_path.glob("*-must-stay-absent"))


@pytest.mark.parametrize("bad", ["relative", "absent", "data_link", "db_link", "db_hardlink", "sidecar_link", "config_link"])
def test_bad_targets_refuse_before_fetch_or_cache_side_effect(rig, tmp_path, capsys, bad):
    state = rig[1]
    victim = tmp_path / "unrelated-file"
    victim.write_text("UNCHANGED")
    target = state
    if bad == "relative":
        target = Path("relative-state")
    elif bad == "absent":
        target = tmp_path / "does-not-exist"
    elif bad == "data_link":
        (state / "data").rmdir()
        (state / "data").symlink_to(tmp_path, target_is_directory=True)
    elif bad == "db_link":
        (state / "data/execution.sqlite").symlink_to(victim)
    elif bad == "db_hardlink":
        os.link(victim, state / "data/execution.sqlite")
    elif bad == "sidecar_link":
        (state / "data/execution.sqlite-wal").symlink_to(victim)
    else:
        path = state / "runtime/config/user.yaml"
        path.unlink()
        path.symlink_to(victim)
    assert invoke(rig, state=target) == 2
    assert not rig[2] and victim.read_text() == "UNCHANGED"
    assert json.loads(capsys.readouterr().out)["ok"] is False


@pytest.mark.parametrize("section,key,value", [
    ("execution", "live_enabled", True), ("live_execution", "armed", True),
    ("paper_trading", "enabled", False), ("paper_trading", "quote_currency", "USDT"),
    ("paper_trading", "require_fresh_snapshot_quotes", False), ("paper_trading", "use_ccxt_fallback", True),
    ("strategy_runner", "paper_entry_sizing", "fixed"), ("strategy_runner", "symbols", ["BTC/USD", "ETH/USD"]),
])
def test_nonpaper_or_incompatible_layout_refuses_before_fetch(rig, capsys, section, key, value):
    set_config(rig, lambda cfg: cfg[section].update({key: value}))
    assert invoke(rig) == 2 and not rig[2]
    assert "SYNTHETIC-private" not in capsys.readouterr().out


@pytest.mark.parametrize("symbols", ["", "BTC-USDT", "ETH-USD", "BTC-USD,ETH-USD", "BTC-USD,BTC/USD", "BTC-USD,"])
def test_all_symbols_are_validated_before_first_fetch(rig, capsys, symbols):
    assert invoke(rig, symbols=symbols) == 2 and not rig[2]
    assert not (rig[1] / "data/execution.sqlite").exists()


def test_group_b_scope_includes_selected_and_still_held_coins(rig, capsys):
    from services.market_data.group_b_selection import POLICY
    set_config(rig, lambda cfg: cfg["strategy_runner"].update({
        "group_b_selection": {"policy": POLICY, "slot": 1, "directory": "/synthetic/slots"}}))
    assert invoke(rig, symbols="BTC-USD,ETH-USD,SOL-USD") == 0
    output = json.loads(capsys.readouterr().out)
    assert [x["symbol"] for x in output["results"]] == ["BTC-USD", "ETH-USD", "SOL-USD"]


@pytest.mark.parametrize("bad", ["inactive", "wrong_identity", "missing_step", "nan_step", "zero_step", "unknown_minimum", "restricted", "unknown_mode", "fetch_error", "write_error", "mismatch"])
def test_unusable_or_failed_refresh_never_reports_success(rig, monkeypatch, capsys, bad):
    command, _, calls, original = rig

    def fetch(db, venue, symbol, **options):
        from services.markets.cache_sqlite import upsert
        if bad in {"fetch_error", "write_error"}:
            raise RuntimeError("SYNTHETIC-private-provider-detail")
        result = rules()
        if bad == "inactive":
            result = replace(result, active=False, meta={"error": "FETCH_FAILED", "detail": "SYNTHETIC-private-provider-detail"})
        elif bad == "wrong_identity":
            result = replace(result, native_symbol="ETH-USD")
        elif bad in {"missing_step", "nan_step", "zero_step"}:
            result = replace(result, qty_step={"missing_step": None, "nan_step": float("nan"), "zero_step": 0}[bad])
        elif bad == "unknown_minimum":
            result = replace(result, min_notional=None)
        elif bad in {"restricted", "unknown_mode"}:
            product = dict(result.meta["coinbase_product"])
            product["limit_only"] = True if bad == "restricted" else "false"
            result = replace(result, meta={"coinbase_product": product})
        upsert(db, result)
        return replace(result, min_qty=99) if bad == "mismatch" else result

    monkeypatch.setattr(command, "fetch_and_cache", fetch)
    assert invoke(rig) == 1
    text = capsys.readouterr().out
    assert "SYNTHETIC-private" not in text and "NaN" not in text
    assert json.loads(text)["ok"] is False


def test_partial_batch_is_reported_as_partial_not_rolled_back(rig, monkeypatch, capsys):
    from services.market_data.group_b_selection import POLICY
    set_config(rig, lambda cfg: cfg["strategy_runner"].update({"group_b_selection": {"policy": POLICY, "slot": 1}}))
    command, state, calls, original = rig

    def fetch(db, venue, symbol, **options):
        if symbol == "ETH-USD":
            raise OSError("SYNTHETIC-private-write-failure")
        return original(db, venue, symbol)

    monkeypatch.setattr(command, "fetch_and_cache", fetch)
    assert invoke(rig, symbols="BTC-USD,ETH-USD") == 1
    out = json.loads(capsys.readouterr().out)
    assert [x["ok"] for x in out["results"]] == [True, False]
    with sqlite3.connect(state / "data/execution.sqlite") as con:
        assert con.execute("SELECT canonical_symbol FROM market_rules_cache").fetchall() == [("BTC-USD",)]


def test_legacy_invocation_keeps_existing_destination_and_defaults(rig, monkeypatch, tmp_path, capsys):
    command = rig[0]
    legacy = str(tmp_path / "legacy.sqlite")
    monkeypatch.setattr(command, "default_exec_db", lambda: legacy)
    assert command.main(["--venue", "coinbase"]) == 0
    assert [(v, s) for _, v, s in rig[2]] == [("coinbase", "BTC-USD"), ("coinbase", "ETH-USD")]
    assert json.loads(capsys.readouterr().out)["exec_db"] == legacy


def fake_coinbase(monkeypatch, *, amount=1, price=.01, raw_amount="1", raw_price=".01", mode=4):
    import sys
    from types import SimpleNamespace
    market = {"id": "BTC-USD", "active": True, "precision": {"amount": amount, "price": price},
              "limits": {"amount": {"min": 1}, "cost": {"min": 1}},
              "info": {**rules().meta["coinbase_product"], "base_increment": raw_amount,
                       "quote_increment": raw_price}}

    class Exchange:
        precisionMode = mode

        def __init__(self, options):
            assert options == {"enableRateLimit": True}  # no account credentials

        def load_markets(self):
            return {"BTC/USD": market}

    monkeypatch.setitem(sys.modules, "ccxt", SimpleNamespace(coinbase=Exchange, TICK_SIZE=4))
    return market


def test_paper_optin_uses_native_whole_unit_tick_not_decimal_count(monkeypatch):
    from services.markets.fetch_coinbase_ccxt import fetch_rules
    # 2026-11-14: owner approved extending the reviewed correction to shared calls.
    # Preserve the old result as an explicit historical control, not a new expectation.
    import importlib.util
    old_path = ROOT / "docs/review_artifacts/coinbase_precision_shared_20261114/fetch_coinbase_before.py"
    spec = importlib.util.spec_from_file_location("_before_shared_precision", old_path)
    old = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(old)
    fake_coinbase(monkeypatch)
    assert old.fetch_rules("BTC-USD").qty_step == .1
    assert fetch_rules("BTC-USD").qty_step == 1
    strict = fetch_rules("BTC-USD", strict_precision=True)
    assert strict.active and strict.qty_step == 1 and strict.price_tick == .01


@pytest.mark.parametrize("changes", [
    {"mode": 2}, {"amount": 1, "raw_amount": "2"}, {"amount": None},
    {"amount": 0}, {"amount": float("nan")}, {"raw_amount": "1.00000000000000001"},
    {"raw_price": None}, {"price": True},
])
def test_strict_precision_refuses_unknown_inconsistent_or_unrepresentable_increment(monkeypatch, changes):
    from services.markets.fetch_coinbase_ccxt import fetch_rules
    fake_coinbase(monkeypatch, **changes)
    assert fetch_rules("BTC-USD", strict_precision=True).active is False


def test_strict_provider_to_cache_to_actual_cash_reader(rig, monkeypatch, capsys):
    from services.markets.rules import fetch_and_cache
    from services.execution.paper_cash_entry import _cached_rules
    fake_coinbase(monkeypatch)
    monkeypatch.setattr(rig[0], "fetch_and_cache", fetch_and_cache)
    assert invoke(rig) == 0
    output = json.loads(capsys.readouterr().out)
    cached, _ = _cached_rules("coinbase", "BTC/USD", datetime.now(timezone.utc).isoformat(),
                              cache_path=output["exec_db"])
    assert cached.qty_step == 1


def test_native_price_increment_precedes_quote_increment(monkeypatch):
    from services.markets.fetch_coinbase_ccxt import fetch_rules
    market = fake_coinbase(monkeypatch)
    market["info"].update(price_increment=".01", quote_increment="1")
    strict = fetch_rules("BTC-USD", strict_precision=True)
    assert strict.active and strict.price_tick == .01
