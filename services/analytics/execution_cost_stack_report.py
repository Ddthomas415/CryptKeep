from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.os.app_paths import data_dir

REPORT_TYPE = "execution_cost_stack_report"
RECOMMENDATIONS = {
    "no_change",
    "research_more",
    "candidate_execution_policy_change",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe_float(value: Any) -> float | None:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return None
    return out if math.isfinite(out) else None


def _safe_stamp() -> str:
    return _now_iso().replace(":", "").replace("+", "Z")


def _canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _read_jsonl_dicts(path: Path) -> tuple[list[dict[str, Any]], int]:
    rows: list[dict[str, Any]] = []
    errors = 0
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows, 1
    for lineno, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            errors += 1
            continue
        if not isinstance(payload, dict):
            errors += 1
            continue
        row = dict(payload)
        row["_source_file"] = str(path)
        row["_source_line"] = lineno
        rows.append(row)
    return rows, errors


def _is_shadow_would_be_fill(row: dict[str, Any]) -> bool:
    return (
        str(row.get("record_subtype") or "") == "shadow_would_be_fill"
        or row.get("shadow_would_be_fill") is True
    )


def load_shadow_would_be_fills(evidence_root: Path | None = None) -> dict[str, Any]:
    root = (evidence_root or (data_dir() / "evidence")).resolve()
    rows: list[dict[str, Any]] = []
    ignored = 0
    parse_errors = 0
    files: list[dict[str, Any]] = []
    for path in sorted(root.glob("*/fill_*.jsonl")) if root.exists() else []:
        file_rows, file_errors = _read_jsonl_dicts(path)
        parse_errors += file_errors
        shadow_rows = [row for row in file_rows if _is_shadow_would_be_fill(row)]
        ignored += len(file_rows) - len(shadow_rows)
        rows.extend(shadow_rows)
        if shadow_rows or file_errors:
            try:
                file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            except OSError:
                file_hash = ""
            files.append(
                {
                    "path": str(path),
                    "sha256": file_hash,
                    "shadow_records": len(shadow_rows),
                    "parse_errors": file_errors,
                }
            )
    rows.sort(
        key=lambda row: (
            str(row.get("timestamp") or row.get("_logged_at") or ""),
            str(row.get("_source_file") or ""),
            int(row.get("_source_line") or 0),
        )
    )
    source_hash = _sha256_text(
        _canonical_json(
            [
                {k: v for k, v in row.items() if k not in {"_source_file", "_source_line"}}
                for row in rows
            ]
        )
    )
    return {
        "evidence_root": str(root),
        "records": rows,
        "ignored_non_shadow_records": ignored,
        "parse_errors": parse_errors,
        "source_files": files,
        "source_artifact_hash": source_hash,
    }


def _mid_from_record(row: dict[str, Any]) -> float | None:
    mid = _safe_float(row.get("reference_mid"))
    if mid is not None and mid > 0:
        return mid
    bid = _safe_float(row.get("bid"))
    ask = _safe_float(row.get("ask"))
    if bid is not None and ask is not None and bid > 0 and ask >= bid:
        return (bid + ask) / 2.0
    return None


def _spread_bps(row: dict[str, Any], mid: float) -> float | None:
    spread = _safe_float(row.get("spread_bps"))
    if spread is not None and spread >= 0:
        return spread
    bid = _safe_float(row.get("bid"))
    ask = _safe_float(row.get("ask"))
    if bid is None or ask is None or bid <= 0 or ask < bid or mid <= 0:
        return None
    return ((ask - bid) / mid) * 10000.0


def _side_cost_bps(*, side: str, price: float, mid: float) -> float:
    if side == "buy":
        return ((price - mid) / mid) * 10000.0
    return ((mid - price) / mid) * 10000.0


def _maker_resting_price(row: dict[str, Any], *, side: str) -> float | None:
    price = _safe_float(row.get("intended_limit_price"))
    if price is not None and price > 0:
        return price
    bid = _safe_float(row.get("bid"))
    ask = _safe_float(row.get("ask"))
    if side == "buy" and bid is not None and bid > 0:
        return bid
    if side == "sell" and ask is not None and ask > 0:
        return ask
    return None


def _path_prices(value: Any) -> list[dict[str, float]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, float]] = []
    for item in value:
        if isinstance(item, dict):
            point: dict[str, float] = {}
            for key in ("low", "high", "bid", "ask", "last", "price", "close"):
                parsed = _safe_float(item.get(key))
                if parsed is not None:
                    point[key] = parsed
            if point:
                out.append(point)
            continue
        parsed = _safe_float(item)
        if parsed is not None:
            out.append({"price": parsed})
    return out


