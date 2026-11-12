"""Independent, offline R4 seal and boundary probes; no production file swaps."""
import difflib
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest


ARTIFACT = Path(__file__).resolve().parents[1]
ROOT = ARTIFACT.parents[2]


def test_seal_and_original_production_hunk_replay():
    expected = {
        "stage.diff": "59bc874c2b72e1f36f9b37b1ddaa0430dc4f9906dc9b219d614e40fa632df067",
        "hashes.json": "a9f8b3d77b1afb8f3aa59a38b7e8dfa1d558fa8b49ff37a8742835e84f6ca773",
        "original_0010.patch": "2bec0aa1fa88ec79c8e955dc769a778e3921f2841d5e0939e1faeec2f774aec3",
    }
    for name, digest in expected.items():
        assert hashlib.sha256((ARTIFACT / name).read_bytes()).hexdigest() == digest
    manifest = json.loads((ARTIFACT / "hashes.json").read_text())
    assert set(manifest["current"]) == {
        "services/market_data/tick_reader.py", "services/execution/paper_engine.py",
        "tests/test_market_snapshot_readers.py", "tests/test_tick_reader_exact_symbol.py",
    }
    chunks = []
    for name, digest in manifest["current"].items():
        old_path = ARTIFACT / "before" / name
        old = old_path.read_bytes() if old_path.exists() else b""
        current = (ROOT / name).read_bytes()
        assert hashlib.sha256(old).hexdigest() == manifest["before"][name]
        assert hashlib.sha256(current).hexdigest() == digest
    for name in ("services/market_data/tick_reader.py", "services/execution/paper_engine.py",
                 "tests/test_market_snapshot_readers.py", "tests/test_tick_reader_exact_symbol.py"):
        old_path = ARTIFACT / "before" / name
        old = old_path.read_text() if old_path.exists() else ""
        chunks.extend(difflib.unified_diff(old.splitlines(keepends=True),
            (ROOT / name).read_text().splitlines(keepends=True),
            fromfile="before/" + name, tofile="after/" + name))
    assert "".join(chunks).encode() == (ARTIFACT / "stage.diff").read_bytes()

    patch = (ARTIFACT / "original_0010.patch").read_text()
    for name in ("services/market_data/tick_reader.py", "services/execution/paper_engine.py"):
        section = patch.split(f"diff --git a/{name} b/{name}\n", 1)[1].split("diff --git ", 1)[0]
        result = (ARTIFACT / "before" / name).read_text()
        for body in re.split(r"(?m)^@@[^\n]*\n", section)[1:]:
            lines = []
            for line in body.splitlines(keepends=True):
                if not line.startswith((" ", "+", "-")):
                    break
                lines.append(line)
            old = "".join(line[1:] for line in lines if line[0] in " -")
            new = "".join(line[1:] for line in lines if line[0] in " +")
            assert old and result.count(old) == 1
            result = result.replace(old, new, 1)
        assert result.encode() == (ROOT / name).read_bytes()


@pytest.fixture
def flow(monkeypatch, tmp_path):
    from services.execution import paper_engine as pe
    from services.market_data import tick_reader as reader
    from storage import paper_trading_sqlite as store

    path = tmp_path / "snapshot.json"
    monkeypatch.setattr(reader, "LATEST", path)
    monkeypatch.setattr(pe, "get_best_bid_ask_last", reader.get_best_bid_ask_last)
    monkeypatch.setattr(store, "DB_PATH", tmp_path / "paper.sqlite")
    monkeypatch.setattr(pe, "_cfg", lambda: {
        "starting_cash_quote": 1000, "quote_currency": "USD", "enabled": True,
        "max_order_qty": 1e9, "fee_bps": 50, "slippage_bps": 0,
        "use_ccxt_fallback": False,
    })
    monkeypatch.setattr(pe, "is_snapshot_fresh", lambda: (True, None))
    engine = pe.PaperEngine()
    monkeypatch.setattr(engine, "_pre_submit_gate", lambda **kw: (True, None))
    return SimpleNamespace(path=path, reader=reader, pe=pe, engine=engine)


def publish(flow, ticks):
    now = int(datetime.now(timezone.utc).timestamp() * 1000)
    flow.path.write_text(json.dumps({"venues": {"coinbase": {"bid": 999, "ask": 999}},
        "ticks": [{"ts_ms": now, **tick} for tick in ticks]}))


@pytest.mark.parametrize("venue,symbol,want", [
    (" COINBASE ", "btc-usd", 10), ("coinbase", "BTC/USDT", 20),
    ("kraken", "BTC/USD", 30), ("coinbase", "BTC/USDC", None),
    ("coinbasepro", "BTC/USD", None), ("coinbase", "BTCUSD", None),
])
def test_mixed_identity_and_canonical_not_mapped(flow, venue, symbol, want):
    publish(flow, [
        {"venue": "coinbase", "symbol": "BTC/USD", "last": 10},
        {"venue": "coinbase", "symbol": "BTC/USDT", "symbol_mapped": "BTC/USDC", "last": 20},
        {"venue": "kraken", "symbol": "BTC/USD", "last": 30},
    ])
    quote = flow.reader.get_best_bid_ask_last(venue, symbol)
    assert (quote["last"] if quote else None) == want


