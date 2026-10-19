"""Observed long-entry mid-price labels, never simulated fills or net profit."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path


def midpoint(row):
    try:
        bid, ask = float(row["bid"]), float(row["ask"])
        age = float(row["source_age_sec"])
        if row.get("quality_ok") is not True or not (math.isfinite(age) and age >= 0):
            return None
        if not (math.isfinite(bid) and math.isfinite(ask) and 0 < bid <= ask):
            return None
        return (bid + ask) / 2
    except (KeyError, TypeError, ValueError):
        return None


def summarize(rows, *, horizons=(5, 30, 60), tolerance_sec=1.0, max_quote_age_sec=1.0):
    if not horizons or any(not math.isfinite(h) or h <= 0 for h in horizons):
        raise ValueError("positive finite horizons required")
    if any(not math.isfinite(v) or v < 0 for v in (tolerance_sec, max_quote_age_sec)):
        raise ValueError("finite nonnegative timing bounds required")
    ids = [row["event_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate event IDs")
    for row in rows:
        if row.get("schema_version") != 1 or type(row.get("monotonic_ns")) is not int:
            raise ValueError("unsupported schema or timestamp")
        if not isinstance(row.get("capture_session_id"), str) or not row["capture_session_id"]:
            raise ValueError("missing capture session provenance")
    if len({row["capture_session_id"] for row in rows}) > 1:
        raise ValueError("mixed capture sessions")
    if any(b["monotonic_ns"] < a["monotonic_ns"] for a, b in zip(rows, rows[1:])):
        raise ValueError("capture clock order reset")
    quotes = {r["event_id"]: r for r in rows if r.get("kind") == "quote"}
    output = []
    for entry in rows:
        if entry.get("kind") != "admitted_entry":
            continue
        start = entry["monotonic_ns"]
        def eligible(q):
            return all(q.get(k) == entry.get(k) and entry.get(k) is not None
                       for k in ("venue", "symbol", "config_sha256")) and midpoint(q) is not None
        quote = quotes.get(entry.get("quote_event_id"))
        valid = (quote is not None and eligible(quote)
                 and quote["monotonic_ns"] <= start
                 and float(quote["source_age_sec"]) + (start - quote["monotonic_ns"]) / 1e9 <= max_quote_age_sec)
        labels = []
        for horizon in horizons:
            label = {"horizon_sec": horizon, "gross_mid_return_bps": None,
                     "reason": "entry_quote_unavailable"}
            if valid:
                target = start + int(horizon * 1e9)
                candidates = [q for q in quotes.values() if eligible(q)
                              and float(q["source_age_sec"]) <= max_quote_age_sec
                              and target <= q["monotonic_ns"] <= target + int(tolerance_sec * 1e9)]
                later = min(candidates, key=lambda q: q["monotonic_ns"], default=None)
                label["reason"] = "horizon_quote_unavailable"
                if later is not None:
                    label.update(reason="observed_mid_label_not_fill",
                                 gross_mid_return_bps=(midpoint(later)/midpoint(quote)-1)*10000,
                                 quote_event_id=later["event_id"],
                                 observation_lateness_sec=(later["monotonic_ns"]-target)/1e9)
            labels.append(label)
        output.append({"entry_event_id": entry["event_id"], "intent_id": entry.get("intent_id"),
                       "entry_quote_valid": bool(valid),
                       "labels": labels, "net_profit": None, "cost_status": "unverified"})
    return {"scope": "single_capture_session_long_entry_mid_labels_only",
            "admitted_entry_count": len(output), "entries": output,
            "valid_entry_quote_count": sum(e["entry_quote_valid"] for e in output),
            "available_label_count": sum(label["gross_mid_return_bps"] is not None
                                         for e in output for label in e["labels"]),
            "horizon_tolerance_sec": tolerance_sec, "max_quote_age_sec": max_quote_age_sec,
            "status": "NO_ENTRY_EVIDENCE" if not output else "DESCRIPTIVE_ONLY",
            "profitability": "NOT_EVALUATED", "coverage": "unverified"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path, help="One session JSONL; never concatenate sessions")
    parser.add_argument("--horizons", type=float, nargs="+", default=[5, 30, 60])
    parser.add_argument("--tolerance-sec", type=float, default=1.0)
    parser.add_argument("--max-quote-age-sec", type=float, default=1.0)
    args = parser.parse_args()
    raw = args.capture.read_bytes()
    rows = [json.loads(line) for line in raw.splitlines()]
    result = summarize(rows, horizons=args.horizons, tolerance_sec=args.tolerance_sec,
                       max_quote_age_sec=args.max_quote_age_sec)
    result["input_sha256"] = hashlib.sha256(raw).hexdigest()
    result["input"] = str(args.capture)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
