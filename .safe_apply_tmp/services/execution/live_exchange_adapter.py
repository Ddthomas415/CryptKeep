from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
from services.market_data.symbol_router import normalize_venue, map_symbol
from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange

class LiveExchangeAdapter:
    def __init__(self, venue: str, *, enable_rate_limit: bool = True) -> None:
        self.venue = normalize_venue(venue)
        creds = load_exchange_credentials(self.venue)
        self._creds_meta = {k: creds.get(k) for k in ("venue","api_env","secret_env","password_env","api_key_present","secret_present","password_present")}
        if not creds.get("apiKey") or not creds.get("secret"):
            raise RuntimeError(f"Missing credentials for {self.venue}: set ENV {creds.get('api_env')} and {creds.get('secret_env')}")
        self.ex = make_exchange(self.venue, {"apiKey": creds["apiKey"], "secret": creds["secret"], "password": creds.get("password")}, enable_rate_limit=enable_rate_limit)

    def creds_meta(self) -> dict:
        return dict(self._creds_meta)

    def close(self) -> None:
        try:
            if hasattr(self.ex, "close"):
                self.ex.close()
        except Exception:
            pass

    def fetch_balance(self) -> dict:
        return self.ex.fetch_balance()

    def fetch_ticker(self, canonical_symbol: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.fetch_ticker(sym)

    def create_order(
        self,
        *,
        canonical_symbol: str,
        side: str,
        order_type: str,
        qty: float,
        limit_price: float | None,
        client_order_id: str,
    ) -> dict:
        """
        Best-effort clientOrderId support.
        """
        sym = map_symbol(self.venue, canonical_symbol)
        side = str(side).lower().strip()
        order_type = str(order_type).lower().strip()
        params = {"clientOrderId": client_order_id}
        price = float(limit_price) if (order_type == "limit" and limit_price is not None) else None
        return self.place_order(sym, order_type, side, float(qty), price, params)

    def cancel_order(self, canonical_symbol: str, exchange_order_id: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.cancel_order(exchange_order_id, sym)

    def fetch_order(self, canonical_symbol: str, exchange_order_id: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.fetch_order(exchange_order_id, sym)

    def fetch_my_trades(self, canonical_symbol: str, since_ms: int | None = None, limit: int | None = 200) -> list[dict]:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.fetch_my_trades(sym, since=since_ms, limit=limit)