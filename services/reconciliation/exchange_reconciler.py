from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import ccxt.async_support as ccxt  # type: ignore

from storage.reconciliation_store_sqlite import SQLiteReconciliationStore
from storage.portfolio_store_sqlite import SQLitePortfolioStore
from storage.repair_runbook_store_sqlite import SQLiteRepairRunbookStore
from services.runbooks.drift_repair_planner import RepairPolicy, build_repair_plan_from_drift
from services.reconciliation.symbol_mapping import build_symbol_rows
from services.os.app_paths import data_dir, ensure_dirs

ensure_dirs()
_DROOT = data_dir()

def now_ms() -> int:
    return int(time.time() * 1000)

@dataclass(frozen=True)
class ReconcileConfig:
    enabled: bool = True
    interval_sec: int = 30

    # drift tolerances
    cash_tolerance: float = 5.0          # quote currency units
    asset_qty_tolerance: float = 0.0001  # base units

    # stores
    recon_db_path: str = str(_DROOT / "reconciliation.sqlite")
    portfolio_db_path: str = str(_DROOT / "portfolio.sqlite")
    runbook_db_path: str = str(_DROOT / "repair_runbooks.sqlite")

    # DRAFT runbooks
    auto_draft_runbook_on_critical: bool = True

    # Cash reporting: list quote currencies to include in drift report
    quote_ccys: Optional[List[str]] = None  # e.g. ["USD","USDT"]

def _extract_total_balances(fetch_balance_result: Dict[str, Any]) -> Dict[str, float]:
    total = fetch_balance_result.get("total")
    if isinstance(total, dict) and total:
        out = {}
        for k, v in total.items():
            try:
                out[str(k)] = float(v or 0.0)
            except Exception:
                pass
        return out
    free = fetch_balance_result.get("free") or {}
    used = fetch_balance_result.get("used") or {}
    out = {}
    keys = set(list(free.keys()) + list(used.keys()))
    for k in keys:
        try:
            out[str(k)] = float(free.get(k, 0.0) or 0.0) + float(used.get(k, 0.0) or 0.0)
        except Exception:
            pass
    return out

def _balance_for(totals: Dict[str, float], asset: str) -> float:
    key = str(asset or "").strip()
    if not key:
        return 0.0
    if key in totals:
        return float(totals.get(key, 0.0) or 0.0)
    up = key.upper()
    if up in totals:
        return float(totals.get(up, 0.0) or 0.0)
    low = key.lower()
    if low in totals:
        return float(totals.get(low, 0.0) or 0.0)
    for k, v in totals.items():
        if str(k).upper() == up:
            return float(v or 0.0)
    return 0.0


def _normalize_quote_ccys(primary_quote: str, cfg_quote_ccys: Optional[List[str]]) -> List[str]:
    primary = str(primary_quote or "USD").upper().strip() or "USD"
    raw = cfg_quote_ccys or [primary]
    out: List[str] = []
    seen: set[str] = set()

    def _append(v: str) -> None:
        q = str(v or "").upper().strip()
        if not q or q in seen:
            return
        seen.add(q)
        out.append(q)

    _append(primary)
    for q in raw:
        _append(str(q))
    return out


def default_reconcile_config() -> ReconcileConfig:
    ensure_dirs()
    droot = data_dir()
    return ReconcileConfig(
        recon_db_path=str(droot / "reconciliation.sqlite"),
        portfolio_db_path=str(droot / "portfolio.sqlite"),
        runbook_db_path=str(droot / "repair_runbooks.sqlite"),
    )

def severity_from(drift: Dict[str, Any], cash_tol: float, qty_tol: float) -> str:
    cash_primary = (drift.get("cash") or {}).get("primary") or {}
    if abs(float(cash_primary.get("abs_drift", 0.0) or 0.0)) > 3 * float(cash_tol):
        return "CRITICAL"
    for p in (drift.get("positions") or []):
        if abs(float(p.get("abs_drift", 0.0) or 0.0)) > 3 * float(qty_tol):
            return "CRITICAL"
    if abs(float(cash_primary.get("abs_drift", 0.0) or 0.0)) > float(cash_tol):
        return "WARN"
    for p in (drift.get("positions") or []):
        if abs(float(p.get("abs_drift", 0.0) or 0.0)) > float(qty_tol):
            return "WARN"
    return "OK"

async def fetch_balance(exchange_id: str, ex_obj) -> Dict[str, Any]:
    return await ex_obj.fetch_balance()

