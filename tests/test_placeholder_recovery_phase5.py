from __future__ import annotations

import importlib


def _reload_state_modules(monkeypatch, tmp_path):
    monkeypatch.setenv("CBP_STATE_DIR", str(tmp_path))
    import services.os.app_paths as app_paths

    importlib.reload(app_paths)
    return app_paths


def test_retry_sync_and_async():
    from services.net.retry import retry, retry_async
    import asyncio

    n = {"count": 0}

    def flaky():
        n["count"] += 1
        if n["count"] < 3:
            raise RuntimeError("x")
        return 42

    assert retry(flaky, retries=4, base_delay_sec=0.0) == 42

    m = {"count": 0}

    async def aflake():
        m["count"] += 1
        if m["count"] < 2:
            raise RuntimeError("y")
        return "ok"

    assert asyncio.run(retry_async(aflake, retries=3, base_delay_sec=0.0)) == "ok"


def test_connectivity_wrappers(monkeypatch):
    import services.admin.connectivity as connectivity

    monkeypatch.setattr(connectivity, "test_private_connectivity", lambda ex: {"ok": ex == "coinbase"})
    monkeypatch.setattr(connectivity, "run_probes", lambda ex, keys: {"ok": True, "results": []})

    one = connectivity.check_exchange_connectivity("coinbase")
    assert one["ok"] is True
    many = connectivity.check_many_connectivity(["coinbase", "gateio"])
    assert many["ok"] is False
    assert many["count"] == 2


def test_build_runner_contract(monkeypatch):
    import services.admin.build_runner as build_runner

    class Dummy:
        ok = True
        code = 0
        cmd = ["x"]
        out = "ok"
        err = ""

    monkeypatch.setitem(build_runner.TARGETS, "dummy", lambda: Dummy())
    out = build_runner.run_build_target("dummy")
    assert out["ok"] is True
    assert build_runner.run_build_target("missing")["ok"] is False


def test_email_notifier_dry_run(monkeypatch):
    import services.alerts.email_notifier as email_notifier

    monkeypatch.setenv("CBP_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("CBP_SMTP_FROM", "bot@example.com")
    out = email_notifier.send_email(to=["u@example.com"], subject="s", body="b", dry_run=True)
    assert out["ok"] is True
    assert out["dry_run"] is True


def test_first_run_checks(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    import services.onboarding.first_run_checks as first_run_checks

    importlib.reload(first_run_checks)
    out = first_run_checks.run_first_run_checks()
    assert out["config_exists"] is True
    assert "kill_switch" in out


def test_portfolio_and_fill_event_store(monkeypatch, tmp_path):
    _reload_state_modules(monkeypatch, tmp_path)
    from services.portfolio.portfolio_store import PortfolioStore
    from services.portfolio.fill_event_store import FillEventStore
    from storage.trade_history_sqlite import TradeHistorySQLite

    ps = PortfolioStore(path=tmp_path / "portfolio.sqlite")
    ps.set_cash(exchange="paper", cash=1000.0)
    ps.set_position(exchange="paper", symbol="BTC/USD", qty=0.5)
    snap = ps.snapshot(exchange="paper")
    assert snap["cash"]["cash"] == 1000.0
    assert snap["positions"][0]["symbol"] == "BTC/USD"

    fe = FillEventStore(store=TradeHistorySQLite(path=tmp_path / "trade_history.sqlite"))
    fe.record_fill({"trade_id": "fill-1", "venue": "paper", "symbol": "BTC/USD", "side": "buy", "qty": 1.0, "price": 100.0})
    rows = fe.recent(limit=5)
    assert rows and rows[0]["trade_id"] == "fill-1"


def test_ccxt_private_factory_and_feature_store(monkeypatch, tmp_path):
    import services.execution.ccxt_private_factory as ccxt_private_factory
    from services.learning.feature_store import FeatureStore

    monkeypatch.setattr(ccxt_private_factory, "load_exchange_credentials", lambda ex: {"apiKey": "k", "secret": "s"})
    monkeypatch.setattr(ccxt_private_factory, "make_exchange", lambda ex, creds, enable_rate_limit=True: {"exchange": ex, "creds": creds})
    ex = ccxt_private_factory.make_private_exchange("coinbase")
    assert ex["exchange"] == "coinbase"

    fs = FeatureStore(path=tmp_path / "feature_store.sqlite")
    out = fs.add_context(row_id="r1", context={"telemetry": {"pnl_usd": 1.5}}, symbol="BTC/USD", side="buy", label=1)
    assert out["ok"] is True
    rows = fs.recent(limit=5)
    assert rows and rows[0]["row_id"] == "r1"


def test_ws_clients_status():
    from services.market_data.ws_clients import build_status

    row = build_status(exchange="coinbase", symbol="BTC/USD", connected=True, recv_ts_ms=1000, now_ts_ms=1110)
    assert row["lag_ms"] == 110.0
    assert row["connected"] is True
