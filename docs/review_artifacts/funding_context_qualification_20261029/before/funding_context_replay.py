from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.strategies.strategy_registry import compute_signal
from storage.crypto_edge_store_sqlite import CryptoEdgeStoreSQLite


ARTIFACT_TYPE = "funding_context_signal_replay_v1"
STRATEGY = "funding_extreme"


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


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


def _safe_ts(value: Any) -> str:
    raw = str(value or "").strip()
    if not raw:
        return ""
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return raw
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _canonical_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows:
        out.append(
            {
                "capture_ts": _safe_ts(row.get("capture_ts")),
                "funding_rate": _finite_float(row.get("funding_rate"), name="funding_rate"),
                "interval_hours": _finite_float(row.get("interval_hours", 8.0), name="interval_hours"),
                "snapshot_id": str(row.get("snapshot_id") or ""),
                "source": str(row.get("source") or ""),
                "symbol": _canon_symbol(row.get("symbol")),
                "venue": _canon_venue(row.get("venue")),
            }
        )
    out.sort(key=lambda item: (str(item["capture_ts"]), str(item["snapshot_id"])))
    return out


def _dataset_hash(rows: list[dict[str, Any]]) -> str:
    payload = json.dumps(rows, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _strategy_cfg(cfg: dict[str, Any] | None) -> dict[str, Any]:
    out = dict(cfg or {})
    strategy = out.get("strategy")
    if not isinstance(strategy, dict):
        strategy = {}
    strategy = dict(strategy)
    strategy.setdefault("name", STRATEGY)
    out["strategy"] = strategy
    return out


def run_funding_context_replay(
    *,
    cfg: dict[str, Any] | None = None,
    db_path: str | Path | None = None,
    source: str = "live_public",
    venue: str = "okx",
    symbol: str = "BTC/USDT:USDT",
    limit: int = 500,
    min_rows: int = 1,
) -> dict[str, Any]:
    """
    Research-only signal replay over stored funding snapshots.

    This intentionally does not compute PnL or expectancy. It proves that
    stored crypto-edge funding rows can drive deterministic funding_extreme
    signal artifacts with dataset provenance.
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
            "row_count": 0,
            "signals": [],
        }

    store = CryptoEdgeStoreSQLite(path=str(db_path or ""))
    raw_rows = store.recent_funding_rows_for_source(source=str(source or ""), limit=int(max(limit, 1)))
    requested_symbol = _canon_symbol(symbol)
    requested_venue = _canon_venue(venue)
    matched = [
        row
        for row in raw_rows
        if _canon_symbol(row.get("symbol")) == requested_symbol and _canon_venue(row.get("venue")) == requested_venue
    ]
    rows = _canonical_rows(matched)
    dataset_hash = _dataset_hash(rows)

    signals: list[dict[str, Any]] = []
    action_counts: Counter[str] = Counter()
    reason_counts: Counter[str] = Counter()
    for row in rows:
        funding_rate_pct = float(row["funding_rate"]) * 100.0
        signal = compute_signal(
            cfg=resolved_cfg,
            symbol=requested_symbol,
            ohlcv=[],
            context={
                "funding": {
                    "funding_rate": row["funding_rate"],
                    "funding_rate_pct": funding_rate_pct,
                }
            },
        )
        action = str(signal.get("action") or "hold")
        reason = str(signal.get("reason") or "")
        action_counts[action] += 1
        reason_counts[reason] += 1
        signals.append(
            {
                "capture_ts": row["capture_ts"],
                "snapshot_id": row["snapshot_id"],
                "funding_rate": row["funding_rate"],
                "funding_rate_pct": round(funding_rate_pct, 8),
                "action": action,
                "reason": reason,
                "ok": bool(signal.get("ok")),
            }
        )

    ok = len(rows) >= int(max(min_rows, 1))
    return {
        "ok": bool(ok),
        "reason": "ok" if ok else "insufficient_funding_rows",
        "research_only": True,
        "artifact_type": ARTIFACT_TYPE,
        "generated_at": _utc_now(),
        "strategy": STRATEGY,
        "source": str(source or ""),
        "venue": requested_venue,
        "symbol": requested_symbol,
        "limit": int(max(limit, 1)),
        "min_rows": int(max(min_rows, 1)),
        "row_count": int(len(rows)),
        "first_capture_ts": rows[0]["capture_ts"] if rows else None,
        "last_capture_ts": rows[-1]["capture_ts"] if rows else None,
        "dataset_hash": dataset_hash,
        "dataset": {
            "source": "crypto_edge_funding_snapshots",
            "store_path": str(db_path or ""),
            "row_count": int(len(rows)),
            "hash": dataset_hash,
        },
        "action_counts": dict(sorted(action_counts.items())),
        "reason_counts": dict(sorted(reason_counts.items())),
        "signals": signals,
        "limitations": [
            "signal_distribution_only",
            "no_price_path_join",
            "no_pnl_or_expectancy",
            "not_promotion_evidence",
        ],
    }
