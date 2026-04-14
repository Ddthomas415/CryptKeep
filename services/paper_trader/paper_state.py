from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from storage.paper_trading_sqlite import PaperTradingSQLite


class PaperState:
    def __init__(self, db_path: str | Path | None = None) -> None:
        # storage.paper_trading_sqlite currently uses a fixed app-path DB.
        # Keep optional db_path parameter for compatibility but ignore it.
        self.db = PaperTradingSQLite()

    def get_cash_quote(self, default: float = 0.0) -> float:
        v = self.db.get_state("cash_quote")
        try:
            return float(v) if v is not None else float(default)
        except Exception:
            return float(default)

    def set_cash_quote(self, value: float) -> None:
        self.db.set_state("cash_quote", str(float(value)))

    def get_realized_pnl(self, default: float = 0.0) -> float:
        v = self.db.get_state("realized_pnl")
        try:
            return float(v) if v is not None else float(default)
        except Exception:
            return float(default)

    def set_realized_pnl(self, value: float) -> None:
        self.db.set_state("realized_pnl", str(float(value)))

    def positions(self, *, limit: int = 200) -> List[Dict[str, Any]]:
        return self.db.list_positions(limit=int(limit))

    def position(self, symbol: str) -> Dict[str, Any] | None:
        return self.db.get_position(str(symbol))

    def snapshot(self, *, limit: int = 100) -> Dict[str, Any]:
        return {
            "ok": True,
            "cash_quote": self.get_cash_quote(),
            "realized_pnl": self.get_realized_pnl(),
            "positions": self.positions(limit=limit),
            "orders": self.db.list_orders(limit=int(limit)),
            "fills": self.db.list_fills(limit=int(limit)),
        }
