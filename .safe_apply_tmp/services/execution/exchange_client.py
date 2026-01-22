from __future__ import annotations

import os
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

import ccxt

from services.execution.place_order import place_order
from services.execution.client_order_id import make_client_order_id
from storage.order_dedupe_store_sqlite import OrderDedupeStore


def _now_ms() -> int:
    return int(time.time() * 1000)

def _client_id_short(uuid_str: str) -> str:
    # keep small and ASCII-safe (some venues constrain length)
    s = uuid_str.replace("-", "")
    return ("cbp_" + s[:24])

def client_id_param(exchange_id: str, client_id: str) -> Dict[str, Any]:
    ex = exchange_id.lower()
    if ex == "binance":
        return {"newClientOrderId": client_id}
    if ex == "coinbase":
        return {"clientOrderId": client_id}
    if ex == "gateio":
        # Gate API: "text" can be used as user custom id
        return {"text": client_id}
    return {"clientOrderId": client_id}

def credentials_from_env(exchange_id: str) -> Dict[str, str]:
    ex = exchange_id.upper().replace(".", "_")
    key = os.environ.get(f"{ex}_API_KEY") or os.environ.get("CBP_API_KEY")
    sec = os.environ.get(f"{ex}_API_SECRET") or os.environ.get("CBP_API_SECRET")
    pwd = os.environ.get(f"{ex}_API_PASSPHRASE") or os.environ.get(f"{ex}_API_PASSWORD") or os.environ.get("CBP_API_PASSPHRASE")
    out: Dict[str, str] = {}
    if key: out["apiKey"] = key
    if sec: out["secret"] = sec
    # some exchanges (or legacy coinbase exchange) require password/passphrase
    if pwd: out["password"] = pwd
    return out


def _is_ambiguous_submit_error(e: Exception) -> bool:
    name = type(e).__name__
    return name in {
        "RequestTimeout",
        "NetworkError",
        "ExchangeNotAvailable",
        "DDoSProtection",
        "RateLimitExceeded",
        "TimeoutError",
    }

@dataclass
class ExchangeClient:
    exchange_id: str
    sandbox: bool = False
    enable_rate_limit: bool = True
    options: Dict[str, Any] | None = None

    def build(self) -> Any:
        if not hasattr(ccxt, self.exchange_id):
            raise ValueError(f"ccxt has no exchange id '{self.exchange_id}'")
        ex_cls = getattr(ccxt, self.exchange_id)
        params: Dict[str, Any] = {"enableRateLimit": bool(self.enable_rate_limit)}
        params.update(credentials_from_env(self.exchange_id))
        if self.options:
            params["options"] = dict(self.options)
        ex = ex_cls(params)
        if hasattr(ex, "set_sandbox_mode"):
            try:
                ex.set_sandbox_mode(bool(self.sandbox))
            except Exception:
                pass
        try:
            ex.load_markets()
        except Exception:
            pass
        return ex
    def submit_order(
        self,
        *,
        symbol: str,
        side: str,
        order_type: str,
        amount: float,
        price: float | None,
        client_id: str | None,
        extra_params: Dict[str, Any] | None = None,
        intent_id: str | None = None,
        exec_db: str | None = None,
    ) -> Dict[str, Any]:
        ex = self.build()
        db_path = exec_db or os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or "data/execution.sqlite"
        store = OrderDedupeStore(exec_db=db_path)

        # Generate compliant stable client id if not provided
        if client_id is None and intent_id is not None:
            client_id = make_client_order_id(self.exchange_id, str(intent_id))

        # Claim-before-submit (restart-safe) when intent_id provided
        if intent_id is not None and client_id is not None:
            row = store.claim(
                exchange_id=self.exchange_id,
                intent_id=str(intent_id),
                symbol=str(symbol),
                client_order_id=str(client_id),
                meta={"side": side, "order_type": order_type},
            )

            rid = row.get("remote_order_id")
            st = str(row.get("status") or "")
            if rid and st in ("submitted", "acked", "terminal"):
                return {"id": rid, "idempotent_replay": True, "client_order_id": client_id, "status": st}

            # If previously submitted/unknown without remote id, block resubmit until reconcile
            if st in ("submitted", "unknown"):
                raise RuntimeError(f"idempotency blocks resubmit: status={st}")

        try:
            params: Dict[str, Any] = {}
            if client_id:
                params.update(client_id_param(self.exchange_id, client_id))
            if extra_params:
                params.update(extra_params)

            # IMPORTANT: use the centralized chokepoint (only place_order.py calls into exchange)
            o = place_order(ex, symbol, order_type, side, float(amount), price, params)

            if intent_id is not None:
                store.mark_submitted(exchange_id=self.exchange_id, intent_id=str(intent_id), remote_order_id=str(o.get("id") or "") or None)

            return o
        except Exception as e:
            if intent_id is not None:
                msg = f"{type(e).__name__}:{e}"
                if _is_ambiguous_submit_error(e):
                    store.mark_unknown(exchange_id=self.exchange_id, intent_id=str(intent_id), error=msg)
                else:
                    store.mark_error(exchange_id=self.exchange_id, intent_id=str(intent_id), error=msg)
            raise
        finally:
            try:
                ex.close()
            except Exception:
                pass

    def fetch_order(self, *, order_id: str, symbol: str) -> Dict[str, Any]:
        ex = self.build()
        try:
            return ex.fetch_order(order_id, symbol)
        finally:
            try: ex.close()
            except Exception: pass

    def fetch_open_orders(self, *, symbol: str, since: int | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        ex = self.build()
        try:
            return ex.fetch_open_orders(symbol, since, limit)
        finally:
            try: ex.close()
            except Exception: pass

    def fetch_my_trades(self, *, symbol: str, since: int | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        ex = self.build()
        try:
            return ex.fetch_my_trades(symbol, since, limit)
        finally:
            try: ex.close()
            except Exception: pass

def make_client_id(intent_id: str) -> str:
    return _client_id_short(intent_id)  # stable mapping