async def reconcile_once(*, exchange_id: str, ex_obj, cfg: ReconcileConfig, trading_cfg: Dict[str, Any]) -> Dict[str, Any]:
    recon = SQLiteReconciliationStore(path=cfg.recon_db_path)
    port = SQLitePortfolioStore(path=cfg.portfolio_db_path)
    runbooks = SQLiteRepairRunbookStore(path=cfg.runbook_db_path)

    ts = now_ms()
    bal_raw = await fetch_balance(exchange_id, ex_obj)
    totals = _extract_total_balances(bal_raw)

    # Determine quote currencies to report
    portfolio = trading_cfg.get("portfolio") or {}
    primary_quote = str(portfolio.get("quote_ccy") or "USD").upper().strip() or "USD"
    quote_ccys = _normalize_quote_ccys(primary_quote, cfg.quote_ccys)

    recon.insert_balance_snapshot(ts, exchange_id, primary_quote, {"totals": totals, "quote_ccys": quote_ccys})

    # Cash drift: compare all configured quote currencies against internal per-quote ledger (v2).
    # Keep legacy single-row fallback for primary quote to preserve backward compatibility.
    def _internal_cash_for_quote(quote_ccy: str) -> float:
        row = port.get_cash(exchange_id, quote_ccy)
        if row:
            return float(row["cash"])
        if quote_ccy == primary_quote:
            legacy = port.get_cash(exchange_id)
            return float(legacy["cash"]) if legacy else 0.0
        return 0.0

    cash_report = {"primary": {}, "others": []}

    internal_primary = _internal_cash_for_quote(primary_quote)
    exch_primary = _balance_for(totals, primary_quote)
    cash_report["primary"] = {
        "quote_ccy": primary_quote,
        "exchange_cash": exch_primary,
        "internal_cash": internal_primary,
        "abs_drift": exch_primary - internal_primary,
    }
    for q in quote_ccys:
        if q == primary_quote:
            continue
        exch_cash = _balance_for(totals, q)
        internal_cash = _internal_cash_for_quote(q)
        cash_report["others"].append(
            {
                "quote_ccy": q,
                "exchange_cash": exch_cash,
                "internal_cash": internal_cash,
                "abs_drift": exch_cash - internal_cash,
            }
        )

    # Positions drift: deterministic from symbol_maps (canonical->exchange symbol) + internal position row keyed by exchange_symbol
    rows = build_symbol_rows(exchange_id, trading_cfg)
    internal_positions = {p["symbol"]: p for p in port.list_positions(exchange=exchange_id)}

    pos_drifts: List[Dict[str, Any]] = []
    tracked_bases = set()

    for r in rows:
        tracked_bases.add(r.base)
        exch_qty = _balance_for(totals, r.base)

        internal_pos = internal_positions.get(r.exchange_symbol)
        internal_qty = float(internal_pos["qty"]) if internal_pos else 0.0

        d = exch_qty - internal_qty
        pos_drifts.append({
            "canonical_symbol": r.canonical_symbol,
            "exchange_symbol": r.exchange_symbol,
            "base": r.base,
            "quote": r.quote,
            "exchange_qty": exch_qty,
            "internal_qty": internal_qty,
            "abs_drift": d,
        })

    # Untracked assets held on exchange (informational)
    untracked_assets = []
    for asset, qty in totals.items():
        try:
            qv = float(qty or 0.0)
        except Exception:
            continue
        if qv == 0:
            continue
        if asset == primary_quote:
            continue
        if asset in tracked_bases:
            continue
        untracked_assets.append({"asset": asset, "qty": qv})
    untracked_assets = sorted(untracked_assets, key=lambda x: abs(float(x["qty"])), reverse=True)[:50]

    drift = {
        "ts_ms": ts,
        "exchange": exchange_id,
        "cash": cash_report,
        "positions": pos_drifts,
        "untracked_assets": untracked_assets,
        "mapping_note": "positions drift is computed per configured symbols + symbol_maps; no guessing is used",
    }

    sev = severity_from(drift, cfg.cash_tolerance, cfg.asset_qty_tolerance)
    summary = f"severity={sev} cash_drift={float(cash_report['primary']['abs_drift']):.4f} {primary_quote} mapped_symbols={len(pos_drifts)}"
    recon.insert_drift_report(ts, exchange_id, sev, summary, drift)

    plan_id = None
    if sev == "CRITICAL" and cfg.auto_draft_runbook_on_critical:
        policy = RepairPolicy(
            allowed_actions=["CANCEL_OPEN_ORDERS", "SYNC_CASH", "SYNC_POSITION"],
            default_actions=["CANCEL_OPEN_ORDERS"],
            max_flatten_symbols=0,
        )
        plan = build_repair_plan_from_drift(exchange_id, drift, policy)
        runbooks.create_plan_sync(plan_id=plan["plan_id"], exchange=plan["exchange"], plan_hash=plan["plan_hash"],
                                  summary=plan["summary"], actions=plan["actions"], meta=plan.get("meta"))
        plan_id = plan["plan_id"]

    return {"ok": True, "severity": sev, "summary": summary, "plan_id": plan_id}
