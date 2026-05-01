"""
storage/live_position_store_sqlite.py

Live spot position and realized-PnL tracker.

Purpose:
- Compute realized PnL locally for spot fills when the exchange does not provide
  realized_pnl_usd, especially Coinbase spot.
- Maintain weighted-average cost basis per (venue, symbol).
- Be idempotent by (venue, fill_id).

Safety rules:
- Duplicate fills are ignored.
- Sell without known position fails closed.
- Oversell fails closed.
- Unknown side fails closed.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class LivePositionAccountingError(RuntimeError):
    """Raised when live position accounting cannot safely apply a fill."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(path: str) -> sqlite3.Connection:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path, timeout=30)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL;")
    con.execute("PRAGMA synchronous=NORMAL;")
    con.execute("""
        CREATE TABLE IF NOT EXISTS live_positions (
            venue       TEXT NOT NULL,
            symbol      TEXT NOT NULL,
            qty         REAL NOT NULL DEFAULT 0.0,
            avg_price   REAL NOT NULL DEFAULT 0.0,
            updated_ts  TEXT NOT NULL,
            PRIMARY KEY (venue, symbol)
        )
    """)
    con.execute("""
        CREATE TABLE IF NOT EXISTS live_position_fills (
            venue        TEXT NOT NULL,
            fill_id      TEXT NOT NULL,
            symbol       TEXT NOT NULL,
            side         TEXT NOT NULL,
            qty          REAL NOT NULL,
            price        REAL NOT NULL,
            realized_pnl REAL NOT NULL DEFAULT 0.0,
            created_ts   TEXT NOT NULL,
            PRIMARY KEY (venue, fill_id)
        )
    """)
    con.execute("""
        CREATE INDEX IF NOT EXISTS idx_lpf_venue_symbol
        ON live_position_fills(venue, symbol, created_ts)
    """)
    return con


class LivePositionStore:
    """
    Position tracker for live spot fills.

    Accounting model:
    - Buy: weighted-average cost basis
    - Sell: realized_pnl = (sell_price - avg_price) * sell_qty
    """

    def __init__(self, exec_db: str) -> None:
        self.path = str(exec_db)
        con = _connect(self.path)
        con.close()

    def get_position(self, venue: str, symbol: str) -> dict[str, Any]:
        con = _connect(self.path)
        try:
            row = con.execute(
                "SELECT qty, avg_price FROM live_positions WHERE venue=? AND symbol=?",
                (str(venue), str(symbol)),
            ).fetchone()
            if not row:
                return {"qty": 0.0, "avg_price": 0.0}
            return {
                "qty": float(row["qty"]),
                "avg_price": float(row["avg_price"]),
            }
        finally:
            con.close()

    def reconcile_to_exchange(
        self,
        *,
        venue: str,
        symbol: str,
        exchange_qty: float,
        tolerance: float = 1e-9,
    ) -> dict[str, Any]:
        """
        Compare local position quantity to exchange quantity.

        This does not mutate state. It gives callers a safe hook to halt or
        repair if local accounting drifts from exchange truth.
        """
        pos = self.get_position(venue, symbol)
        local_qty = float(pos["qty"])
        exchange_qty_f = float(exchange_qty)
        drift = exchange_qty_f - local_qty

        return {
            "ok": abs(drift) <= float(tolerance),
            "venue": str(venue),
            "symbol": str(symbol),
            "local_qty": local_qty,
            "exchange_qty": exchange_qty_f,
            "drift": drift,
            "tolerance": float(tolerance),
        }

    def apply_fill(
        self,
        *,
        venue: str,
        symbol: str,
        fill_id: str,
        side: str,
        qty: float,
        price: float,
    ) -> dict[str, Any]:
        """
        Apply one fill exactly once.

        Returns:
            {
                "ok": bool,
                "idempotent": bool,
                "realized_pnl_usd": float,
                "new_qty": float,
                "new_avg_price": float,
                "reason": str | None,
            }

        Raises:
            LivePositionAccountingError on unsafe accounting conditions.
        """
        venue_s = str(venue)
        symbol_s = str(symbol)
        fill_id_s = str(fill_id)
        side_s = str(side).strip().lower()
        qty_f = float(qty)
        price_f = float(price)

        if not venue_s or not symbol_s or not fill_id_s:
            raise LivePositionAccountingError("missing_required_identity")
        if qty_f <= 0.0:
            raise LivePositionAccountingError(f"invalid_qty:{qty_f}")
        if price_f <= 0.0:
            raise LivePositionAccountingError(f"invalid_price:{price_f}")
        if side_s not in ("buy", "sell"):
            raise LivePositionAccountingError(f"unknown_side:{side_s}")

        con = _connect(self.path)
        try:
            con.execute("BEGIN IMMEDIATE")

            existing = con.execute(
                """
                SELECT realized_pnl
                FROM live_position_fills
                WHERE venue=? AND fill_id=?
                """,
                (venue_s, fill_id_s),
            ).fetchone()

            if existing:
                con.execute("ROLLBACK")
                return {
                    "ok": True,
                    "idempotent": True,
                    "realized_pnl_usd": float(existing["realized_pnl"]),
                    "new_qty": self.get_position(venue_s, symbol_s)["qty"],
                    "new_avg_price": self.get_position(venue_s, symbol_s)["avg_price"],
                    "reason": "duplicate_fill",
                }

            row = con.execute(
                "SELECT qty, avg_price FROM live_positions WHERE venue=? AND symbol=?",
                (venue_s, symbol_s),
            ).fetchone()

            old_qty = float(row["qty"]) if row else 0.0
            old_avg = float(row["avg_price"]) if row else 0.0

            if side_s == "buy":
                new_qty = old_qty + qty_f
                new_avg = ((old_qty * old_avg) + (qty_f * price_f)) / new_qty
                realized = 0.0

            else:
                if old_qty <= 0.0:
                    raise LivePositionAccountingError(
                        f"sell_without_position venue={venue_s} symbol={symbol_s} fill_id={fill_id_s}"
                    )
                if qty_f > old_qty + 1e-12:
                    raise LivePositionAccountingError(
                        f"sell_exceeds_position venue={venue_s} symbol={symbol_s} "
                        f"fill_id={fill_id_s} sell_qty={qty_f} position_qty={old_qty}"
                    )

                realized = (price_f - old_avg) * qty_f
                new_qty = old_qty - qty_f
                new_avg = old_avg if new_qty > 1e-12 else 0.0
                if new_qty <= 1e-12:
                    new_qty = 0.0

            now = _now()

            con.execute(
                """
                INSERT INTO live_positions (venue, symbol, qty, avg_price, updated_ts)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(venue, symbol) DO UPDATE SET
                    qty = excluded.qty,
                    avg_price = excluded.avg_price,
                    updated_ts = excluded.updated_ts
                """,
                (venue_s, symbol_s, float(new_qty), float(new_avg), now),
            )

            con.execute(
                """
                INSERT INTO live_position_fills
                    (venue, fill_id, symbol, side, qty, price, realized_pnl, created_ts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    venue_s,
                    fill_id_s,
                    symbol_s,
                    side_s,
                    float(qty_f),
                    float(price_f),
                    float(realized),
                    now,
                ),
            )

            con.execute("COMMIT")

            return {
                "ok": True,
                "idempotent": False,
                "realized_pnl_usd": float(realized),
                "new_qty": float(new_qty),
                "new_avg_price": float(new_avg),
                "reason": None,
            }

        except Exception:
            try:
                con.execute("ROLLBACK")
            except Exception:
                pass
            raise
        finally:
            con.close()
