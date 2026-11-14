"""Review-only configuration checks; synthetic inputs and temporary state only."""
from datetime import datetime, timezone
import importlib
import json
import os
from pathlib import Path
import socket
import subprocess

import pytest
import yaml

HERE = Path(__file__).resolve().parent
PROFILES = sorted((HERE / "profiles").glob("*.yaml"))
STRATEGIES = {
    "breakout_default": "breakout_donchian",
    "ema_cross_default": "ema_cross",
    "mean_reversion_default": "mean_reversion_rsi",
}


def test_roster_is_exact_and_state_paths_are_disjoint():
    from services.control.group_a_account_units import render_group_a_account_units
    expected = {f"{preset.replace('_', '-')}-{asset.lower()}"
                for preset in STRATEGIES for asset in ("BTC", "ETH", "SOL")}
    assert len(PROFILES) == 9
    assert {path.stem for path in PROFILES} == expected
    units = render_group_a_account_units("profilereview", service_user="cbp-ga-review")
    states = set()
    for _, argv in units.launch_args:
        state = next(part.split("=", 1)[1] for part in argv if part.startswith("CBP_STATE_DIR="))
        states.add(state)
    assert len(states) == 9
    assert {Path(path).name for path in states} == expected
    assert all("ExecStart=" not in fragment for _, fragment in units.account_files)


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("profile verification attempted external activity")

    for key in tuple(os.environ):
        if key.startswith("CBP_") or key in {"EXEC_DB_PATH", "EXEC_DB", "DATABASE_URL"}:
            monkeypatch.delenv(key)
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("PYTHONDONTWRITEBYTECODE", "1")
    monkeypatch.setattr(socket.socket, "connect", forbidden)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    from tests.test_paper_reconciler_recovery import _reload_modules, _allow_submit_gates
    ledger, queue, _, engine, _ = _reload_modules(tmp_path)
    import services.admin.config_editor as config
    import services.execution.strategy_runner as runner
    importlib.reload(runner)
    import services.strategies.evidence_logger as evidence
    monkeypatch.setattr(evidence, "_version_stamp", lambda strategy_id, **kw: {
        "_strategy_id": strategy_id, "_stage": "synthetic", "_commit": "fixture"})
    # These unrelated operational/risk gates are synthetic, not acceptance evidence.
    _allow_submit_gates(monkeypatch, engine)
    monkeypatch.setattr(engine, "load_gates", lambda: {})
    monkeypatch.setattr(engine, "ExecutionGuardStoreSQLite", lambda: None)
    monkeypatch.setattr(engine.PaperEngine, "_price", forbidden)
    return tmp_path, monkeypatch, config, runner, engine, ledger, queue


def load_candidate(rig, path, edit=None):
    root, _, config, runner, engine, _, _ = rig
    raw = yaml.safe_load(path.read_text())
    if edit:
        edit(raw)
    assert config.CONFIG_PATH == root / "runtime/config/user.yaml"
    config.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config.CONFIG_PATH.write_text(yaml.safe_dump(raw))
    (root / "data").mkdir(exist_ok=True)
    assert config.load_user_yaml(strict=True) == raw
    return raw, runner._cfg(), engine._cfg()


def market_inputs(rig, symbol):
    root, mp, *_ = rig
    from services.market_data import tick_reader
    from services.market_data.local_data_reader import write_local_ohlcv_snapshot
    from services.markets.cache_sqlite import upsert
    from tests.test_paper_cash_entry import rules
    now = datetime.now(timezone.utc)
    stamp = int(now.timestamp() * 1000)
    quote = root / "synthetic-quotes.json"
    quote.write_text(json.dumps({"ts_ms": stamp, "ticks": [{
        "source": "public_ticker", "venue": "coinbase", "symbol": symbol,
        "symbol_mapped": symbol, "ticker_symbol": symbol,
        "bid": 99, "ask": 101, "ts_ms": stamp}]}))
    mp.setattr(tick_reader, "LATEST", quote)
    hour = int(now.replace(minute=0, second=0, microsecond=0).timestamp() * 1000)
    rows = [[hour - n * 3600000, 100, 102, 99, 100, 10] for n in range(59, -1, -1)]
    candle = write_local_ohlcv_snapshot("coinbase", symbol, rows, timeframe="1h", source="public_ohlcv")
    upsert(str(root / "data/execution.sqlite"), rules(symbol))
    # Cache upsert timestamps its write; the read clock must be after that write.
    return datetime.now(timezone.utc), quote, candle