def _maker_filled_by_path(*, side: str, maker_price: float, path: list[dict[str, float]]) -> bool | None:
    if not path or maker_price <= 0:
        return None
    if side == "buy":
        for point in path:
            low = point.get("low")
            bid = point.get("bid")
            price = point.get("price", point.get("last", point.get("close")))
            if any(v is not None and v <= maker_price for v in (low, bid, price)):
                return True
        return False
    for point in path:
        high = point.get("high")
        ask = point.get("ask")
        price = point.get("price", point.get("last", point.get("close")))
        if any(v is not None and v >= maker_price for v in (high, ask, price)):
            return True
    return False


def _avg(values: list[float]) -> float | None:
    vals = [float(v) for v in values if math.isfinite(float(v))]
    if not vals:
        return None
    return sum(vals) / len(vals)


def _round_or_none(value: float | None, digits: int = 6) -> float | None:
    if value is None or not math.isfinite(value):
        return None
    return round(float(value), digits)


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    taker_costs = [row["taker_cost_bps"] for row in rows]
    maker_costs = [row["maker_quote_cost_bps"] for row in rows if row.get("maker_quote_cost_bps") is not None]
    spreads = [row["spread_bps"] for row in rows if row.get("spread_bps") is not None]
    fees = [row["taker_fee_bps"] for row in rows]
    maker_flags = [row["maker_would_fill"] for row in rows if row.get("maker_would_fill") is not None]
    return {
        "records": len(rows),
        "avg_taker_cost_bps": _round_or_none(_avg(taker_costs)),
        "avg_taker_fee_bps": _round_or_none(_avg(fees)),
        "avg_spread_bps": _round_or_none(_avg(spreads)),
        "avg_maker_quote_cost_bps": _round_or_none(_avg(maker_costs)),
        "maker_fill_probability_estimate": (
            _round_or_none(sum(1 for flag in maker_flags if flag) / len(maker_flags), 6)
            if maker_flags
            else None
        ),
        "maker_fill_probability_records": len(maker_flags),
    }


