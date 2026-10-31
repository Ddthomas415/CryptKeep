"""Probe (not part of the repository): paper engine accounting with fixed quotes, checked by hand arithmetic."""
import importlib, math

def _engine(monkeypatch, tmp_path, quotes):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as ap; importlib.reload(ap)
    import services.admin.config_editor as ce; importlib.reload(ce)
    import storage.paper_trading_sqlite as pts; importlib.reload(pts)
    import services.execution.paper_engine as pe; importlib.reload(pe)
    monkeypatch.setattr(pe, "_cfg", lambda: {"enabled": True, "quote_currency": "USD", "starting_cash_quote": 1000.0,
        "fee_bps": 50.0, "slippage_bps": 0.0, "use_ccxt_fallback": False, "max_order_qty": 1e9, "strategy_id": "probe"})
    # gates are bypassed here only to test accounting; the gates themselves are a separate finding
    monkeypatch.setattr(pe, "is_snapshot_fresh", lambda *a, **k: (True, "probe"))
    monkeypatch.setattr(pe, "is_master_read_only", lambda *a, **k: (False, "probe"))
    monkeypatch.setattr(pe, "check_market_quality", lambda venue, symbol: {"ok": True, "price_used": quotes[0]["last"], "last": quotes[0]["last"]})
    monkeypatch.setattr(pe, "should_allow_order", lambda *a, **k: (True, "probe"))
    eng = pe.PaperEngine()
    monkeypatch.setattr(eng, "_price", lambda venue, symbol: dict(quotes[0]))
    return pe, eng

def test_round_trip(monkeypatch, tmp_path):
    quotes = [{"ts_ms": 1, "bid": 99.0, "ask": 101.0, "last": 100.0}]
    pe, eng = _engine(monkeypatch, tmp_path, quotes)
    r = eng.submit_order(venue="coinbase", symbol="BTC/USD", side="buy", order_type="market", qty=5.0, client_order_id="probe-1")
    print("\nsubmit:", {k: r.get(k) for k in ("ok", "reason", "status")})
    print("evaluate buy:", {k: v for k, v in eng.evaluate_open_orders().items() if k != "details_sample"})
    pos = eng.db.get_position("BTC/USD"); cash = eng.cash_quote()
    # hand: fill at mid 100 (no slippage), fee 0.5% of 500 = 2.5, cash 1000-502.5=497.5, avg = 502.5/5 = 100.5
    print("after buy: qty", pos["qty"], "avg", round(pos["avg_price"], 6), "cash", round(cash, 6), "| expected qty 5 avg 100.5 cash 497.5; at the ask it would be avg 101.505")
    quotes[0] = {"ts_ms": 2, "bid": 109.0, "ask": 111.0, "last": 110.0}
    eng.submit_order(venue="coinbase", symbol="BTC/USD", side="sell", order_type="market", qty=5.0, client_order_id="probe-2")
    eng.evaluate_open_orders()
    pos = eng.db.get_position("BTC/USD"); cash = eng.cash_quote()
    # hand: fill at mid 110, proceeds 550 - fee 2.75 = 547.25; realized = 547.25 - 502.5 = 44.75; cash 1044.75
    print("after sell: qty", pos["qty"], "realized", round(pos["realized_pnl"], 6), "cash", round(cash, 6), "| expected realized 44.75 cash 1044.75; at the bid it would be 39.27")

def test_rejections(monkeypatch, tmp_path):
    quotes = [{"ts_ms": 1, "bid": 99.0, "ask": 101.0, "last": 100.0}]
    pe, eng = _engine(monkeypatch, tmp_path, quotes)
    eng.submit_order(venue="coinbase", symbol="ETH/USD", side="sell", order_type="market", qty=1.0, client_order_id="probe-3")
    eng.submit_order(venue="coinbase", symbol="ETH/USD", side="buy", order_type="market", qty=20.0, client_order_id="probe-4")
    out = eng.evaluate_open_orders()
    print("\nrejections:", [(o["side"], o["status"], o.get("reject_reason")) for o in eng.db.list_orders(limit=10)])
