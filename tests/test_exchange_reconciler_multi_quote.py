from __future__ import annotations

import asyncio

from services.reconciliation.exchange_reconciler import ReconcileConfig, reconcile_once
from storage.portfolio_store_sqlite import SQLitePortfolioStore
from storage.reconciliation_store_sqlite import SQLiteReconciliationStore


class _StubExchange:
    def __init__(self, total: dict[str, float]):
        self._total = total

    async def fetch_balance(self):
        return {"total": dict(self._total)}


def test_reconcile_once_reports_multi_quote_internal_cash_drift(tmp_path):
    portfolio_db = tmp_path / "portfolio.sqlite"
    recon_db = tmp_path / "reconciliation.sqlite"
    runbook_db = tmp_path / "repair_runbooks.sqlite"

    portfolio = SQLitePortfolioStore(path=portfolio_db)
    portfolio.upsert_cash(exchange="coinbase", cash=1000.0, quote_ccy="USD")
    portfolio.upsert_cash_quote(exchange="coinbase", quote_ccy="USDT", cash=2000.0)

    cfg = ReconcileConfig(
        enabled=True,
        interval_sec=30,
        cash_tolerance=5.0,
        asset_qty_tolerance=0.0001,
        recon_db_path=str(recon_db),
        portfolio_db_path=str(portfolio_db),
        runbook_db_path=str(runbook_db),
        auto_draft_runbook_on_critical=False,
        quote_ccys=["usd", "usdt"],
    )
    trading_cfg = {
        "portfolio": {"quote_ccy": "USD"},
        "symbols": ["BTC/USD"],
        "symbol_maps": {"coinbase": {"BTC/USD": "BTC/USD"}},
    }
    ex = _StubExchange({"USD": 1010.0, "USDT": 1980.0, "BTC": 0.0})

    out = asyncio.run(reconcile_once(exchange_id="coinbase", ex_obj=ex, cfg=cfg, trading_cfg=trading_cfg))
    assert out["ok"] is True
    assert out["severity"] == "WARN"

    recon = SQLiteReconciliationStore(path=recon_db)
    rows = recon.list_drift_reports(exchange="coinbase", limit=1)
    assert len(rows) == 1

    payload = rows[0]["payload"]
    primary = payload["cash"]["primary"]
    assert primary["quote_ccy"] == "USD"
    assert primary["exchange_cash"] == 1010.0
    assert primary["internal_cash"] == 1000.0
    assert primary["abs_drift"] == 10.0

    others = payload["cash"]["others"]
    assert len(others) == 1
    assert others[0]["quote_ccy"] == "USDT"
    assert others[0]["exchange_cash"] == 1980.0
    assert others[0]["internal_cash"] == 2000.0
    assert others[0]["abs_drift"] == -20.0


def test_reconcile_once_primary_quote_uses_v2_cash_row_without_legacy(tmp_path):
    portfolio_db = tmp_path / "portfolio.sqlite"
    recon_db = tmp_path / "reconciliation.sqlite"
    runbook_db = tmp_path / "repair_runbooks.sqlite"

    portfolio = SQLitePortfolioStore(path=portfolio_db)
    portfolio.upsert_cash_quote(exchange="coinbase", quote_ccy="USDT", cash=300.0)

    cfg = ReconcileConfig(
        enabled=True,
        interval_sec=30,
        cash_tolerance=5.0,
        asset_qty_tolerance=0.0001,
        recon_db_path=str(recon_db),
        portfolio_db_path=str(portfolio_db),
        runbook_db_path=str(runbook_db),
        auto_draft_runbook_on_critical=False,
        quote_ccys=["USDT", "USD"],
    )
    trading_cfg = {
        "portfolio": {"quote_ccy": "USDT"},
        "symbols": ["BTC/USDT"],
        "symbol_maps": {"coinbase": {"BTC/USDT": "BTC/USDT"}},
    }
    ex = _StubExchange({"USDT": 312.0, "USD": 25.0, "BTC": 0.0})

    out = asyncio.run(reconcile_once(exchange_id="coinbase", ex_obj=ex, cfg=cfg, trading_cfg=trading_cfg))
    assert out["ok"] is True
    assert out["severity"] == "WARN"

    recon = SQLiteReconciliationStore(path=recon_db)
    rows = recon.list_drift_reports(exchange="coinbase", limit=1)
    assert len(rows) == 1

    primary = rows[0]["payload"]["cash"]["primary"]
    assert primary["quote_ccy"] == "USDT"
    assert primary["internal_cash"] == 300.0
    assert primary["exchange_cash"] == 312.0
    assert primary["abs_drift"] == 12.0