@pytest.mark.parametrize("profile", PROFILES, ids=lambda path: path.stem)
def test_actual_loaders_sizing_guards_and_cash_carry_forward(isolated, profile):
    root, _, _, runner, engine, _, queue = isolated
    raw, cfg, paper = load_candidate(isolated, profile)
    from services.strategies.presets import get_preset
    from scripts.refresh_market_rules import _paper_target
    from services.execution.paper_cash_entry import size_paper_entry
    from services.execution.paper_weekly_slot import _paper_only
    preset = cfg["strategy_preset"]
    symbol = cfg["symbol"]
    assert cfg["strategy_id"] == STRATEGIES[preset]
    assert cfg["strategy"] == runner.build_strategy_block(
        name=STRATEGIES[preset], trade_enabled=True, params=get_preset(preset)["strategy"])
    assert profile.stem == f"{preset.replace('_', '-')}-{symbol.split('/')[0].lower()}"
    assert cfg["symbols"] == [symbol] and cfg["venue"] == "coinbase"
    assert cfg["signal_source"] == "public_ohlcv_1h" and cfg["loop_interval_sec"] == 15
    assert cfg["position_aware"] and cfg["sell_full_position"]
    assert cfg["auto_select_best_venue"] is False and cfg["order_type"] == "market"
    assert cfg["paper_entry_sizing"] == "available_cash_v1" and _paper_only(cfg)
    assert not {"risk", "qty", "allow_first_signal_trade", "group_b_selection"} & raw["strategy_runner"].keys()
    assert cfg["allow_first_signal_trade"] is False
    assert paper["enabled"] is True and paper["quote_currency"] == "USD"
    assert paper["starting_cash_quote"] == 1000 and paper["fee_bps"] == 50 and paper["slippage_bps"] == 0
    assert paper["use_ccxt_fallback"] is False
    assert paper["require_fresh_snapshot_quotes"] is True and paper["require_fresh_hourly_candles"] is True
    assert _paper_target(str(root), "coinbase", symbol.replace("/", "-")) == (
        root / "data/execution.sqlite", [symbol.replace("/", "-")])
    now, quote, candle = market_inputs(isolated, symbol)
    eng = engine.PaperEngine(clock=lambda: now.isoformat())
    qdb = queue.IntentQueueSQLite()
    assert eng.cash_quote() == 1000
    # Explicit test setup only. Fresh initialization does not populate this key;
    # the separately retained regression below must stay a visible failure.
    eng.db.set_state("quote_currency", "USD")
    sized = size_paper_entry(cfg=cfg, qdb=qdb, pdb=eng.db, venue="coinbase", symbol=symbol, now=now.isoformat())
    assert sized["ok"], sized
    qty = sized["qty"]
    assert qty * 101 * 1.005 <= 1000
    buy = eng.submit_order(client_order_id="candidate-buy", venue="coinbase", symbol=symbol,
                           side="buy", order_type="market", qty=qty)
    assert buy["ok"], buy
    assert eng.evaluate_open_orders()["filled"] == 1
    assert eng.cash_quote() == pytest.approx(1000 - qty * 100 * 1.005)
    assert eng.db.list_fills()[0]["fee"] == pytest.approx(qty * 100 * .005)
    restarted = engine.PaperEngine(clock=lambda: now.isoformat())
    assert restarted.cash_quote() == eng.cash_quote()  # No $1000 reset on initialization.
    payload = json.loads(quote.read_text())
    payload["ticks"][0].update(bid=119, ask=121)
    quote.write_text(json.dumps(payload))
    candle.unlink()  # Missing candles block entries but not exits at a fresh quote.
    sell = restarted.submit_order(client_order_id="candidate-sell", venue="coinbase", symbol=symbol,
                                 side="sell", order_type="market", qty=qty)
    assert sell["ok"], sell
    assert restarted.evaluate_open_orders()["filled"] == 1
    expected = 1000 - qty * 100 * 1.005 + qty * 120 * .995
    assert restarted.cash_quote() == pytest.approx(expected)
    again = size_paper_entry(cfg=cfg, qdb=qdb, pdb=restarted.db, venue="coinbase", symbol=symbol, now=now.isoformat())
    assert again["ok"] and float(again["evidence"]["cash"]) == pytest.approx(expected)
    refused = restarted.submit_order(client_order_id="candidate-missing-candle", venue="coinbase", symbol=symbol,
                                     side="buy", order_type="market", qty=again["qty"])
    assert refused["ok"] is False and "candle_data:" in refused["reason"]
    payload["ts_ms"] -= 6000
    quote.write_text(json.dumps(payload))
    assert size_paper_entry(cfg=cfg, qdb=qdb, pdb=restarted.db, venue="coinbase", symbol=symbol,
                            now=now.isoformat())["ok"] is False


@pytest.mark.xfail(strict=True, reason="Fresh account omits quote_currency required by cash sizing")
def test_fresh_account_is_immediately_readable_by_cash_sizing(isolated):
    _, _, _, _, engine, _, queue = isolated
    _, cfg, _ = load_candidate(isolated, PROFILES[0])
    now, _, _ = market_inputs(isolated, cfg["symbol"])
    eng = engine.PaperEngine(clock=lambda: now.isoformat())
    from services.execution.paper_cash_entry import size_paper_entry
    sized = size_paper_entry(cfg=cfg, qdb=queue.IntentQueueSQLite(), pdb=eng.db,
                             venue="coinbase", symbol=cfg["symbol"], now=now.isoformat())
    assert sized["ok"], sized


@pytest.mark.parametrize("section,key,value", [
    ("execution", "live_enabled", True), ("live_execution", "armed", True),
    ("paper_trading", "enabled", False), ("paper_trading", "require_fresh_snapshot_quotes", False),
    ("paper_trading", "use_ccxt_fallback", True), ("strategy_runner", "paper_entry_sizing", "fixed"),
    ("strategy_runner", "auto_select_best_venue", True), ("strategy_runner", "symbols", ["BTC/USD", "ETH/USD"]),
])
def test_policy_mutation_refuses_provisioning_before_fetch(isolated, section, key, value):
    root = isolated[0]
    from scripts.refresh_market_rules import _paper_target
    load_candidate(isolated, PROFILES[0], lambda raw: raw[section].update({key: value}))
    with pytest.raises(ValueError):
        _paper_target(str(root), "coinbase", "BTC-USD")
    assert not (root / "data/execution.sqlite").exists()
