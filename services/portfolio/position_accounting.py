from __future__ import annotations

from typing import Any


def _norm_ccy(value: str | None) -> str:
    return str(value or "").strip().upper()


class PositionAccounting:
    def __init__(self, db_path=None):
        self.db_path = db_path
        self._positions: dict[str, dict[str, float | str]] = {}
        self._cash: dict[str, float] = {}
        self._realized: float = 0.0

    def apply_fill(self, fill: dict):
        side = str(fill.get("side", "")).upper()
        symbol = str(fill.get("symbol", ""))
        qty = float(fill.get("qty", 0.0) or 0.0)
        price = float(fill.get("price", 0.0) or 0.0)

        if not symbol or "/" not in symbol:
            raise ValueError("fill.symbol must be like BASE/QUOTE")
        if side not in {"BUY", "SELL"}:
            raise ValueError("fill.side must be BUY or SELL")
        if qty <= 0.0:
            raise ValueError("fill.qty must be > 0")
        if price < 0.0:
            raise ValueError("fill.price must be >= 0")

        base, quote = symbol.split("/", 1)
        pos = self._positions.setdefault(
            symbol,
            {
                "symbol": symbol,
                "base": base,
                "quote": quote,
                "qty": 0.0,
                "avg_price": 0.0,
            },
        )

        old_qty = float(pos["qty"])
        old_avg = float(pos["avg_price"])
        notional = qty * price

        self._cash.setdefault(quote, 0.0)

        if side == "BUY":
            new_qty = old_qty + qty
            new_avg = ((old_qty * old_avg) + notional) / new_qty if new_qty > 0 else 0.0
            pos["qty"] = new_qty
            pos["avg_price"] = new_avg
            self._cash[quote] -= notional
            return

        # SELL
        if qty > old_qty:
            raise ValueError("sell qty exceeds current position")

        realized = (price - old_avg) * qty
        self._realized += realized
        new_qty = old_qty - qty
        pos["qty"] = new_qty
        pos["avg_price"] = old_avg if new_qty > 0 else 0.0
        self._cash[quote] += notional

        if new_qty == 0.0:
            # keep symbol row but zeroed for stable snapshots
            pos["qty"] = 0.0
            pos["avg_price"] = 0.0

    def snapshot(
        self,
        marks: dict[str, float] | None = None,
        *,
        target_quote: str | None = None,
        quote_marks: dict[str, float] | None = None,
    ) -> dict:
        marks = marks or {}
        quote_marks = quote_marks or {}
        quote_marks_norm: dict[str, float] = {}
        for k, v in quote_marks.items():
            kk = str(k or "").strip().upper()
            if not kk or "/" not in kk:
                continue
            try:
                quote_marks_norm[kk] = float(v)
            except Exception:
                continue
        positions = []
        unrealized = 0.0

        for symbol in sorted(self._positions):
            pos = self._positions[symbol]
            qty = float(pos["qty"])
            avg_price = float(pos["avg_price"])
            mark = marks.get(symbol)
            if mark is not None:
                mark = float(mark)
                unrealized += (mark - avg_price) * qty

            positions.append(
                {
                    "symbol": pos["symbol"],
                    "base": pos["base"],
                    "quote": pos["quote"],
                    "qty": qty,
                    "avg_price": avg_price,
                    "mark_price": float(mark) if mark is not None else None,
                    "unrealized": ((float(mark) - avg_price) * qty) if mark is not None else None,
                }
            )

        cash = dict(sorted(self._cash.items()))
        equity_by_quote: dict[str, float] = dict(cash)

        for pos in positions:
            qty = float(pos["qty"])
            quote = str(pos["quote"])
            mark = pos["mark_price"]
            if mark is not None:
                equity_by_quote[quote] = float(equity_by_quote.get(quote, 0.0)) + (float(mark) * qty)

        equity_by_quote = dict(sorted(equity_by_quote.items()))
        total_equity = None
        fx_conversion = {
            "target_quote": _norm_ccy(target_quote) if target_quote else None,
            "used": [],
            "missing": [],
            "complete": None,
        }

        if target_quote:
            target_quote = _norm_ccy(target_quote)
            converted = 0.0
            for quote, value in equity_by_quote.items():
                if quote == target_quote:
                    converted += float(value)
                    fx_conversion["used"].append({"from": quote, "to": target_quote, "pair": None, "rate": 1.0, "method": "identity"})
                    continue
                pair = f"{_norm_ccy(quote)}/{target_quote}"
                inv_pair = f"{target_quote}/{_norm_ccy(quote)}"
                rate = quote_marks_norm.get(pair)
                method = "direct"
                if rate is None:
                    inv_rate = quote_marks_norm.get(inv_pair)
                    if inv_rate is not None and float(inv_rate) != 0.0:
                        rate = 1.0 / float(inv_rate)
                        method = "inverse"
                if rate is None:
                    total_equity = None
                    fx_conversion["missing"].append({"from": quote, "to": target_quote, "pair": pair, "inverse_pair": inv_pair})
                    break
                converted += float(value) * float(rate)
                fx_conversion["used"].append(
                    {"from": quote, "to": target_quote, "pair": pair if method == "direct" else inv_pair, "rate": float(rate), "method": method}
                )
            else:
                total_equity = float(converted)
            fx_conversion["complete"] = total_equity is not None
        elif len(equity_by_quote) == 1:
            total_equity = float(next(iter(equity_by_quote.values())))
            fx_conversion["complete"] = True
        else:
            fx_conversion["complete"] = False

        return {
            "positions": positions,
            "cash": cash,
            "realized": float(self._realized),
            "unrealized": float(unrealized),
            "equity_by_quote": equity_by_quote,
            "total_equity": total_equity,
            "fx_conversion": fx_conversion,
        }
