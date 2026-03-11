from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import median
from typing import Any, Iterable

from services.ops.live_signal_adapter import LiveSignalAdapter
from services.ops.risk_gate_contract import RawSignalSnapshot
from services.os.app_paths import data_dir, runtime_dir
from services.risk.risk_daily import snapshot as risk_daily_snapshot


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        if v is None:
            return float(default)
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        if v is None:
            return int(default)
        return int(v)
    except Exception:
        return int(default)


def _p95(values: Iterable[float]) -> float:
    vals = sorted(float(v) for v in values)
    if not vals:
        return 0.0
    idx = max(0, min(len(vals) - 1, int(round((len(vals) - 1) * 0.95))))
    return float(vals[idx])


def _stdev(values: list[float]) -> float:
    n = len(values)
    if n <= 1:
        return 0.0
    mu = sum(values) / float(n)
    var = sum((x - mu) ** 2 for x in values) / float(n - 1)
    return math.sqrt(max(0.0, var))


@dataclass(frozen=True)
class TelemetrySnapshotCfg:
    source: str = "ops_signal_adapter"
    symbol: str = "BTC/USD"
    ops_db_path: str = ""
    system_status_path: str = ""
    live_intent_db_path: str = ""
    ws_status_db_path: str = ""
    ws_latency_db_path: str = ""
    market_data_db_path: str = ""
    paper_db_path: str = ""
    exec_db_path: str = ""
    sample_limit: int = 240

    def with_defaults(self) -> "TelemetrySnapshotCfg":
        droot = data_dir()
        rroot = runtime_dir()
        return TelemetrySnapshotCfg(
            source=self.source,
            symbol=self.symbol,
            ops_db_path=self.ops_db_path or str(droot / "ops_intel.sqlite"),
            system_status_path=self.system_status_path or str(rroot / "snapshots" / "system_status.latest.json"),
            live_intent_db_path=self.live_intent_db_path or str(droot / "live_intent_queue.sqlite"),
            ws_status_db_path=self.ws_status_db_path or str(droot / "ws_status.sqlite"),
            ws_latency_db_path=self.ws_latency_db_path or str(rroot / "market_ws.sqlite"),
            market_data_db_path=self.market_data_db_path or str(droot / "market_data.sqlite"),
            paper_db_path=self.paper_db_path or str(droot / "paper_trading.sqlite"),
            exec_db_path=self.exec_db_path or str(droot / "execution.sqlite"),
            sample_limit=max(20, int(self.sample_limit or 240)),
        )


