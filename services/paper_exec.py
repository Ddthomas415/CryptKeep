from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
import uuid
from core.models import Fill, Side
from storage.journal_store_sqlite import JournalStoreSQLite
from core.symbols import normalize_symbol

def bps_to_mult(bps: float) -> float:
    return bps / 10_000.0

@dataclass
class PaperExecConfig:
    venue: str = "paper"
    slippage_bps: float = 5.0
    fee_bps: float = 10.0

class PaperExecutor:
    def __init__(self, journal: JournalStoreSQLite, cfg: PaperExecConfig) -> None:
        self.journal = journal
        self.cfg = cfg

    async def execute_target(self, symbol: str, current_qty: float, target_qty: float, last_price: float) -> Optional[Fill]:
        delta = target_qty - current_qty
        if abs(delta) < 1e-12:
            return None
        side = Side.BUY if delta > 0 else Side.SELL
        qty = abs(delta)
        slip = bps_to_mult(self.cfg.slippage_bps)
        px = last_price * (1.0 + slip) if side == Side.BUY else last_price * (1.0 - slip)
        fee = abs(qty * px) * bps_to_mult(self.cfg.fee_bps)
        fill = Fill(
            venue=self.cfg.venue,
            symbol=normalize_symbol(self.cfg.venue, symbol),
            side=side,
            qty=qty,
            price=px,
            fee=fee,
            client_order_id=f"paper-{uuid.uuid4().hex[:12]}",
            venue_order_id=None,
            fill_id=f"paperfill-{uuid.uuid4().hex[:12]}",
            ts=datetime.now(timezone.utc),
        )
        await self.journal.record_fill(fill)
        return fill
