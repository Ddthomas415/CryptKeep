from __future__ import annotations
import asyncio
import logging
import os
from pathlib import Path
from typing import Optional
import orjson
import sqlite3
from core.event_factory import event_from_dict
from core.events import TradeEvent
from core.symbols import normalize_symbol
from services.strategy_ema import EMACrossStrategy
from services.risk_engine import RiskConfig, RiskEngine
from services.paper_exec import PaperExecConfig, PaperExecutor
from storage.journal_store_sqlite import JournalStoreSQLite

def _setup_logging() -> None:
    level = os.environ.get("CBP_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, level, logging.INFO),
        format="%(asctime)sZ %(levelname)s %(name)s: %(message)s",
    )

def _get_position_qty(journal_path: Path, venue: str, symbol_norm: str) -> float:
    if not journal_path.exists():
        return 0.0
    conn = sqlite3.connect(journal_path)
    row = conn.execute(
        "SELECT qty FROM positions WHERE venue=? AND symbol_norm=?",
        (venue, symbol_norm),
    ).fetchone()
    conn.close()
    return float(row[0]) if row else 0.0

async def main() -> None:
    _setup_logging()
    log = logging.getLogger("paper_trader")
    events_db = Path("data") / "events.sqlite"
    journal_db = Path("data") / "journal.sqlite"
    if not events_db.exists():
        raise RuntimeError("events DB missing. Run collector first.")
    symbol = os.environ.get("CBP_TRADE_SYMBOL", "BTC-USDT")
    src_venue = os.environ.get("CBP_SOURCE_VENUE", "gateio")  # fallback to gateio
    paper_venue = os.environ.get("CBP_PAPER_VENUE", "paper")
    fast = int(os.environ.get("CBP_EMA_FAST", "5"))
    slow = int(os.environ.get("CBP_EMA_SLOW", "10"))
    target_qty = float(os.environ.get("CBP_TARGET_QTY", "0.001"))
    max_abs_qty = float(os.environ.get("CBP_MAX_ABS_QTY", "0.01"))
    max_trades_day = int(os.environ.get("CBP_MAX_TRADES_DAY", "50"))
    slippage_bps = float(os.environ.get("CBP_SLIPPAGE_BPS", "5"))
    fee_bps = float(os.environ.get("CBP_FEE_BPS", "10"))
    symn = normalize_symbol(src_venue, symbol)
    log.info("paper_trader start symbol=%s source_venue=%s paper_venue=%s", symn, src_venue, paper_venue)
    journal = JournalStoreSQLite(journal_db)
    strat = EMACrossStrategy(venue=paper_venue, symbol=symn, target_qty=target_qty, fast_period=fast, slow_period=slow)
    risk = RiskEngine(RiskConfig(max_abs_qty=max_abs_qty, max_trades_per_day=max_trades_day))
    execu = PaperExecutor(journal, PaperExecConfig(venue=paper_venue, slippage_bps=slippage_bps, fee_bps=fee_bps))
    last_id = 0
    last_price: Optional[float] = None
    poll_sec = 0.25
    while True:
        await asyncio.sleep(poll_sec)
        conn = sqlite3.connect(events_db)
        cur = conn.execute(
            "SELECT id, payload FROM events WHERE id > ? AND event_type='trade' ORDER BY id ASC LIMIT 500",
            (last_id,),
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            continue
        for rid, blob in rows:
            last_id = rid
            try:
                d = orjson.loads(blob)
                e = event_from_dict(d)
            except Exception:
                continue
            if not isinstance(e, TradeEvent):
                continue
            if str(e.venue).lower() != str(src_venue).lower():
                continue
            esym = normalize_symbol(e.venue, e.symbol)
            if esym != symn:
                continue
            last_price = float(e.price)
            intent = strat.on_price(last_price)
            if intent is None:
                continue
            cur_qty = _get_position_qty(journal_db, paper_venue, symn)
            ps = await journal.load_portfolio()
            decision = risk.allow_intent(intent, ps, last_price)
            if not decision.allowed:
                log.warning("risk_blocked reason=%s intent_target=%s", decision.reason, intent.target_qty)
                continue
            fill = await execu.execute_target(symn, cur_qty, intent.target_qty, last_price)
            if fill:
                risk.record_trade()
                log.info(
                    "paper_fill side=%s qty=%.6f px=%.2f fee=%.6f target=%.6f cur=%.6f",
                    fill.side.value, fill.qty, fill.price, fill.fee, intent.target_qty, cur_qty
                )

if __name__ == "__main__":
    asyncio.run(main())
