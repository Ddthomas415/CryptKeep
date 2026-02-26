from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore

from core.price_aggregator import AggregationConfig, aggregate_prices
from core.risk_manager import RiskConfig, RiskState, allow_order
from services.os.app_paths import data_dir, ensure_dirs
from services.strategy_runner.strategies.ema_crossover import EMACfg, EMAState, update_ema_state, compute_signal

from storage.journal_store_sqlite import SQLiteJournalStore
from storage.market_data_store_sqlite import SQLiteMarketDataStore
from services.paper_trader.paper_execution_venue import PaperExecutionVenue
from services.market_data.run_price_feeds import main_async as run_feeds_async
from core.models import Order, OrderType, Side, TimeInForce, utc_now


def _utc_day_key(dt: Optional[datetime] = None) -> str:
    dt = dt or datetime.now(timezone.utc)
    return dt.strftime("%Y-%m-%d")


def load_cfg(path: Path) -> Dict[str, Any]:
    d = yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
    if not isinstance(d, dict):
        raise ValueError("trading.yaml must be a mapping")
    return d


def load_state(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace")) or {}
    except Exception:
        return {}


def save_state(path: Path, d: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(d, indent=2, sort_keys=True), encoding="utf-8")


async def runner(cfg_path: Path) -> int:
    cfg = load_cfg(cfg_path)
    ensure_dirs()

    mode = str(cfg.get("mode") or "paper").strip().lower()
    if mode != "paper":
        raise ValueError("Phase 321 runner supports PAPER mode only (live later).")

    run_id = str(cfg.get("run_id") or "paper_run")

    paths = cfg.get("paths") or {}
    droot = data_dir()
    journal_db = Path((paths.get("journal_db") or str(droot / "paper_journal.sqlite")))
    market_db = Path((paths.get("market_db") or str(droot / "market_data.sqlite")))
    state_file = Path((paths.get("state_file") or str(droot / "runner_state.json")))
    kill_file = Path((paths.get("kill_switch_file") or str(droot / "KILL_SWITCH.flag")))

    tick_interval = float((cfg.get("runner") or {}).get("tick_interval_sec") or 2.0)

    # Risk config/state
    rcfg_d = cfg.get("risk") or {}
    rcfg = RiskConfig(
        max_trades_per_day=int(rcfg_d.get("max_trades_per_day") or 10),
        max_position_notional=float(rcfg_d.get("max_position_notional") or 2000.0),
        max_drawdown_frac=float(rcfg_d.get("max_drawdown_frac") or 0.10),
        min_cash=float(rcfg_d.get("min_cash") or 0.0),
    )

    st = load_state(state_file)
    day_key = _utc_day_key()
    if st.get("day_key") != day_key:
        st = {"day_key": day_key, "trades_today": 0, "peak_equity_today": 0.0, "seq": 0}
        save_state(state_file, st)

    risk_state = RiskState(
        day_key=st.get("day_key", day_key),
        trades_today=int(st.get("trades_today") or 0),
        peak_equity_today=float(st.get("peak_equity_today") or 0.0),
    )
    seq = int(st.get("seq") or 0)

    # Aggregation config
    aggd = cfg.get("aggregation") or {}
    agg_cfg = AggregationConfig(
        mode=str(aggd.get("mode") or "median"),
        stale_seconds=int(aggd.get("stale_seconds") or 10),
        primary_exchange_by_symbol=dict(aggd.get("primary_exchange_by_symbol") or {}) if isinstance(aggd.get("primary_exchange_by_symbol") or {}, dict) else None,
    )

    symbols = [str(s) for s in (cfg.get("symbols") or [])]
    if not symbols:
        raise ValueError("trading.yaml symbols must be non-empty")

    # Strategy
    strat = cfg.get("strategy") or {}
    if str(strat.get("type") or "") != "ema_crossover":
        raise ValueError("Phase 321 supports strategy.type=ema_crossover only.")

    ema_d = (strat.get("ema") or {})
    ecfg = EMACfg(
        fast=int(ema_d.get("fast") or 12),
        slow=int(ema_d.get("slow") or 26),
        min_history=int(ema_d.get("min_history") or 30),
        trade_qty=float(ema_d.get("trade_qty") or 0.01),
    )

    # Stores
    journal = SQLiteJournalStore(path=journal_db, initial_cash=10_000.0)
    md_store = SQLiteMarketDataStore(path=market_db)

    # PAPER execution
    venue = PaperExecutionVenue(venue="paper", fee_bps=1.0, slippage_bps=0.0)
    await venue.connect()

    async def fill_consumer():
        async for fill in venue.fills():
            await journal.record_fill(fill)

    fill_task = asyncio.create_task(fill_consumer())

    # Optional: start CCXT feeders inside runner (safe; no keys; market data only)
    md_cfg = cfg.get("market_data") or {}
    auto_start = bool(md_cfg.get("auto_start_feeds", True))
    feeder_task: Optional[asyncio.Task] = None
    if auto_start:
        feeder_cfg_path = Path(str(md_cfg.get("config_path") or "config/market_data.yaml"))
        feeder_task = asyncio.create_task(run_feeds_async(feeder_cfg_path))
        # give it a moment to start
        await asyncio.sleep(0.5)

    # EMA state per symbol
    ema_state: Dict[str, EMAState] = {s: EMAState() for s in symbols}
    seen_ticks: Dict[str, int] = {s: 0 for s in symbols}

    print("[runner] started", {"mode": mode, "run_id": run_id, "symbols": symbols, "tick_interval": tick_interval})
    try:
        while True:
            if kill_file.exists():
                print("[runner] KILL SWITCH file present -> stopping:", str(kill_file))
                break

            # reset daily counters if day flips
            dk = _utc_day_key()
            if dk != risk_state.day_key:
                risk_state.day_key = dk
                risk_state.trades_today = 0
                risk_state.peak_equity_today = 0.0
                seq = 0

            md_rows = md_store.get_latest_sync()
            prices, _ = aggregate_prices(md_rows, agg_cfg)

            # Portfolio MTM using aggregated prices
            portfolio = journal.load_portfolio_sync(latest_prices=prices)
            if portfolio.equity > risk_state.peak_equity_today:
                risk_state.peak_equity_today = float(portfolio.equity)

            # Per-symbol decision
            for sym in symbols:
                px = prices.get(sym)
                if px is None:
                    continue

                # set paper venue price per symbol
                venue.set_price_for(sym, float(px))

                seen_ticks[sym] += 1
                ema_state[sym] = update_ema_state(float(px), ecfg, ema_state[sym])

                # require warmup
                if seen_ticks[sym] < ecfg.min_history:
                    continue

                sig = compute_signal(ema_state[sym])
                # Only act on signal changes (reduces churn)
                if sig == ema_state[sym].last_signal:
                    continue

                ema_state[sym].last_signal = sig

                if sig == 0:
                    continue

                side = Side.BUY if sig > 0 else Side.SELL
                seq += 1

                # Deterministic client_order_id => idempotent on restart
                client_order_id = f"{run_id}:{sym}:{'BUY' if sig>0 else 'SELL'}:{risk_state.day_key}:{seq}"

                order = Order(
                    client_order_id=client_order_id,
                    venue="paper",
                    symbol=sym,
                    side=side,
                    qty=float(ecfg.trade_qty),
                    order_type=OrderType.MARKET,
                    limit_price=None,
                    tif=TimeInForce.IOC,
                    reduce_only=False,
                    post_only=False,
                    ts=utc_now(),
                )

                allowed, reason = allow_order(order, portfolio, prices, rcfg, risk_state)
                if not allowed:
                    print("[risk] blocked", {"order": client_order_id, "reason": reason})
                    continue

                ack = await venue.place_order(order)
                await journal.record_order_ack(ack)
                risk_state.trades_today += 1
                print("[trade] placed", {"id": client_order_id, "side": str(side), "sym": sym, "px": px, "reason": reason})

            # Persist runner state
            save_state(state_file, {
                "day_key": risk_state.day_key,
                "trades_today": risk_state.trades_today,
                "peak_equity_today": risk_state.peak_equity_today,
                "seq": seq,
            })

            await asyncio.sleep(max(0.25, tick_interval))

    finally:
        try:
            await venue.close()
        except Exception:
            pass
        try:
            await asyncio.sleep(0.1)
        except Exception:
            pass
        try:
            fill_task.cancel()
        except Exception:
            pass
        if feeder_task:
            feeder_task.cancel()

    print("[runner] stopped")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="config/trading.yaml")
    args = ap.parse_args()
    return asyncio.run(runner(Path(args.config)))


if __name__ == "__main__":
    raise SystemExit(main())
