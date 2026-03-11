from __future__ import annotations

import asyncio
import importlib

from core.models import Fill, Order, OrderType, Side, TimeInForce
from storage.journal_store_sqlite import SQLiteJournalStore


def test_run_trader_module_imports():
    mod = importlib.import_module("services.trading_runner.run_trader")
    assert mod is not None


def test_price_aggregator_median_and_primary():
    from core.price_aggregator import AggregationConfig, aggregate_prices

    rows = [
        {"venue": "coinbase", "symbol": "BTC/USD", "bid": 99.0, "ask": 101.0, "ts_ms": 1000},
        {"venue": "kraken", "symbol": "BTC/USD", "last": 105.0, "ts_ms": 1000},
    ]

    prices, detail = aggregate_prices(rows, AggregationConfig(mode="median", stale_seconds=0))
    assert prices["BTC/USD"] == 102.5
    assert detail["sources"]["BTC/USD"]["count"] == 2

    prices2, detail2 = aggregate_prices(
        rows,
        AggregationConfig(mode="median", stale_seconds=0, primary_exchange_by_symbol={"BTC/USD": "coinbase"}),
    )
    assert prices2["BTC/USD"] == 100.0
    assert detail2["sources"]["BTC/USD"]["mode"] == "primary"


def test_sqlite_journal_store_load_portfolio_sync(tmp_path):
    journal = SQLiteJournalStore(path=tmp_path / "journal.sqlite", initial_cash=1000.0)
    asyncio.run(
        journal.record_fill(
            Fill(
                venue="paper",
                symbol="BTC/USD",
                side=Side.BUY,
                qty=2.0,
                price=100.0,
                fee=1.0,
                client_order_id="cid-1",
                venue_order_id="oid-1",
                fill_id="fill-1",
            )
        )
    )

    portfolio = journal.load_portfolio_sync(latest_prices={"BTC/USD": 120.0})

    assert portfolio.cash == 799.0
    assert portfolio.equity == 1039.0
    assert len(portfolio.positions) == 1
    pos = next(iter(portfolio.positions.values()))
    assert pos.unrealized_pnl == 40.0


def test_paper_execution_venue_emits_fill():
    from services.paper_trader.paper_execution_venue import PaperExecutionVenue

    async def scenario():
        venue = PaperExecutionVenue(venue="paper", fee_bps=10.0, slippage_bps=0.0)
        await venue.connect()
        venue.set_price_for("BTC/USD", 100.0)
        order = Order(
            venue="paper",
            symbol="BTC/USD",
            side=Side.BUY,
            order_type=OrderType.MARKET,
            qty=1.5,
            client_order_id="cid-1",
            tif=TimeInForce.IOC,
        )
        ack = await venue.place_order(order)
        fills = venue.fills()
        fill = await fills.__anext__()
        await venue.close()
        return ack, fill

    ack, fill = asyncio.run(scenario())

    assert ack.status.value == "filled"
    assert fill.price == 100.0
    assert fill.qty == 1.5
