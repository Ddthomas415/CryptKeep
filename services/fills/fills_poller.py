from __future__ import annotations

import asyncio, datetime, time
from dataclasses import dataclass
from typing import Any, Dict, List
import yaml

from services.security.exchange_credentials import ExchangeCredentialManager
from services.execution.ccxt_adapter import CCXTAdapterCfg, CCXTExchangeAdapter
from services.journal.fill_sink import CanonicalFillSink
from services.risk.live_risk_gates import LiveGateDB

def _load_yaml(path: str) -> Dict[str, Any]:
    return yaml.safe_load(open(path, "r", encoding="utf-8").read()) or {}

def _now_ms() -> int:
    return int(time.time() * 1000)

def _k_since(ex: str) -> str:
    return f"fills_since_ms::{ex}"

def _k_hb(ex: str) -> str:
    return f"fills_poller_last::{ex}"

def _k_last_err(ex: str) -> str:
    return f"fills_poller_err::{ex}"

@dataclass
class FillsPollerCfg:
    exec_db: str
    exchanges: List[str]
    poll_interval_sec: float = 5.0
    lookback_ms: int = 5*60*1000
    sandbox: bool = False
    default_type: str = "spot"
    enable_rate_limit: bool = True

class FillsPoller:
    """
    REST-polls 'my trades' and writes to canonical FillSink.
    Idempotent, cursored, safe defaults (no orders placed).
    """
    def __init__(self, cfg: FillsPollerCfg):
        self.cfg = cfg
        self.db = LiveGateDB(exec_db=cfg.exec_db)
        self.sink = CanonicalFillSink(exec_db=cfg.exec_db)
        self.cred = ExchangeCredentialManager()
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    def _load_since_ms(self, ex_id: str) -> int:
        s = self.db.get_state(_k_since(ex_id), "")
        if s.strip().isdigit():
            return int(s.strip())
        return max(0, _now_ms() - int(self.cfg.lookback_ms))

    def _save_since_ms(self, ex_id: str, since_ms: int) -> None:
        self.db.set_state(_k_since(ex_id), str(int(since_ms)))

    def _hb(self, ex_id: str) -> None:
        self.db.set_state(_k_hb(ex_id), datetime.datetime.utcnow().isoformat() + "Z")

    def _err(self, ex_id: str, msg: str) -> None:
        self.db.set_state(_k_last_err(ex_id), msg[:500])

    def _make_exchange(self, ex_id: str):
        a = CCXTExchangeAdapter(CCXTAdapterCfg(
            exec_db=self.cfg.exec_db,
            exchange_id=ex_id,
            enable_rate_limit=bool(self.cfg.enable_rate_limit),
            sandbox=bool(self.cfg.sandbox),
            default_type=str(self.cfg.default_type),
        ))
        ex = a.exchange
        creds = self.cred.load_ccxt_kwargs(ex_id)
        if not creds.get("apiKey") or not creds.get("secret"):
            raise RuntimeError(f"Missing creds for {ex_id}")
        for k, v in creds.items():
            setattr(ex, k, v)
        return ex

    def _trade_to_fill(self, ex_id: str, t: Dict[str, Any]) -> Dict[str, Any]:
        ts = t.get("timestamp") or t.get("datetime") or datetime.datetime.utcnow().isoformat() + "Z"
        fee_usd = 0.0
        fee = t.get("fee")
        if isinstance(fee, dict):
            try:
                cur = str(fee.get("currency") or "").upper()
                cost = float(fee.get("cost") or 0.0)
                if cur in ("USD", "USDT", "USDC"):
                    fee_usd = cost
            except Exception:
                pass
        return {
            "venue": ex_id,
            "fill_id": str(t.get("id") or ""),
            "order_id": str(t.get("order") or t.get("orderId") or ""),
            "client_order_id": "",
            "symbol": t.get("symbol") or "",
            "side": t.get("side") or "",
            "qty": t.get("amount"),
            "price": t.get("price"),
            "ts": ts,
            "fee_usd": fee_usd,
            "realized_pnl_usd": None,
            "raw": {"ccxt_trade": t},
        }

    async def _poll_one(self, ex_id: str) -> None:
        ex_id = ex_id.lower().strip()
        since = self._load_since_ms(ex_id)
        ex = self._make_exchange(ex_id)
        while not self._stop.is_set():
            try:
                trades = ex.fetch_my_trades(None, since, None, {})
                if trades:
                    trades_sorted = sorted(trades, key=lambda x: int(x.get("timestamp") or 0))
                    max_ts = since
                    for t in trades_sorted:
                        fill = self._trade_to_fill(ex_id, t)
                        if not fill.get("symbol") or not fill.get("side") or fill.get("qty") is None or fill.get("price") is None:
                            continue
                        self.sink.on_fill(fill)
                        try:
                            ts = int(t.get("timestamp") or 0)
                            if ts > max_ts:
                                max_ts = ts
                        except Exception:
                            pass
                    if max_ts > since:
                        since = max_ts + 1
                        self._save_since_ms(ex_id, since)
                self._hb(ex_id)
                self._err(ex_id, "")
            except Exception as e:
                self._err(ex_id, f"{type(e).__name__}: {e}")
                await asyncio.sleep(max(2.0, float(self.cfg.poll_interval_sec)))
            await asyncio.sleep(float(self.cfg.poll_interval_sec))
        try:
            ex.close()
        except Exception:
            pass

    async def run(self) -> None:
        tasks = [asyncio.create_task(self._poll_one(ex)) for ex in self.cfg.exchanges]
        try:
            await self._stop.wait()
        finally:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

def load_cfg(path: str = "config/trading.yaml") -> FillsPollerCfg:
    cfg = _load_yaml(path)
    ex_cfg = cfg.get("execution") or {}
    exec_db = str(ex_cfg.get("db_path") or "data/execution.sqlite")
    p = cfg.get("fills_poller") or {}
    exchanges = p.get("exchanges") or (cfg.get("venues") or ["coinbase", "binance", "gate"])
    exchanges = [str(x).lower().strip() for x in exchanges]
    return FillsPollerCfg(
        exec_db=exec_db,
        exchanges=exchanges,
        poll_interval_sec=float(p.get("poll_interval_sec") or 5.0),
        lookback_ms=int(p.get("lookback_ms") or 5*60*1000),
        sandbox=bool(p.get("sandbox") or False),
        default_type=str(p.get("default_type") or "spot"),
        enable_rate_limit=bool(p.get("enable_rate_limit") if p.get("enable_rate_limit") is not None else True),
    )
