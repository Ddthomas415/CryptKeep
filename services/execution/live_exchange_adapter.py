from __future__ import annotations
from services.market_data.symbol_router import normalize_venue, map_symbol
from services.execution.lifecycle_boundary import (
    cancel_order_via_boundary,
    fetch_my_trades_via_boundary,
    fetch_order_via_boundary,
)
from services.execution.order_params import prepare_ccxt_params
from services.execution.place_order import place_order
from services.execution.execution_context import ExecutionContext
from services.security.credentials_loader import load_exchange_credentials
from services.security.exchange_factory import make_exchange

class LiveExchangeAdapter:
    def __init__(self, venue: str, *, enable_rate_limit: bool = True) -> None:
        self.venue = normalize_venue(venue)
        creds = load_exchange_credentials(self.venue)
        self._creds_meta = {
            k: creds.get(k)
            for k in (
                "venue",
                "source",
                "api_env",
                "secret_env",
                "password_env",
                "api_key_present",
                "secret_present",
                "password_present",
            )
        }
        if not creds.get("apiKey") or not creds.get("secret"):
            raise RuntimeError(
                f"Missing credentials for {self.venue}: "
                f"keyring or env-backed credentials required "
                f"({creds.get('api_env')}, {creds.get('secret_env')})"
            )
        self.ex = make_exchange(
            self.venue,
            {
                "apiKey": creds["apiKey"],
                "secret": creds["secret"],
                "password": creds.get("password"),
            },
            enable_rate_limit=enable_rate_limit,
        )

    def creds_meta(self) -> dict:
        return dict(self._creds_meta)

    def close(self) -> None:
        try:
            if hasattr(self.ex, "close"):
                self.ex.close()
        except Exception as _err:
            pass  # suppressed: live_exchange_adapter.py

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
        context: ExecutionContext | None = None,
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
        context: ExecutionContext | None = None,
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
        return place_order(self.ex, sym, order_type, side, float(qty), price, ccxt_params, context=context)

    def cancel_order(self, canonical_symbol: str, exchange_order_id: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return cancel_order_via_boundary(
            self.ex,
            venue=self.venue,
            symbol=sym,
            order_id=str(exchange_order_id),
            source="live_exchange_adapter.cancel_order",
        )

    def fetch_order(self, canonical_symbol: str, exchange_order_id: str) -> dict:
        sym = map_symbol(self.venue, canonical_symbol)
        return fetch_order_via_boundary(
            self.ex,
            venue=self.venue,
            symbol=sym,
            order_id=str(exchange_order_id),
            source="live_exchange_adapter.fetch_order",
        )

    def fetch_my_trades(self, canonical_symbol: str, since_ms: int | None = None, limit: int | None = 200) -> list[dict]:
        sym = map_symbol(self.venue, canonical_symbol)
        return fetch_my_trades_via_boundary(
            self.ex,
            venue=self.venue,
            symbol=sym,
            since_ms=since_ms,
            limit=limit,
            source="live_exchange_adapter.fetch_my_trades",
        )


    def find_order_by_client_oid(self, canonical_symbol: str, client_oid: str) -> dict | None:
        sym = map_symbol(self.venue, canonical_symbol)
        try:
            oo = self.ex.fetch_open_orders(sym) or []
        except Exception:
            oo = []
        for o in oo:
            ocid = (
                o.get("clientOrderId")
                or o.get("client_order_id")
                or (o.get("info") or {}).get("clientOrderId")
                or (o.get("info") or {}).get("text")
            )
            if ocid and str(ocid) == str(client_oid):
                return dict(o or {})
        return None
