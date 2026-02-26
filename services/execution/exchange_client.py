from __future__ import annotations

import os
from services.security.binance_guard import require_binance_allowed
import sys
import time
import uuid
import getpass
from dataclasses import dataclass
from typing import Any, Dict, Optional

import ccxt

from services.os.app_paths import data_dir, ensure_dirs
from services.execution.place_order import place_order
from services.execution.client_order_id import make_client_order_id
from storage.order_dedupe_store_sqlite import OrderDedupeStore


def _now_ms() -> int:
    return int(time.time() * 1000)

def _coinbase_auth_mode() -> str:
    # Controls Coinbase Advanced Trade vs legacy (Coinbase Pro-style) auth routing.
    v = (
        os.environ.get("CBP_COINBASE_AUTH_MODE")
        or os.environ.get("COINBASE_AUTH_MODE")
        or os.environ.get("CBP_COINBASE_MODE")
        or ""
    )
    return str(v).strip().lower()

def _coinbase_ccxt_id() -> str:
    # "coinbase" in ccxt is Advanced Trade; "coinbasepro" is legacy.
    mode = _coinbase_auth_mode()
    if mode in ("legacy", "pro", "coinbasepro", "exchange", "coinbase_exchange"):
        return "coinbasepro"
    if mode in ("jwt", "cdp", "advanced", "adv", "coinbase", "advanced_trade"):
        return "coinbase"
    # Auto-choose: passphrase implies legacy, otherwise default to advanced.
    if os.environ.get("COINBASE_API_PASSPHRASE") or os.environ.get("COINBASE_API_PASSWORD"):
        return "coinbasepro"
    return "coinbase"

def _client_id_short(uuid_str: str) -> str:
    # keep small and ASCII-safe (some venues constrain length)
    s = uuid_str.replace("-", "")
    return ("cbp_" + s[:24])

def client_id_param(exchange_id: str, client_id: str) -> Dict[str, Any]:
    ex = exchange_id.lower()
    require_binance_allowed(ex)
    if ex == "binance":
        return {"newClientOrderId": client_id}
    if ex == "coinbase":
        return {"clientOrderId": client_id}
    if ex == "gateio":
        # Gate API: "text" can be used as user custom id
        return {"text": client_id}
    return {"clientOrderId": client_id}



# CBP_PROMPT_FOR_KEYS_V1
# Optional interactive prompting for API keys (stored only in-memory for this process).
# Enable by setting: CBP_PROMPT_FOR_KEYS=1
# Works best when running in a TTY.

_PROMPT_CACHE: dict[str, Dict[str, str]] = {}

def _truthy_env(v: str | None) -> bool:
    if v is None:
        return False
    return str(v).strip().lower() in ("1","true","yes","y","on")

def _prompt_exchange_creds(exchange_id: str) -> Dict[str, str]:
    ex = str(exchange_id).upper().replace(".", "_")
    if not _truthy_env(os.environ.get("CBP_PROMPT_FOR_KEYS")):
        return {}
    try:
        if not sys.stdin.isatty():
            return {}
    except Exception:
        return {}

    if ex in _PROMPT_CACHE:
        return dict(_PROMPT_CACHE[ex])

    print("")
    print(f"[CBP] Missing API creds for {exchange_id}. Enter them now (in-memory only).")
    print("")

    key = input(f"{ex}_API_KEY: ").strip()
    if not key:
        return {}
    sec = getpass.getpass(f"{ex}_API_SECRET: ").strip()
    if not sec:
        return {}
    pwd = getpass.getpass(f"{ex}_API_PASSPHRASE (optional, press Enter to skip): ").strip()

    out: Dict[str, str] = {"apiKey": key, "secret": sec}
    if pwd:
        out["password"] = pwd

    _PROMPT_CACHE[ex] = dict(out)
    os.environ[f"{ex}_API_KEY"] = key
    os.environ[f"{ex}_API_SECRET"] = sec
    if pwd:
        os.environ[f"{ex}_API_PASSPHRASE"] = pwd
    return dict(out)

def credentials_from_env(exchange_id: str) -> Dict[str, str]:
    ex = exchange_id.upper().replace(".", "_")
    key = os.environ.get(f"{ex}_API_KEY") or os.environ.get("CBP_API_KEY")
    sec = os.environ.get(f"{ex}_API_SECRET") or os.environ.get("CBP_API_SECRET")
    pwd = os.environ.get(f"{ex}_API_PASSPHRASE") or os.environ.get(f"{ex}_API_PASSWORD") or os.environ.get("CBP_API_PASSPHRASE")
    out: Dict[str, str] = {}
    if exchange_id.lower() == "coinbase":
        # Advanced Trade keys are often labeled "private key" / "JWT".
        sec = sec or os.environ.get("COINBASE_PRIVATE_KEY") or os.environ.get("COINBASE_API_PRIVATE_KEY") or os.environ.get("CBP_COINBASE_PRIVATE_KEY") or os.environ.get("CBP_COINBASE_JWT")
    if key: out["apiKey"] = key
    if sec: out["secret"] = sec
    # some exchanges (or legacy coinbase exchange) require password/passphrase
    if pwd and not (exchange_id.lower() == "coinbase" and _coinbase_ccxt_id() == "coinbase"):
        out["password"] = pwd
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
        ex_id = self.exchange_id
        if ex_id.lower() == "coinbase":
            ex_id = _coinbase_ccxt_id()
        if not hasattr(ccxt, ex_id):
            raise ValueError(f"ccxt has no exchange id '{ex_id}'")
        ex_cls = getattr(ccxt, ex_id)
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
        ensure_dirs()
        db_path = exec_db or os.environ.get("EXEC_DB_PATH") or os.environ.get("CBP_DB_PATH") or str(data_dir() / "execution.sqlite")
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

    # ---------------- PHASE 84: idempotent cancel helper ----------------
    def cancel_intent(self, *, exec_db: str, intent_id: str, symbol: str) -> dict:
        ex_id = (self.exchange_id or "").lower().strip()
        store = OrderDedupeStore(exec_db=exec_db)
        row = store.get_by_intent(ex_id, str(intent_id))
        if not row:
            return {"ok": False, "error": "unknown_intent"}

        cid = str(row.get("client_order_id") or "")
        rid = str(row.get("remote_order_id") or "")

        if not rid:
            # resolve via open orders
            try:
                oo = self.fetch_open_orders(symbol=symbol) or []
            except Exception:
                oo = []
            for o in oo:
                ocid = o.get("clientOrderId") or o.get("client_order_id") or (o.get("info") or {}).get("clientOrderId") or (o.get("info") or {}).get("text")
                if ocid and str(ocid) == cid:
                    rid = str(o.get("id") or "")
                    break
            if rid:
                store.set_remote_id_if_empty(exchange_id=ex_id, intent_id=str(intent_id), remote_order_id=rid)

        if not rid:
            return {"ok": False, "error": "remote_id_unknown", "client_order_id": cid}

        try:
            out = self.exchange.cancel_order(rid, symbol)
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}", "remote_order_id": rid}

        store.mark_terminal(exchange_id=ex_id, intent_id=str(intent_id), terminal_status="canceled")
        return {"ok": True, "remote_order_id": rid, "exchange_status": (out or {}).get("status")}

def _cbp_guard_binance(ex_id: str) -> None:
    require_binance_allowed(ex_id)
