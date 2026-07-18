from __future__ import annotations

import math
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.os.app_paths import data_dir
from services.control.paper_promotion_policy import (
    before_policy_cohort,
    record_timestamp,
    resolve_paper_promotion_policy,
)
from services.strategies.crypto_edge_context import (
    DEFAULT_CONTEXT_SOURCE,
    DEFAULT_FUNDING_MAX_AGE_SEC,
)

_CONTEXT_STRATEGIES = {
    "funding_extreme",
    "open_interest_shift",
    "order_book_imbalance",
}


def _expected_contract(config: dict[str, Any]) -> dict[str, Any]:
    strategy = config.get("strategy") if isinstance(config.get("strategy"), dict) else {}
    signal = strategy.get("signal") if isinstance(strategy.get("signal"), dict) else {}
    timeframe = str(signal.get("timeframe") or "").strip().lower()
    configured_source = str(config.get("signal_source") or "").strip().lower()
    suffix = f"_{timeframe}" if timeframe else ""
    source = (
        configured_source[: -len(suffix)]
        if suffix and configured_source.endswith(suffix)
        else configured_source
    )
    expected: dict[str, Any] = {
        "market_data_source": source,
        "ohlcv_timeframe": timeframe,
        "ohlcv_venue": str(strategy.get("venue") or "").strip().lower(),
        "ohlcv_symbol": str(strategy.get("symbol") or "").strip().upper(),
    }
    context = _expected_context_contract(config, strategy)
    if context:
        expected["context"] = context
    return expected


def _context_config_value(
    config: dict[str, Any],
    strategy: dict[str, Any],
    key: str,
    default: Any = "",
) -> Any:
    if key in config:
        return config.get(key)
    if key in strategy:
        return strategy.get(key)
    return default


def _expected_context_contract(
    config: dict[str, Any],
    strategy: dict[str, Any],
) -> dict[str, Any]:
    strategy_name = str(strategy.get("name") or config.get("strategy_id") or "").strip().lower()
    explicit_context_keys = {
        "strategy_context_source",
        "strategy_context_symbol",
        "strategy_context_venue",
        "strategy_context_max_age_sec",
    }
    requires_context = strategy_name in _CONTEXT_STRATEGIES or any(
        key in config or key in strategy for key in explicit_context_keys
    )
    if not requires_context:
        return {}

    max_age = _positive_float(
        _context_config_value(
            config,
            strategy,
            "strategy_context_max_age_sec",
            DEFAULT_FUNDING_MAX_AGE_SEC,
        ),
        default=DEFAULT_FUNDING_MAX_AGE_SEC,
    )
    return {
        "source": str(
            _context_config_value(
                config,
                strategy,
                "strategy_context_source",
                DEFAULT_CONTEXT_SOURCE,
            )
            or DEFAULT_CONTEXT_SOURCE
        ).strip()
        or DEFAULT_CONTEXT_SOURCE,
        "symbol": str(
            _context_config_value(
                config,
                strategy,
                "strategy_context_symbol",
                strategy.get("symbol") or "",
            )
            or ""
        ).strip().upper(),
        "venue": str(
            _context_config_value(
                config,
                strategy,
                "strategy_context_venue",
                strategy.get("venue") or "",
            )
            or ""
        ).strip().lower(),
        "max_age_sec": max_age,
    }


def _positive_float(value: Any, *, default: float) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    if not math.isfinite(out) or out <= 0.0:
        return float(default)
    return out


def _explicit_non_sample(value: Any) -> bool:
    if value is False or value == 0:
        return True
    return str(value).strip().lower() in {"false", "no", "off"}


def _record_ts(fill: dict[str, Any]) -> str:
    return str(fill.get("timestamp") or fill.get("_logged_at") or "").strip()


def _record_date(fill: dict[str, Any]) -> str:
    return _record_ts(fill)[:10]