def analyze_shadow_would_be_fills(
    records: list[dict[str, Any]],
    *,
    maker_fee_bps: float | None = None,
    min_records: int = 30,
    min_fill_probability_records: int | None = None,
    min_fill_probability: float = 0.6,
) -> dict[str, Any]:
    usable: list[dict[str, Any]] = []
    invalid_reasons: dict[str, int] = defaultdict(int)
    for row in records:
        side = str(row.get("side") or "").strip().lower()
        if side not in {"buy", "sell"}:
            invalid_reasons["invalid_side"] += 1
            continue
        mid = _mid_from_record(row)
        modeled = _safe_float(row.get("modeled_fill_price", row.get("fill_price")))
        qty = _safe_float(row.get("qty", row.get("size")))
        if mid is None or mid <= 0 or modeled is None or modeled <= 0 or qty is None or qty <= 0:
            invalid_reasons["invalid_price_or_qty"] += 1
            continue
        taker_fee = _safe_float(row.get("fee_bps"))
        if taker_fee is None:
            notional = _safe_float(row.get("notional"))
            fees_paid = _safe_float(row.get("fees_paid"))
            taker_fee = (fees_paid / notional) * 10000.0 if fees_paid is not None and notional else 0.0
        taker_slippage_cost = _side_cost_bps(side=side, price=modeled, mid=mid)
        taker_cost = taker_slippage_cost + taker_fee
        maker_price = _maker_resting_price(row, side=side)
        maker_quote_cost: float | None = None
        maker_fill: bool | None = None
        if maker_price is not None and maker_price > 0:
            maker_quote_cost = _side_cost_bps(side=side, price=maker_price, mid=mid)
            maker_quote_cost += maker_fee_bps if maker_fee_bps is not None else taker_fee
            maker_fill = _maker_filled_by_path(
                side=side,
                maker_price=maker_price,
                path=_path_prices(row.get("subsequent_price_path")),
            )
        usable.append(
            {
                "intent_id": row.get("intent_id"),
                "timestamp": row.get("timestamp") or row.get("_logged_at"),
                "venue": row.get("venue") or row.get("exchange"),
                "symbol": row.get("symbol"),
                "strategy": row.get("selected_strategy") or row.get("strategy_id") or row.get("_strategy_id"),
                "side": side,
                "qty": qty,
                "reference_mid": mid,
                "modeled_taker_fill_price": modeled,
                "taker_slippage_cost_bps": taker_slippage_cost,
                "taker_fee_bps": taker_fee,
                "taker_cost_bps": taker_cost,
                "spread_bps": _spread_bps(row, mid),
                "maker_resting_price": maker_price,
                "maker_fee_bps_assumption": maker_fee_bps if maker_fee_bps is not None else taker_fee,
                "maker_quote_cost_bps": maker_quote_cost,
                "maker_would_fill": maker_fill,
                "source_file": row.get("_source_file"),
            }
        )

    min_prob_records = int(min_fill_probability_records or min_records)
    summary = _summarize_rows(usable)
    status = "ready"
    limitations: list[str] = []
    recommendation = "no_change"
    if not records:
        status = "no_records"
        recommendation = "research_more"
        limitations.append("no shadow_would_be_fill records found")
    elif len(usable) < int(min_records):
        status = "insufficient_data"
        recommendation = "research_more"
        limitations.append(f"usable shadow records below minimum: {len(usable)}/{int(min_records)}")
    if records and summary["maker_fill_probability_records"] < min_prob_records:
        status = "insufficient_data"
        recommendation = "research_more"
        limitations.append(
            "stored shadow records do not include enough subsequent_price_path data "
            f"for maker fill-probability estimation: {summary['maker_fill_probability_records']}/{min_prob_records}"
        )
    if status == "ready":
        maker_prob = float(summary["maker_fill_probability_estimate"] or 0.0)
        maker_cost = summary["avg_maker_quote_cost_bps"]
        taker_cost = summary["avg_taker_cost_bps"]
        if maker_prob >= float(min_fill_probability) and maker_cost is not None and taker_cost is not None and maker_cost < taker_cost:
            recommendation = "candidate_execution_policy_change"
        elif maker_cost is not None and taker_cost is not None and maker_cost >= taker_cost:
            recommendation = "no_change"
        else:
            recommendation = "research_more"

    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in usable:
        key = (
            str(row.get("venue") or "unknown"),
            str(row.get("symbol") or "unknown"),
            str(row.get("strategy") or "unknown"),
        )
        grouped[key].append(row)
    groups = []
    for (venue, symbol, strategy), rows in sorted(grouped.items()):
        groups.append(
            {
                "venue": venue,
                "symbol": symbol,
                "strategy": strategy,
                **_summarize_rows(rows),
            }
        )
    return {
        "status": status,
        "recommendation": recommendation,
        "records_loaded": len(records),
        "usable_records": len(usable),
        "invalid_records": sum(invalid_reasons.values()),
        "invalid_reasons": dict(sorted(invalid_reasons.items())),
        "summary": summary,
        "groups": groups,
        "limitations": limitations,
    }


def build_execution_cost_stack_report(
    *,
    evidence_root: Path | None = None,
    maker_fee_bps: float | None = None,
    min_records: int = 30,
    min_fill_probability_records: int | None = None,
    min_fill_probability: float = 0.6,
) -> dict[str, Any]:
    loaded = load_shadow_would_be_fills(evidence_root)
    analysis = analyze_shadow_would_be_fills(
        loaded["records"],
        maker_fee_bps=maker_fee_bps,
        min_records=min_records,
        min_fill_probability_records=min_fill_probability_records,
        min_fill_probability=min_fill_probability,
    )
    report = {
        "report_type": REPORT_TYPE,
        "generated_at": _now_iso(),
        "read_only": True,
        "scope": "research_only_shadow_would_be_fill_records",
        "evidence_root": loaded["evidence_root"],
        "source_artifact_hash": loaded["source_artifact_hash"],
        "source_files": loaded["source_files"],
        "ignored_non_shadow_records": loaded["ignored_non_shadow_records"],
        "parse_errors": loaded["parse_errors"],
        "policy": {
            "no_live_routing_changes": True,
            "no_order_type_policy_changes": True,
            "no_canonical_paper_campaign_changes": True,
            "paper_fills_excluded": True,
        },
        "parameters": {
            "maker_fee_bps": maker_fee_bps,
            "min_records": int(min_records),
            "min_fill_probability_records": int(min_fill_probability_records or min_records),
            "min_fill_probability": float(min_fill_probability),
        },
        **analysis,
    }
    report["source_report_hash"] = _sha256_text(_canonical_json({k: v for k, v in report.items() if k != "source_report_hash"}))
    return report


def default_report_path() -> Path:
    return data_dir() / "execution_cost_stack" / f"execution_cost_stack.{_safe_stamp()}.json"
