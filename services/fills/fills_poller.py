from __future__ import annotations

# CBP_FILLS_POLLER_STATE_DB_FIXED_V2

# CBP_FILLS_POLLER_STATE_DB_AND_EXCHANGE_MAP_V1

# CBP_FILLS_POLLER_STATE_DB_V1

# CBP_OPTIONAL_YAML_V1

# CBP_FILLS_POLLER_USE_EXCHANGE_CLIENT_V1

# CBP_FILLS_POLLER_FILL_ID_AND_FEE_USD_V1

# CBP_FILLS_POLLER_SINGLE_SINK_PATH_V1

import os

# CBP_FILLS_POLLER_CALLS_FILL_SINK_V1

import asyncio, datetime, time
import sqlite3
from pathlib import Path as _Path
from dataclasses import dataclass
from typing import Any, Dict, List
# yaml is optional (PyYAML)
from services.os.app_paths import data_dir, ensure_dirs

from services.execution.exchange_client import ExchangeClient

from services.journal.fill_sink import CanonicalFillSink
from services.fills.user_stream_router import ccxt_trade_to_fill, route_fill_event



# CBP_FILLS_POLLER_STATE_DB_V1_FIX
class _StateDB:
    def __init__(self, exec_db: str):
        self.exec_db = str(exec_db)
        _Path(self.exec_db).parent.mkdir(parents=True, exist_ok=True)
        self._ensure()

    def _conn(self):
        c = sqlite3.connect(self.exec_db)
        c.row_factory = sqlite3.Row
        return c

    def _ensure(self) -> None:
        with self._conn() as c:
            c.execute("""
            CREATE TABLE IF NOT EXISTS fills_poller_state(
              k TEXT PRIMARY KEY,
              v TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            """)

    def get(self, k: str, default: str = "") -> str:
        with self._conn() as c:
            r = c.execute("SELECT v FROM fills_poller_state WHERE k=?", (str(k),)).fetchone()
            return str(r["v"]) if r else str(default)

    def set(self, k: str, v: str) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO fills_poller_state(k,v,updated_at) VALUES(?,?,?) "
                "ON CONFLICT(k) DO UPDATE SET v=excluded.v, updated_at=excluded.updated_at",
                (str(k), str(v), datetime.datetime.utcnow().isoformat() + "Z"),
            )
def _load_yaml(path: str) -> Dict[str, Any]:
    # PyYAML is optional; fall back to env/defaults if unavailable.
    try:
        import yaml  # type: ignore
        return yaml.safe_load(open(path, "r", encoding="utf-8").read()) or {}
    except Exception:
        # Try JSON as a fallback (rare but harmless)
        try:
            import json
            return json.loads(open(path, "r", encoding="utf-8").read()) or {}
        except Exception:
            return {}

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
    route_via_live_executor_hook: bool = True