def _parse_record_ts(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except Exception:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _explicit_true(value: Any) -> bool:
    if value is True or value == 1:
        return True
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _fill_rejection_reasons(fill: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    order_id = str(fill.get("order_id") or "").strip()
    if not order_id:
        reasons.append("missing_order_id")

    source = str(fill.get("market_data_source") or "").strip().lower()
    if not source:
        reasons.append("missing_market_data_source")
    elif expected["market_data_source"] and source != expected["market_data_source"]:
        reasons.append("market_data_source_mismatch")

    if "ohlcv_sample_mode" not in fill:
        reasons.append("missing_ohlcv_sample_mode")
    elif not _explicit_non_sample(fill.get("ohlcv_sample_mode")):
        reasons.append("sample_mode")

    timeframe = str(fill.get("ohlcv_timeframe") or "").strip().lower()
    if not timeframe:
        reasons.append("missing_ohlcv_timeframe")
    elif expected["ohlcv_timeframe"] and timeframe != expected["ohlcv_timeframe"]:
        reasons.append("ohlcv_timeframe_mismatch")

    venue = str(fill.get("ohlcv_venue") or "").strip().lower()
    if not venue:
        reasons.append("missing_ohlcv_venue")
    elif expected["ohlcv_venue"] and venue != expected["ohlcv_venue"]:
        reasons.append("ohlcv_venue_mismatch")

    symbol = str(fill.get("ohlcv_symbol") or "").strip().upper()
    if not symbol:
        reasons.append("missing_ohlcv_symbol")
    elif expected["ohlcv_symbol"] and symbol != expected["ohlcv_symbol"]:
        reasons.append("ohlcv_symbol_mismatch")

    context_expected = expected.get("context")
    if isinstance(context_expected, dict) and context_expected:
        reasons.extend(_context_rejection_reasons(fill, context_expected))

    return reasons


def _context_rejection_reasons(fill: dict[str, Any], expected: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    if "strategy_context_ok" not in fill:
        reasons.append("missing_strategy_context_ok")
    elif not _explicit_true(fill.get("strategy_context_ok")):
        reasons.append("strategy_context_not_ready")

    reason = str(fill.get("strategy_context_reason") or "").strip()
    if not reason:
        reasons.append("missing_strategy_context_reason")
    elif reason != "funding_context_ready":
        reasons.append("strategy_context_not_ready")

    source = str(fill.get("strategy_context_source") or "").strip()
    if not source:
        reasons.append("missing_strategy_context_source")
    elif source != str(expected.get("source") or "").strip():
        reasons.append("strategy_context_source_mismatch")

    symbol = str(fill.get("strategy_context_symbol") or "").strip().upper()
    if not symbol:
        reasons.append("missing_strategy_context_symbol")
    elif symbol != str(expected.get("symbol") or "").strip().upper():
        reasons.append("strategy_context_symbol_mismatch")

    venue = str(fill.get("strategy_context_venue") or "").strip().lower()
    if not venue:
        reasons.append("missing_strategy_context_venue")
    elif venue != str(expected.get("venue") or "").strip().lower():
        reasons.append("strategy_context_venue_mismatch")

    if not str(fill.get("strategy_context_snapshot_id") or "").strip():
        reasons.append("missing_strategy_context_snapshot_id")

    capture_ts = _parse_record_ts(fill.get("strategy_context_capture_ts"))
    if capture_ts is None:
        reasons.append("missing_strategy_context_capture_ts")
        return reasons

    fill_ts = _parse_record_ts(_record_ts(fill))
    if fill_ts is None:
        reasons.append("invalid_fill_timestamp_for_context")
        return reasons
    age_sec = (fill_ts - capture_ts).total_seconds()
    if age_sec < -60.0:
        reasons.append("strategy_context_capture_after_fill")
        return reasons
    if age_sec > float(expected.get("max_age_sec") or DEFAULT_FUNDING_MAX_AGE_SEC):
        reasons.append("strategy_context_stale")
    return reasons


def _journal_rows(path: Path, order_ids: set[str]) -> tuple[list[dict[str, Any]], str | None]:
    if not path.exists():
        return [], "journal_missing"
    if not order_ids:
        return [], None

    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    try:
        table = con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='journal_fills'"
        ).fetchone()
        if not table:
            return [], "journal_fills_table_missing"
        columns = {
            str(row["name"])
            for row in con.execute("PRAGMA table_info(journal_fills)").fetchall()
        }
        required = {
            "fill_id",
            "journal_ts",
            "order_id",
            "fill_ts",
            "venue",
            "symbol",
            "side",
            "qty",
            "price",
            "fee",
            "fee_currency",
        }
        if not required.issubset(columns):
            return [], "journal_schema_missing_order_provenance_link"

        placeholders = ",".join("?" for _ in order_ids)
        rows = con.execute(
            "SELECT fill_id, journal_ts, order_id, fill_ts, venue, symbol, side, "
            "qty, price, fee, fee_currency FROM journal_fills "
            f"WHERE order_id IN ({placeholders}) ORDER BY fill_ts ASC",
            sorted(order_ids),
        ).fetchall()
        return [dict(row) for row in rows], None
    except Exception as exc:
        return [], f"journal_read_error:{type(exc).__name__}"
    finally:
        con.close()


def _completed_round_trip_order_ids(fills: list[dict[str, Any]]) -> tuple[set[str], int, list[str]]:
    completed_order_ids: set[str] = set()
    cycle_order_ids: set[str] = set()
    cycle_qualified = True
    open_qty = 0.0
    completed_round_trips = 0
    completed_close_timestamps: list[str] = []
    ordered = sorted(
        fills,
        key=_record_ts,
    )
    for fill in ordered:
        side = str(fill.get("side") or "").strip().lower()
        order_id = str(fill.get("order_id") or "").strip()
        try:
            qty = float(fill.get("size") or fill.get("qty") or 0.0)
        except (TypeError, ValueError):
            qty = 0.0
        if not order_id or qty <= 0.0:
            continue
        if side == "buy":
            if open_qty <= 1e-12:
                cycle_order_ids = set()
                cycle_qualified = True
            cycle_order_ids.add(order_id)
            cycle_qualified = cycle_qualified and not bool(
                fill.get("_promotion_rejection_reasons")
            )
            open_qty += qty
        elif side == "sell" and open_qty > 1e-12:
            cycle_order_ids.add(order_id)
            cycle_qualified = cycle_qualified and not bool(
                fill.get("_promotion_rejection_reasons")
            )
            open_qty = max(0.0, open_qty - qty)
            if open_qty <= 1e-12:
                if cycle_qualified:
                    completed_order_ids.update(cycle_order_ids)
                    completed_round_trips += 1
                    if close_ts := _record_ts(fill):
                        completed_close_timestamps.append(close_ts)
                cycle_order_ids = set()
                cycle_qualified = True
    return completed_order_ids, completed_round_trips, completed_close_timestamps


def _qualified_metrics(journal_rows: list[dict[str, Any]]) -> dict[str, Any]:
    analytics = fifo_pnl_from_fills(journal_rows)
    summary = dict(analytics.get("summary") or {})
    closed = [
        dict(row)
        for row in list(analytics.get("closed_trades") or [])
        if isinstance(row, dict)
    ]
    wins = [row for row in closed if float(row.get("net_pnl") or 0.0) > 0.0]
    losses = [row for row in closed if float(row.get("net_pnl") or 0.0) < 0.0]
    closed_count = len(closed)
    net_realized = float(summary.get("net_realized_pnl") or 0.0)
    return {
        "fills": len(journal_rows),
        "closed_trades": closed_count,
        "win_rate": (len(wins) / closed_count) if closed_count else None,
        "avg_win": (
            sum(float(row.get("net_pnl") or 0.0) for row in wins) / len(wins)
            if wins
            else None
        ),
        "avg_loss": (
            sum(float(row.get("net_pnl") or 0.0) for row in losses) / len(losses)
            if losses
            else None
        ),
        "avg_win_return_pct": (
            sum(float(row.get("return_pct") or 0.0) for row in wins) / len(wins)
            if wins
            else None
        ),
        "avg_loss_return_pct": (
            sum(float(row.get("return_pct") or 0.0) for row in losses) / len(losses)
            if losses
            else None
        ),
        "expectancy_return_pct": (
            sum(float(row.get("return_pct") or 0.0) for row in closed) / closed_count
            if closed_count
            else None
        ),
        "net_realized_pnl": net_realized,
        "expectancy_per_closed_trade": (
            net_realized / closed_count if closed_count else None
        ),
        "latest_fill_ts": (
            str(journal_rows[-1].get("fill_ts") or journal_rows[-1].get("journal_ts") or "")
            or None
            if journal_rows
            else None
        ),
    }


def qualify_paper_history(
    *,
    evidence_fills: list[dict[str, Any]],
    config: dict[str, Any],
    journal_path: str = "",
) -> dict[str, Any]:
    """Return promotion metrics using only fills with explicit matching provenance."""
    expected = _expected_contract(config)
    policy = resolve_paper_promotion_policy(config)
    annotated_fills: list[dict[str, Any]] = []
    qualified_fill_timestamps: list[str] = []
    provenance_qualified_fill_count = 0
    rejection_counts: Counter[str] = Counter()
    unqualified_date_counts: Counter[str] = Counter()
    excluded_before_cohort_date_counts: Counter[str] = Counter()
    unqualified_fills = 0
    excluded_before_cohort_fills = 0

    for raw_fill in list(evidence_fills or []):
        fill = dict(raw_fill)
        if policy.cohort_start_dt is not None:
            ts = record_timestamp(fill)
            if ts is None:
                reasons = ["invalid_timestamp_for_cohort"]
            elif before_policy_cohort(fill, policy):
                excluded_before_cohort_fills += 1
                if date := _record_date(fill):
                    excluded_before_cohort_date_counts[date] += 1
                continue
            else:
                reasons = _fill_rejection_reasons(fill, expected)
        else:
            reasons = _fill_rejection_reasons(fill, expected)
        fill["_promotion_rejection_reasons"] = reasons
        annotated_fills.append(fill)
        if reasons:
            unqualified_fills += 1
            rejection_counts.update(reasons)
            if date := _record_date(fill):
                unqualified_date_counts[date] += 1
            continue
        provenance_qualified_fill_count += 1
        if ts := _record_ts(fill):
            qualified_fill_timestamps.append(ts)

    (
        qualified_order_ids,
        completed_evidence_round_trips,
        completed_close_timestamps,
    ) = _completed_round_trip_order_ids(
        annotated_fills
    )

    path = (
        Path(journal_path).expanduser().resolve()
        if journal_path
        else (data_dir() / "trade_journal.sqlite").resolve()
    )
    journal_rows, journal_error = _journal_rows(path, qualified_order_ids)
    journal_order_ids = {
        str(row.get("order_id") or "").strip()
        for row in journal_rows
        if str(row.get("order_id") or "").strip()
    }
    missing_journal_order_ids = sorted(qualified_order_ids - journal_order_ids)
    metrics = _qualified_metrics(journal_rows)

    return {
        "ok": journal_error is None,
        "status": "available" if journal_error is None else "error",
        "source": "jsonl_provenance+trade_journal_sqlite",
        "journal_path": str(path),
        **metrics,
        "qualification": {
            "expected": expected,
            "policy": policy.to_dict(),
            "evidence_fills": len(evidence_fills or []),
            "cohort_evidence_fills": len(annotated_fills),
            "excluded_before_cohort_evidence_fills": excluded_before_cohort_fills,
            "excluded_before_cohort_date_counts": dict(
                sorted(excluded_before_cohort_date_counts.items())
            ),
            "provenance_qualified_evidence_fills": provenance_qualified_fill_count,
            "qualified_evidence_fills": len(qualified_order_ids),
            "completed_evidence_round_trips": completed_evidence_round_trips,
            "incomplete_qualified_evidence_fills": (
                provenance_qualified_fill_count - len(qualified_order_ids)
            ),
            "first_provenance_qualified_fill_ts": (
                min(qualified_fill_timestamps) if qualified_fill_timestamps else None
            ),
            "latest_provenance_qualified_fill_ts": (
                max(qualified_fill_timestamps) if qualified_fill_timestamps else None
            ),
            "first_completed_qualified_round_trip_close_ts": (
                min(completed_close_timestamps) if completed_close_timestamps else None
            ),
            "latest_completed_qualified_round_trip_close_ts": (
                max(completed_close_timestamps) if completed_close_timestamps else None
            ),
            "unqualified_evidence_fills": unqualified_fills,
            "unqualified_reason_counts": dict(sorted(rejection_counts.items())),
            "unqualified_date_counts": dict(sorted(unqualified_date_counts.items())),
            "qualified_order_ids": sorted(qualified_order_ids),
            "missing_journal_order_ids": missing_journal_order_ids,
            "journal_error": journal_error,
            "rule": "entry and exit fills must each carry the configured non-sample provenance",
        },
    }
