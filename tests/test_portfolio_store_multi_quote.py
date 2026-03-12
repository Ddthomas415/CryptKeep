from __future__ import annotations

from storage.portfolio_store_sqlite import SQLitePortfolioStore


def test_sqlite_portfolio_store_multi_quote_cash_ledger_v2(tmp_path):
    store = SQLitePortfolioStore(path=tmp_path / "portfolio.sqlite")

    store.upsert_cash(exchange="coinbase", cash=1000.0)
    store.upsert_cash_quote(exchange="coinbase", quote_ccy="usdt", cash=250.5)

    usd = store.get_cash("coinbase", "USD")
    usdt = store.get_cash("coinbase", "USDT")
    quotes = store.list_cash_quotes(exchange="coinbase")

    assert usd is not None
    assert usd["quote_ccy"] == "USD"
    assert usd["cash"] == 1000.0

    assert usdt is not None
    assert usdt["quote_ccy"] == "USDT"
    assert usdt["cash"] == 250.5

    assert [r["quote_ccy"] for r in quotes] == ["USD", "USDT"]


def test_sqlite_portfolio_store_get_cash_fallback_prefers_usd(tmp_path):
    store = SQLitePortfolioStore(path=tmp_path / "portfolio.sqlite")

    # No legacy row: fallback should use v2 rows and prefer USD if present.
    store.upsert_cash_quote(exchange="coinbase", quote_ccy="USDT", cash=800.0)
    store.upsert_cash_quote(exchange="coinbase", quote_ccy="USD", cash=1200.0)

    row = store.get_cash("coinbase")
    assert row is not None
    assert row["quote_ccy"] == "USD"
    assert row["cash"] == 1200.0
