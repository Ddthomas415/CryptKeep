from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from services.os.app_paths import data_dir, ensure_dirs
from storage.portfolio_store_sqlite import SQLitePortfolioStore

ensure_dirs()
DEFAULT_DB = data_dir() / "portfolio.sqlite"


class PortfolioStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_DB
        self.db = SQLitePortfolioStore(self.path)

    def set_cash(self, *, exchange: str, cash: float) -> None:
        self.db.upsert_cash(exchange=str(exchange), cash=float(cash))

    def get_cash(self, *, exchange: str) -> Dict[str, Any] | None:
        return self.db.get_cash(str(exchange))

    def set_position(self, *, exchange: str, symbol: str, qty: float) -> None:
        self.db.upsert_position(exchange=str(exchange), symbol=str(symbol), qty=float(qty))

    def list_positions(self, *, exchange: str | None = None) -> List[Dict[str, Any]]:
        return self.db.list_positions(exchange=str(exchange) if exchange else None)

    def snapshot(self, *, exchange: str | None = None) -> Dict[str, Any]:
        positions = self.list_positions(exchange=exchange)
        cash = self.get_cash(exchange=str(exchange)) if exchange else None
        return {"ok": True, "exchange": exchange, "cash": cash, "positions": positions}