@pytest.mark.parametrize("mode", ["construction", "fetch", "malformed", "timestamp", "close", "success"])
def test_exchange_missing_snapshot_reaches_mock_and_closes(flow, monkeypatch, mode):
    publish(flow, [{"venue": "coinbase", "symbol": "BTC/USD", "last": 10}])
    calls = []

    class Exchange:
        def fetch_ticker(self, symbol):
            calls.append(("fetch", symbol))
            if mode == "fetch":
                raise RuntimeError("synthetic")
            if mode == "malformed":
                return None
            return {"timestamp": "bad" if mode == "timestamp" else 100, "last": 2}

        def close(self):
            calls.append(("close",))
            if mode == "close":
                raise RuntimeError("synthetic close")

    def make(venue, credentials, **kwargs):
        calls.append(("make", venue))
        assert credentials == {"apiKey": None, "secret": None}
        if mode == "construction":
            raise RuntimeError("synthetic")
        return Exchange()

    monkeypatch.setattr(flow.pe, "make_exchange", make)
    flow.engine.cfg["use_ccxt_fallback"] = True
    quote = flow.engine._price(" COINBASE ", "ADA/USD")
    assert calls[0] == ("make", "coinbase")
    if mode == "construction":
        assert quote is None and len(calls) == 1
    else:
        assert calls[1:] == [("fetch", "ADA/USD"), ("close",)]
        assert (quote["last"] if quote else None) == (2 if mode in {"close", "success"} else None)


def test_missing_symbol_does_not_block_other_order_fill(flow):
    publish(flow, [{"venue": "coinbase", "symbol": "BTC/USD", "bid": 10, "ask": 10}])
    for symbol in ("ADA/USD", "BTC/USD"):
        assert flow.engine.submit_order(client_order_id=symbol, venue="coinbase", symbol=symbol,
            side="buy", order_type="market", qty=1)["ok"]
    assert flow.engine.evaluate_open_orders()["filled"] == 1
    assert [row["order_id"] for row in flow.engine.db.list_fills()] == [
        flow.engine.db.get_order_by_client_id("BTC/USD")["order_id"]]
    assert flow.engine.db.get_order_by_client_id("ADA/USD")["status"] == "new"


@pytest.mark.parametrize("tagged", [False, True])
def test_sell_identity_survives_missing_quote_and_fills_once(flow, tagged):
    publish(flow, [{"venue": "coinbase", "symbol": "BTC/USD", "last": 100}])
    flow.engine.db.upsert_position("ADA/USD", 1, 50, 0)
    meta = {"paper_exit_policy": "retry_until_filled_v1", "paper_exit_id": "r4-exit"} if tagged else {}
    client = "paper_intent_r4-exit" if tagged else "r4-sell"
    result = flow.engine.submit_order(client_order_id=client, venue="coinbase", symbol="ADA/USD",
        side="sell", order_type="limit", limit_price=2, qty=1, meta=meta)
    assert result["ok"], result
    order_id = result["order"]["order_id"]
    assert flow.engine.evaluate_open_orders()["filled"] == 0
    assert flow.engine.db.get_order_by_client_id(client)["status"] == "new"
    publish(flow, [{"venue": "coinbase", "symbol": "ADA/USD", "bid": 2, "ask": 2}])
    assert flow.engine.evaluate_open_orders()["filled"] == 1
    assert flow.engine.evaluate_open_orders()["filled"] == 0
    order = flow.engine.db.get_order_by_client_id(client)
    assert (order["order_id"], order["limit_price"], order["order_type"]) == (order_id, 2, "limit")
    assert len(flow.engine.db.list_fills()) == 1
    assert flow.engine.db.list_fills()[0]["price"] == 2


def test_missing_quote_does_not_bypass_buy_expiry(flow):
    publish(flow, [])
    created = datetime.now(timezone.utc)
    flow.engine._clock = lambda: created.isoformat()
    result = flow.engine.submit_order(client_order_id="r4-old-buy", venue="coinbase", symbol="ADA/USD",
        side="buy", order_type="limit", limit_price=2, qty=1)
    assert result["ok"]
    flow.engine._clock = lambda: (created + timedelta(seconds=180)).isoformat()
    assert flow.engine.evaluate_open_orders()["filled"] == 0
    assert flow.engine.db.get_order_by_client_id("r4-old-buy")["status"] == "expired"
    assert flow.engine.cash_quote() == 1000


def test_missing_quote_mark_to_market_is_not_a_valid_position_valuation(flow):
    publish(flow, [{"venue": "coinbase", "symbol": "BTC/USD", "last": 100}])
    flow.engine.db.upsert_position("ADA/USD", 1, 50, 0)
    result = flow.engine.mark_to_market("coinbase", "ADA/USD")
    assert result["ok"] is True and result["mid"] is None
    assert result["equity_quote"] == result["cash_quote"] == 1000
    assert result["unrealized_pnl"] == 0
    assert flow.engine.db.get_position("ADA/USD")["qty"] == 1
