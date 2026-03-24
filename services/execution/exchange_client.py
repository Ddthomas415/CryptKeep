from __future__ import annotations

import getpass
import inspect
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import ccxt  # type: ignore

from services.execution.place_order import place_order
from services.execution.risk_gates import require_binance_allowed
from services.os.app_paths import data_dir, ensure_dirs

# Human Review Required: confirm per-exchange client order id param names.
def client_id_param(exchange_id: str, client_id: str | None) -> dict:
    if not client_id:
        return {}
    ex = str(exchange_id).lower()
    if ex == "binance":
        return {"newClientOrderId": client_id}
    return {"clientOrderId": client_id}

from services.security.credentials_loader import load_exchange_credentials
from storage.idempotency_sqlite import OrderDedupeStore
from services.execution.order_reconciliation import reconcile_ambiguous_submission, SafeToRetryAfterReconciliation

_LOG = logging.getLogger(__name__)
_PROMPT_CACHE: Dict[str, Dict[str, str]] = {}


def _coinbase_ccxt_id() -> str:
    return "coinbase"


def _client_id_short(intent_id: str) -> str:
    clean = "".join(ch for ch in str(intent_id) if ch.isalnum()).lower()
    return f"cbp-{clean[:24]}" if clean else "cbp-intent"


def make_client_order_id(exchange_id: str, intent_id: str) -> str:
    ex = (exchange_id or "").lower().strip()
    base = _client_id_short(intent_id)
    if ex == "binance":
        return base[:36]
    if ex == "coinbase":
        return base[:100]
    return base[:48]


def _prompt_exchange_creds(exchange_id: str) -> Dict[str, str]:
    """
    Development-only interactive prompt cache.
    Secrets remain in process memory only and are not written into os.environ.
    This path is legacy/non-preferred; the preferred runtime path is the shared
    credentials loader used by LiveExchangeAdapter.
    """
    ex = exchange_id.upper().replace(".", "_")
    cached = _PROMPT_CACHE.get(ex)
    if cached:
        return dict(cached)

    print(f"[crypto-bot-pro] Enter credentials for {exchange_id} (leave blank to skip)")
    key = getpass.getpass(f"{ex}_API_KEY: ").strip()
    sec = getpass.getpass(f"{ex}_API_SECRET: ").strip()
    pwd = getpass.getpass(f"{ex}_API_PASSPHRASE (optional): ").strip()

    out: Dict[str, str] = {}
    if key:
        out["apiKey"] = key
    if sec:
        out["secret"] = sec
    if pwd:
        out["password"] = pwd

    _PROMPT_CACHE[ex] = dict(out)
    return dict(out)


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


def _safe_close(ex: Any, *, where: str) -> None:
    try:
        ex.close()
    except Exception as e:
        _LOG.warning("exchange close failed in %s: %s: %s", where, type(e).__name__, e)


