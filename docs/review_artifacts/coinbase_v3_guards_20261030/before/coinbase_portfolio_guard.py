from __future__ import annotations

from typing import Any


def _get_portfolio_uuid(ex: Any) -> str | None:
    resp = ex.v3PrivateGetBrokerageKeyPermissions()
    return resp.get("portfolio_uuid")


def _get_portfolio_currencies(ex: Any, portfolio_uuid: str) -> set[str]:
    bal = ex.fetch_balance()
    data = ((bal or {}).get("info") or {}).get("data") or []
    out: set[str] = set()
    for acct in data:
        if acct.get("portfolio_id") == portfolio_uuid:
            cur = ((acct.get("currency") or {}).get("code")) or ""
            if cur:
                out.add(cur.upper())
    return out


def _split_symbol(symbol: str) -> tuple[str, str]:
    if "/" not in symbol:
        raise ValueError(f"Unsupported symbol format: {symbol}")
    base, quote = symbol.split("/", 1)
    return base.upper(), quote.upper()


def enforce_coinbase_quote_account_available(ex: Any, symbol: str) -> None:
    ex_id = str(getattr(ex, "id", "") or getattr(ex, "exchange_id", "") or "").lower()
    if ex_id != "coinbase":
        return

    portfolio_uuid = _get_portfolio_uuid(ex)
    if not portfolio_uuid:
        raise RuntimeError("CBP_ORDER_BLOCKED:portfolio_uuid_unavailable")

    currencies = _get_portfolio_currencies(ex, portfolio_uuid)
    _, quote = _split_symbol(symbol)

    if quote not in currencies:
        raise RuntimeError(
            "CBP_ORDER_BLOCKED:portfolio_account_unavailable:"
            f"portfolio={portfolio_uuid} "
            f"symbol={symbol} "
            f"missing_quote={quote} "
            f"available_currencies={sorted(currencies)}"
        )
