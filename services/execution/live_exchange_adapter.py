from __future__ import annotations
from services.market_data.symbol_router import normalize_venue, map_symbol
from services.execution.order_params import prepare_ccxt_params
from services.execution.place_order import place_order
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
        params: dict | None = None,
        allow_extra_params: bool = False,
    ) -> dict:
        # Backward-compatible alias; use submit_order in new call sites.
        return self.submit_order(
            canonical_symbol=canonical_symbol,
            side=side,
            order_type=order_type,
            qty=qty,
            limit_price=limit_price,
            client_order_id=client_order_id,
            params=params,
            allow_extra_params=allow_extra_params,
        )

    def submit_order(
        self,
        *,
        canonical_symbol: str,
        side: str,
        order_type: str,
        qty: float,
        limit_price: float | None,
        client_order_id: str,
        params: dict | None = None,
        allow_extra_params: bool = False,
    ) -> dict:
        """
        Venue-aware param normalization + idempotency key injection.
        """
        sym = map_symbol(self.venue, canonical_symbol)
        side = str(side).lower().strip()
        order_type = str(order_type).lower().strip()
        price = float(limit_price) if (order_type == "limit" and limit_price is not None) else None
        ccxt_params = prepare_ccxt_params(
            exchange_id=self.venue,
            client_order_id=str(client_order_id),
            order_type=order_type,
            price=price,
            params=dict(params or {}),
            allow_extra=bool(allow_extra_params),
        )
        return place_order(self.ex, sym, order_type, side, float(qty), price, ccxt_params)

    def cancel_order(self, canonical_symbol: str, exchange_order_id: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.cancel_order(exchange_order_id, sym)

    def fetch_order(self, canonical_symbol: str, exchange_order_id: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.fetch_order(exchange_order_id, sym)

    def fetch_my_trades(self, canonical_symbol: str, since_ms: int | None = None, limit: int | None = 200) -> list[dict]:
        sym = map_symbol(self.venue, canonical_symbol)
        return self.ex.fetch_my_trades(sym, since=since_ms, limit=limit)