class FillsPoller:
    """
    REST-polls 'my trades' and writes to canonical FillSink.
    Idempotent, cursored, safe defaults (no orders placed).
    """
    def __init__(self, cfg: FillsPollerCfg):
        self.cfg = cfg
        self.state = _StateDB(exec_db=cfg.exec_db)
        self.sink = CanonicalFillSink(exec_db=cfg.exec_db)
        self._stop = asyncio.Event()

    def stop(self) -> None:
        self._stop.set()

    def _load_since_ms(self, ex_id: str) -> int:
        s = self.state.get(_k_since(ex_id), "")
        if s.strip().isdigit():
            return int(s.strip())
        return max(0, _now_ms() - int(self.cfg.lookback_ms))

    def _save_since_ms(self, ex_id: str, since_ms: int) -> None:
        self.state.set(_k_since(ex_id), str(int(since_ms)))

    def _hb(self, ex_id: str) -> None:
        self.state.set(_k_hb(ex_id), datetime.datetime.utcnow().isoformat() + "Z")

    def _err(self, ex_id: str, msg: str) -> None:
        self.state.set(_k_last_err(ex_id), msg[:500])

    def _make_exchange(self, ex_id: str):
        # Use the central ExchangeClient (avoids missing ccxt_adapter/credential_manager modules)
        ex_id = str(ex_id).lower().strip()
        ex_id = {'gate':'gateio','gate.io':'gateio'}.get(ex_id, ex_id)
        ex_id = {'gate':'gateio','gate.io':'gateio'}.get(ex_id, ex_id)
        ex_id = {'gate':'gateio','gate.io':'gateio'}.get(ex_id, ex_id)
        opts = {"defaultType": str(self.cfg.default_type)} if getattr(self.cfg, "default_type", None) else None
        # Friendly missing-creds check (env-based)
        need = (ex_id.upper().replace('.','_') + '_API_')
        if not (os.environ.get(need+'KEY') or os.environ.get('CBP_API_KEY')):
            raise RuntimeError(f"Missing creds for {ex_id} (set {need}KEY and {need}SECRET, or CBP_API_KEY/CBP_API_SECRET)")
        if not (os.environ.get(need+'SECRET') or os.environ.get('CBP_API_SECRET')):
            raise RuntimeError(f"Missing creds for {ex_id} (set {need}KEY and {need}SECRET, or CBP_API_KEY/CBP_API_SECRET)")

        ex = ExchangeClient(
            exchange_id=ex_id,
            sandbox=bool(self.cfg.sandbox),
            enable_rate_limit=bool(self.cfg.enable_rate_limit),
            options=(dict(opts) if isinstance(opts, dict) else None),
        ).build()
        return ex
    def _trade_to_fill(self, ex_id: str, t: Dict[str, Any]) -> Dict[str, Any]:
        return ccxt_trade_to_fill(ex_id, t)
    async def _poll_one(self, ex_id: str) -> None:
        ex_id = ex_id.lower().strip()
        ex_id = {'gate':'gateio','gate.io':'gateio'}.get(ex_id, ex_id)
        ex_id = {'gate':'gateio','gate.io':'gateio'}.get(ex_id, ex_id)
        ex_id = {'gate':'gateio','gate.io':'gateio'}.get(ex_id, ex_id)
        since = self._load_since_ms(ex_id)
        # CBP_POLL_ONE_LAZY_EXCHANGE_V1
        ex = None
        while not self._stop.is_set():
            if ex is None:
                try:
                    ex = self._make_exchange(ex_id)
                except Exception as e:
                    self._err(ex_id, f"{type(e).__name__}: {e}")
                    await asyncio.sleep(max(5.0, float(self.cfg.poll_interval_sec)))
                    continue
            try:
                trades = ex.fetch_my_trades(None, since, None, {})
                if trades:
                    trades_sorted = sorted(trades, key=lambda x: int(x.get("timestamp") or 0))
                    max_ts = since
                    for t in trades_sorted:
                        fill = self._trade_to_fill(ex_id, t)
                        if not fill.get("symbol") or not fill.get("side") or fill.get("qty") is None or fill.get("price") is None:
                            continue
                        route_fill_event(
                            fill,
                            exec_db=self.cfg.exec_db,
                            prefer_live_executor_hook=bool(self.cfg.route_via_live_executor_hook),
                            fallback_sink=self.sink,
                        )
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
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)

# CBP_FILLS_POLLER_TAIL_CLEAN_V1
def load_cfg(path: str = "config/trading.yaml") -> FillsPollerCfg:
    ensure_dirs()
    cfg = _load_yaml(path)
    ex_cfg = cfg.get("execution") or {}
    if not isinstance(ex_cfg, dict):
        ex_cfg = {}

    exec_db = str(
        ex_cfg.get("db_path")
        or os.environ.get("EXEC_DB_PATH")
        or os.environ.get("CBP_DB_PATH")
        or (data_dir() / "execution.sqlite")
    )

    fp = cfg.get("fills_poller") or {}
    if not isinstance(fp, dict):
        fp = {}

    # Env override wins even if empty string:
    #   - unset -> use config/defaults
    #   - set to "" -> run with zero exchanges
    env_raw = os.environ.get("CBP_FILLS_EXCHANGES")
    if env_raw is not None:
        env_ex = str(env_raw).strip()
        if env_ex == "":
            exchanges = []
            # FILLSPOLLER_DROP_BINANCE_UNLESS_CBP_VENUE
            env_v = (os.environ.get('CBP_VENUE') or '').lower().strip()
            if env_v and not env_v.startswith('binance'):
                exchanges = [v for v in exchanges if not str(v).lower().startswith('binance')]

            _env_v = (os.environ.get("CBP_VENUE") or "").strip().lower()
            if _env_v:
                exchanges = [_env_v]
            else:
                exchanges = [v for v in exchanges if v != 'binance']

        else:
            exchanges = [x.strip() for x in env_ex.split(",") if x.strip()]
    else:
        exchanges = fp.get("exchanges") or cfg.get("venues") or ["coinbase", "gateio"]

    exchanges = [str(x).lower().strip() for x in exchanges if str(x).strip()]
    exchanges = [{"gate": "gateio", "gate.io": "gateio", "coinbase_adv": "coinbase"}.get(e, e) for e in exchanges]

    return FillsPollerCfg(
        exec_db=exec_db,
        exchanges=exchanges,
        poll_interval_sec=float(fp.get("poll_interval_sec") or 5.0),
        lookback_ms=int(fp.get("lookback_ms") or 5 * 60 * 1000),
        sandbox=bool(fp.get("sandbox") or False),
        default_type=str(fp.get("default_type") or "spot"),
        enable_rate_limit=bool(fp.get("enable_rate_limit") if fp.get("enable_rate_limit") is not None else True),
        route_via_live_executor_hook=bool(
            fp.get("route_via_live_executor_hook")
            if fp.get("route_via_live_executor_hook") is not None
            else True
        ),
    )