@dataclass
class ExchangeClient:
    """
    Legacy/non-preferred execution helper.

    Preferred runtime path:
      LiveExchangeAdapter -> shared credentials loader -> place_order.py

    This class is kept for compatibility, but it should use the same shared
    credentials loader and must not become its own credential authority.
    """
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
        params.update(load_exchange_credentials(self.exchange_id))

        if self.options:
            params["options"] = dict(self.options)

        ex = ex_cls(params)
        if hasattr(ex, "set_sandbox_mode"):
            try:
                ex.set_sandbox_mode(bool(self.sandbox))
            except Exception as e:
                _LOG.warning("set_sandbox_mode failed for %s: %s: %s", self.exchange_id, type(e).__name__, e)
        try:
            ex.load_markets()
        except Exception as e:
            _LOG.warning("load_markets failed for %s: %s: %s", self.exchange_id, type(e).__name__, e)
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
        db_path = exec_db or str(Path(data_dir()) / "execution.sqlite")
        store = OrderDedupeStore(exec_db=db_path)

        if client_id is None and intent_id is not None:
            client_id = make_client_order_id(self.exchange_id, str(intent_id))

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

            if st in ("submitted", "unknown"):
                raise RuntimeError(f"idempotency blocks resubmit: status={st}")

        try:
            params: Dict[str, Any] = {}
            if client_id:
                params.update(client_id_param(self.exchange_id, client_id))
            if extra_params:
                params.update(extra_params)

            # Preserve the centralized raw-order authority.
            o = place_order(ex, symbol, order_type, side, float(amount), price, params)

            if intent_id is not None:
                store.mark_submitted(
                    exchange_id=self.exchange_id,
                    intent_id=str(intent_id),
                    remote_order_id=str(o.get("id") or "") or None,
                )

            return o
        except Exception as e:
            if intent_id is not None:
                msg = f"{type(e).__name__}:{e}"
                if _is_ambiguous_submit_error(e):
                    store.mark_unknown(exchange_id=self.exchange_id, intent_id=str(intent_id), error=msg)
                    recon = reconcile_ambiguous_submission(
                        venue=self.exchange_id,
                        client=ex,
                        symbol=symbol,
                        client_oid=client_id,
                        remote_order_id=None,
                        age_sec=0,
                    )
                    if recon.outcome == "confirmed_not_placed":
                        raise SafeToRetryAfterReconciliation("confirmed_not_placed_after_reconciliation")
                    raise RuntimeError(f"ambiguous_submit_blocked:{recon.outcome}")
                else:
                    store.mark_error(exchange_id=self.exchange_id, intent_id=str(intent_id), error=msg)
            raise
        finally:
            _safe_close(ex, where="submit_order")

    def fetch_order(self, *, order_id: str, symbol: str) -> Dict[str, Any]:
        ex = self.build()
        try:
            return ex.fetch_order(order_id, symbol)
        finally:
            _safe_close(ex, where="fetch_order")

    def fetch_open_orders(self, *, symbol: str, since: int | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        ex = self.build()
        try:
            return ex.fetch_open_orders(symbol, since, limit)
        finally:
            _safe_close(ex, where="fetch_open_orders")

    def fetch_my_trades(self, *, symbol: str, since: int | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        ex = self.build()
        try:
            return ex.fetch_my_trades(symbol, since, limit)
        finally:
            _safe_close(ex, where="fetch_my_trades")

    def cancel_intent(self, *, exec_db: str, intent_id: str, symbol: str) -> dict:
        # Legacy lifecycle helper; separately audited from raw submit safety.
        ex_id = (self.exchange_id or "").lower().strip()
        store = OrderDedupeStore(exec_db=exec_db)
        row = store.get_by_intent(ex_id, str(intent_id))
        if not row:
            return {"ok": False, "error": "unknown_intent"}

        cid = str(row.get("client_order_id") or "")
        rid = str(row.get("remote_order_id") or "")

        if not rid:
            try:
                oo = self.fetch_open_orders(symbol=symbol) or []
            except Exception:
                oo = []
            for o in oo:
                ocid = (
                    o.get("clientOrderId")
                    or o.get("client_order_id")
                    or (o.get("info") or {}).get("clientOrderId")
                    or (o.get("info") or {}).get("text")
                )
                if ocid and str(ocid) == cid:
                    rid = str(o.get("id") or "")
                    break
            if rid:
                store.set_remote_id_if_empty(exchange_id=ex_id, intent_id=str(intent_id), remote_order_id=rid)

        if not rid:
            return {"ok": False, "error": "remote_id_unknown", "client_order_id": cid}

        ex = self.build()
        try:
            out = ex.cancel_order(rid, symbol)
        except Exception as e:
            return {"ok": False, "error": f"{type(e).__name__}: {e}", "remote_order_id": rid}
        finally:
            _safe_close(ex, where="cancel_intent")

        store.mark_terminal(exchange_id=ex_id, intent_id=str(intent_id), terminal_status="canceled")
        return {"ok": True, "remote_order_id": rid, "exchange_status": (out or {}).get("status")}


def make_client_id(intent_id: str) -> str:
    return _client_id_short(intent_id)


def _cbp_guard_binance(ex_id: str) -> None:
    require_binance_allowed(ex_id)
