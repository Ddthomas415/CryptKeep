from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_left
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.backtest.ohlcv_archive import load_archived_ohlcv, normalize_ohlcv_rows
from services.execution.fill_model import apply_fee_slippage
from services.strategies.strategy_registry import compute_signal
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


ARTIFACT_TYPE = "funding_context_price_join_v1"
STRATEGY = "funding_extreme"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_ts_ms(value: Any) -> int | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        if raw.isdigit():
            num = int(raw)
            return num if num > 10_000_000_000 else num * 1000
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.astimezone(timezone.utc).timestamp() * 1000)


def _iso_ms(ts_ms: int | None) -> str | None:
    if ts_ms is None:
        return None
    return datetime.fromtimestamp(int(ts_ms) / 1000.0, tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _finite_float(value: Any, *, name: str) -> float:
    try:
        out = float(value)
    except Exception as exc:
        raise ValueError(f"invalid_numeric:{name}") from exc
    if not math.isfinite(out):
        raise ValueError(f"invalid_numeric:{name}")
    return out


def _canon_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def _canon_venue(value: Any) -> str:
    return str(value or "").strip().lower()


def _sha(payload: Any) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _funding_rows(
    *,
    db_path: str | Path | None,
    source: str,
    venue: str,
    symbol: str,
    limit: int,
) -> list[dict[str, Any]]:
    store = CryptoEdgeStoreSQLite(path=str(db_path or ""))
    raw_rows = store.recent_funding_rows_for_source(source=str(source or ""), limit=int(max(limit, 1)))
    wanted_symbol = _canon_symbol(symbol)
    wanted_venue = _canon_venue(venue)
    out: list[dict[str, Any]] = []
    for row in raw_rows:
        ts_ms = _parse_ts_ms(row.get("capture_ts"))
        if ts_ms is None:
            continue
        if _canon_symbol(row.get("symbol")) != wanted_symbol or _canon_venue(row.get("venue")) != wanted_venue:
            continue
        out.append(
            {
                "capture_ts": _iso_ms(ts_ms),
                "capture_ts_ms": int(ts_ms),
                "funding_rate": _finite_float(row.get("funding_rate"), name="funding_rate"),
                "interval_hours": _finite_float(row.get("interval_hours", 8.0), name="interval_hours"),
                "snapshot_id": str(row.get("snapshot_id") or ""),
                "source": str(row.get("source") or ""),
                "symbol": _canon_symbol(row.get("symbol")),
                "venue": _canon_venue(row.get("venue")),
            }
        )
    out.sort(key=lambda item: (int(item["capture_ts_ms"]), str(item["snapshot_id"])))
    return out


def _strategy_cfg(cfg: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(cfg or {})
    strategy = out.get("strategy")
    if not isinstance(strategy, dict):
        strategy = {}
    strategy = dict(strategy)
    strategy.setdefault("name", STRATEGY)
    out["strategy"] = strategy
    return out


def _round_trip_return_pct(
    *,
    action: str,
    entry_px: float,
    exit_px: float,
    fee_bps: float,
    slippage_bps: float,
) -> float | None:
    if entry_px <= 0.0 or exit_px <= 0.0:
        return None
    side = str(action or "").lower().strip()
    if side not in {"buy", "sell"}:
        return None
    if side == "buy":
        entry = apply_fee_slippage(mid_px=entry_px, side="buy", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        exit_fill = apply_fee_slippage(mid_px=exit_px, side="sell", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        basis = entry.notional + entry.fee
        profit = (exit_fill.notional - exit_fill.fee) - basis
    else:
        entry = apply_fee_slippage(mid_px=entry_px, side="sell", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        exit_fill = apply_fee_slippage(mid_px=exit_px, side="buy", qty=1.0, fee_bps=fee_bps, slippage_bps=slippage_bps)
        basis = entry.notional + entry.fee
        profit = (entry.notional - entry.fee) - (exit_fill.notional + exit_fill.fee)
    if basis <= 0.0:
        return None
    return float((profit / basis) * 100.0)


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    actionable = [row for row in rows if row.get("net_forward_return_pct") is not None]
    wins = [row for row in actionable if float(row.get("net_forward_return_pct") or 0.0) > 0.0]
    avg = sum(float(row["net_forward_return_pct"]) for row in actionable) / len(actionable) if actionable else None
    return {
        "joined_rows": int(len(rows)),
        "actionable_rows": int(len(actionable)),
        "positive_actionable_rows": int(len(wins)),
        "positive_actionable_ratio": None if not actionable else float(len(wins) / len(actionable)),
        "avg_net_forward_return_pct": None if avg is None else float(avg),
    }


def run_funding_context_price_join(
    *,
    cfg: dict[str, Any] | None = None,
    edge_db_path: str | Path | None = None,
    archive_db_path: str | Path | None = None,
    context_source: str = "live_public",
    context_venue: str = "okx",
    context_symbol: str = "BTC/USDT:USDT",
    price_venue: str = "okx",
    price_symbol: str = "BTC/USDT",
    timeframe: str = "5m",
    funding_limit: int = 500,
    ohlcv_limit: int = 500,
    horizon_bars: int = 1,
    min_joined_rows: int = 1,
    fee_bps: float = 10.0,
    slippage_bps: float = 5.0,
) -> dict[str, Any]:
    """
    Research-only forward-return join between funding context and OHLCV archive.

    This is descriptive. It does not simulate portfolio state, position sizing,
    campaign behavior, or promotion eligibility.
    """
    resolved_cfg = _strategy_cfg(cfg)
    strategy_name = str(((resolved_cfg.get("strategy") or {}).get("name")) or "").strip()
    if strategy_name != STRATEGY:
        return {
            "ok": False,
            "reason": "unsupported_strategy",
            "research_only": True,
            "artifact_type": ARTIFACT_TYPE,
            "strategy": strategy_name,
            "expected_strategy": STRATEGY,
            "joined_rows": 0,
            "rows": [],
        }

    funding_rows = _funding_rows(
        db_path=edge_db_path,
        source=context_source,
        venue=context_venue,
        symbol=context_symbol,
        limit=funding_limit,
    )
    loaded = load_archived_ohlcv(
        price_venue,
        price_symbol,
        timeframe=str(timeframe),
        limit=int(max(ohlcv_limit, 1)),
        db_path=archive_db_path,
    )
    ohlcv_rows = normalize_ohlcv_rows(list(loaded.get("rows") or []))
    if not (loaded.get("ok") and loaded.get("complete")):
        return {
            "ok": False,
            "reason": str(loaded.get("reason") or "archive_unavailable"),
            "research_only": True,
            "artifact_type": ARTIFACT_TYPE,
            "strategy": STRATEGY,
            "funding_row_count": int(len(funding_rows)),
            "joined_rows": 0,
            "archive": {k: v for k, v in dict(loaded).items() if k != "rows"},
            "rows": [],
            "limitations": ["archive_required", "not_promotion_evidence"],
        }

    timestamps = [int(row[0]) for row in ohlcv_rows]
    horizon = int(max(horizon_bars, 1))
    joined: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    for funding in funding_rows:
        entry_idx = bisect_left(timestamps, int(funding["capture_ts_ms"]))
        exit_idx = entry_idx + horizon
        if entry_idx >= len(ohlcv_rows) or exit_idx >= len(ohlcv_rows):
            continue
        entry = ohlcv_rows[entry_idx]
        exit_row = ohlcv_rows[exit_idx]
        funding_rate_pct = float(funding["funding_rate"]) * 100.0
        signal = compute_signal(
            cfg=resolved_cfg,
            symbol=_canon_symbol(context_symbol),
            ohlcv=[],
            context={
                "funding": {
                    "funding_rate": funding["funding_rate"],
                    "funding_rate_pct": funding_rate_pct,
                }
            },
        )
        action = str(signal.get("action") or "hold").lower().strip()
        reason = str(signal.get("reason") or "")
        action_counts[action] += 1
        reason_counts[reason] += 1
        net_return = _round_trip_return_pct(
            action=action,
            entry_px=float(entry[4]),
            exit_px=float(exit_row[4]),
            fee_bps=float(fee_bps),
            slippage_bps=float(slippage_bps),
        )
        joined.append(
            {
                "capture_ts": funding["capture_ts"],
                "snapshot_id": funding["snapshot_id"],
                "funding_rate": funding["funding_rate"],
                "funding_rate_pct": round(funding_rate_pct, 8),
                "action": action,
                "reason": reason,
                "signal_ok": bool(signal.get("ok")),
                "entry_ts": _iso_ms(int(entry[0])),
                "exit_ts": _iso_ms(int(exit_row[0])),
                "entry_close": float(entry[4]),
                "exit_close": float(exit_row[4]),
                "horizon_bars": int(horizon),
                "net_forward_return_pct": None if net_return is None else round(float(net_return), 8),
            }
        )

    funding_hash = _sha(funding_rows)
    price_hash = str(loaded.get("dataset_hash") or _sha(ohlcv_rows))
    dataset_hash = _sha(
        {
            "artifact_type": ARTIFACT_TYPE,
            "funding_hash": funding_hash,
            "price_hash": price_hash,
            "params": {
                "context_source": context_source,
                "context_venue": _canon_venue(context_venue),
                "context_symbol": _canon_symbol(context_symbol),
                "price_venue": _canon_venue(price_venue),
                "price_symbol": _canon_symbol(price_symbol),
                "timeframe": str(timeframe),
                "horizon_bars": int(horizon),
                "fee_bps": float(fee_bps),
                "slippage_bps": float(slippage_bps),
            },
        }
    )
    ok = len(joined) >= int(max(min_joined_rows, 1))
    return {
        "ok": bool(ok),
        "reason": "ok" if ok else "insufficient_joined_rows",
        "research_only": True,
        "artifact_type": ARTIFACT_TYPE,
        "generated_at": _utc_now(),
        "strategy": STRATEGY,
        "context_source": str(context_source or ""),
        "context_venue": _canon_venue(context_venue),
        "context_symbol": _canon_symbol(context_symbol),
        "price_venue": _canon_venue(price_venue),
        "price_symbol": _canon_symbol(price_symbol),
        "timeframe": str(timeframe),
        "horizon_bars": int(horizon),
        "fee_bps": float(fee_bps),
        "slippage_bps": float(slippage_bps),
        "funding_row_count": int(len(funding_rows)),
        "price_row_count": int(len(ohlcv_rows)),
        "joined_rows": int(len(joined)),
        "dataset_hash": dataset_hash,
        "funding_dataset_hash": funding_hash,
        "price_dataset_hash": price_hash,
        "archive": {k: v for k, v in dict(loaded).items() if k != "rows"},
        "action_counts": dict(sorted(action_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "summary": _summary(joined),
        "rows": joined,
        "limitations": [
            "forward_return_only",
            "unit_size_no_position_state",
            "no_portfolio_pnl",
            "not_promotion_evidence",
        ],
    }
