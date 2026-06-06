from __future__ import annotations

import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.os.app_paths import data_dir


def _expected_contract(config: dict[str, Any]) -> dict[str, str]:
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
    return {
        "market_data_source": source,
        "ohlcv_timeframe": timeframe,
        "ohlcv_venue": str(strategy.get("venue") or "").strip().lower(),
        "ohlcv_symbol": str(strategy.get("symbol") or "").strip().upper(),
    }


def _explicit_non_sample(value: Any) -> bool:
    if value is False or value == 0:
        return True
    return str(value).strip().lower() in {"false", "no", "off"}


def _fill_rejection_reasons(fill: dict[str, Any], expected: dict[str, str]) -> list[str]:
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


def _completed_round_trip_order_ids(fills: list[dict[str, Any]]) -> tuple[set[str], int]:
    completed_order_ids: set[str] = set()
    cycle_order_ids: set[str] = set()
    cycle_qualified = True
    open_qty = 0.0
    completed_round_trips = 0
    ordered = sorted(
        fills,
        key=lambda row: str(row.get("timestamp") or row.get("_logged_at") or ""),
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
                cycle_order_ids = set()
                cycle_qualified = True
    return completed_order_ids, completed_round_trips


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
    annotated_fills: list[dict[str, Any]] = []
    provenance_qualified_fill_count = 0
    rejection_counts: Counter[str] = Counter()
    unqualified_fills = 0

    for raw_fill in list(evidence_fills or []):
        fill = dict(raw_fill)
        reasons = _fill_rejection_reasons(fill, expected)
        fill["_promotion_rejection_reasons"] = reasons
        annotated_fills.append(fill)
        if reasons:
            unqualified_fills += 1
            rejection_counts.update(reasons)
            continue
        provenance_qualified_fill_count += 1

    qualified_order_ids, completed_evidence_round_trips = _completed_round_trip_order_ids(
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
            "evidence_fills": len(evidence_fills or []),
            "provenance_qualified_evidence_fills": provenance_qualified_fill_count,
            "qualified_evidence_fills": len(qualified_order_ids),
            "completed_evidence_round_trips": completed_evidence_round_trips,
            "incomplete_qualified_evidence_fills": (
                provenance_qualified_fill_count - len(qualified_order_ids)
            ),
            "unqualified_evidence_fills": unqualified_fills,
            "unqualified_reason_counts": dict(sorted(rejection_counts.items())),
            "qualified_order_ids": sorted(qualified_order_ids),
            "missing_journal_order_ids": missing_journal_order_ids,
            "journal_error": journal_error,
            "rule": "entry and exit fills must each carry the configured non-sample provenance",
        },
    }