def _load_system_status(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _exchange_api_ok(status: dict[str, Any], symbol_hint: str) -> bool:
    venues = status.get("venues") if isinstance(status.get("venues"), dict) else {}
    if not venues:
        return False
    venue_hint = str(symbol_hint or "").lower().strip()
    if venue_hint and venue_hint in venues and isinstance(venues.get(venue_hint), dict):
        return bool((venues.get(venue_hint) or {}).get("ok"))
    ok_vals = [bool(v.get("ok")) for v in venues.values() if isinstance(v, dict)]
    return any(ok_vals) if ok_vals else False


def _query_values(path: str, sql: str, params: tuple[Any, ...] = ()) -> list[float]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        con = sqlite3.connect(str(p))
        rows = con.execute(sql, params).fetchall()
        con.close()
    except Exception:
        return []
    out: list[float] = []
    for row in rows:
        if not row:
            continue
        out.append(_safe_float(row[0], 0.0))
    return out


def _compute_order_reject_rate(path: str, limit: int) -> float:
    p = Path(path)
    if not p.exists():
        return 0.0
    try:
        con = sqlite3.connect(str(p))
        rows = con.execute(
            "SELECT status FROM live_trade_intents ORDER BY rowid DESC LIMIT ?",
            (max(10, int(limit)),),
        ).fetchall()
        con.close()
    except Exception:
        return 0.0
    statuses = [str(r[0] or "").strip().lower() for r in rows if r]
    if not statuses:
        return 0.0
    attempted = [s for s in statuses if s in {"submitted", "rejected", "filled", "open", "closed", "error", "failed"}]
    if not attempted:
        return 0.0
    rejected = [s for s in attempted if s in {"rejected", "error", "failed"}]
    return float(len(rejected)) / float(max(1, len(attempted)))


def _compute_ws_lag_ms(path: str, limit: int) -> float:
    vals = _query_values(path, "SELECT lag_ms FROM ws_status_events ORDER BY rowid DESC LIMIT ?", (max(20, int(limit)),))
    return _p95(vals)


def _compute_venue_latency_ms(path: str, limit: int) -> float:
    vals = _query_values(
        path,
        "SELECT value_ms FROM market_ws_latency WHERE category='execution' AND name='submit_to_ack_ms' ORDER BY rowid DESC LIMIT ?",
        (max(20, int(limit)),),
    )
    return _p95(vals)


def _compute_realized_volatility(path: str, symbol: str, limit: int) -> float:
    p = Path(path)
    if not p.exists():
        return 0.0
    sym = str(symbol or "").strip()
    if not sym:
        return 0.0
    try:
        con = sqlite3.connect(str(p))
        rows = con.execute(
            "SELECT last FROM market_tickers WHERE symbol=? AND last IS NOT NULL ORDER BY rowid DESC LIMIT ?",
            (sym, max(20, int(limit))),
        ).fetchall()
        con.close()
    except Exception:
        return 0.0
    prices = [_safe_float(r[0], 0.0) for r in rows if r]
    prices = [p for p in prices if p > 0]
    if len(prices) < 3:
        return 0.0
    rets: list[float] = []
    for i in range(1, len(prices)):
        prev = prices[i]
        cur = prices[i - 1]
        if prev <= 0:
            continue
        rets.append((cur - prev) / prev)
    return max(0.0, _stdev(rets))


def _compute_drawdown_exposure_leverage(path: str) -> tuple[float, float, float]:
    p = Path(path)
    if not p.exists():
        return 0.0, 0.0, 0.0
    try:
        con = sqlite3.connect(str(p))
        eq = con.execute("SELECT equity_quote FROM paper_equity ORDER BY rowid DESC LIMIT 1").fetchone()
        peak = con.execute("SELECT MAX(equity_quote) FROM paper_equity").fetchone()
        exp = con.execute("SELECT COALESCE(SUM(ABS(qty * avg_price)), 0) FROM paper_positions").fetchone()
        con.close()
    except Exception:
        return 0.0, 0.0, 0.0

    current_equity = _safe_float(eq[0] if eq else 0.0, 0.0)
    peak_equity = _safe_float(peak[0] if peak else 0.0, 0.0)
    exposure_usd = _safe_float(exp[0] if exp else 0.0, 0.0)
    drawdown_pct = 0.0
    if peak_equity > 0.0 and current_equity >= 0.0:
        drawdown_pct = max(0.0, ((peak_equity - current_equity) / peak_equity) * 100.0)
    leverage = 0.0
    if current_equity > 0.0:
        leverage = max(0.0, exposure_usd / current_equity)
    return drawdown_pct, exposure_usd, leverage


def build_snapshot(cfg: TelemetrySnapshotCfg | None = None) -> RawSignalSnapshot:
    c = (cfg or TelemetrySnapshotCfg()).with_defaults()
    status = _load_system_status(c.system_status_path)
    rd = risk_daily_snapshot(exec_db=str(c.exec_db_path))

    order_reject_rate = _compute_order_reject_rate(c.live_intent_db_path, c.sample_limit)
    ws_lag_ms = _compute_ws_lag_ms(c.ws_status_db_path, c.sample_limit)
    venue_latency_ms = _compute_venue_latency_ms(c.ws_latency_db_path, c.sample_limit)
    realized_volatility = _compute_realized_volatility(c.market_data_db_path, c.symbol, c.sample_limit)
    drawdown_pct, exposure_usd, leverage = _compute_drawdown_exposure_leverage(c.paper_db_path)
    if exposure_usd <= 0.0:
        exposure_usd = abs(_safe_float(rd.get("notional"), 0.0))
    if leverage <= 0.0 and exposure_usd > 0.0:
        # Conservative fallback when no current equity snapshot is available.
        leverage = 1.0

    return RawSignalSnapshot(
        ts=_now_iso(),
        source=str(c.source),
        exchange_api_ok=_exchange_api_ok(status, ""),
        order_reject_rate=float(order_reject_rate),
        ws_lag_ms=float(ws_lag_ms),
        venue_latency_ms=float(venue_latency_ms),
        realized_volatility=float(realized_volatility),
        drawdown_pct=float(drawdown_pct),
        pnl_usd=float(_safe_float(rd.get("pnl"), 0.0)),
        exposure_usd=float(exposure_usd),
        leverage=float(leverage),
        extra={
            "trades_today": _safe_int(rd.get("trades"), 0),
            "risk_day": str(rd.get("day") or ""),
            "system_status_path": c.system_status_path,
        },
    )


def publish_snapshot(cfg: TelemetrySnapshotCfg | None = None) -> dict[str, Any]:
    c = (cfg or TelemetrySnapshotCfg()).with_defaults()
    snap = build_snapshot(c)
    adapter = LiveSignalAdapter.from_default_db(path=str(c.ops_db_path))
    raw_id = adapter.publish_snapshot(snap)
    return {"ok": True, "raw_id": int(raw_id), "snapshot": snap.to_dict()}

