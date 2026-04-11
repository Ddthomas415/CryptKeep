from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

STORE_DIR = Path(".cbp_state/backtests")
STORE_FILE = STORE_DIR / "selector_comparison_runs.jsonl"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_selector_run(
    *,
    result: dict[str, Any],
    label: str = "",
    ranking_config: dict[str, Any] | None = None,
    preset_name: str = "",
) -> dict[str, Any]:
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    row = {
        "ts": _now(),
        "label": str(label or "").strip(),
        "preset_name": str(preset_name or "").strip(),
        "ranking_config": dict(ranking_config or {}),
        "venue": result.get("venue"),
        "timeframe": result.get("timeframe"),
        "forward_bars": result.get("forward_bars"),
        "top_n": result.get("top_n"),
        "baseline": result.get("baseline") or {},
        "composite": result.get("composite") or {},
        "delta": result.get("delta") or {},
    }

    with STORE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    return {"ok": True, "row": row, "path": str(STORE_FILE)}


def load_selector_runs(limit: int = 200) -> list[dict[str, Any]]:
    if not STORE_FILE.exists():
        return []

    rows: list[dict[str, Any]] = []
    with STORE_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
    return rows[-limit:]


def summarize_selector_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        b = dict(r.get("baseline") or {}).get("summary", {})
        c = dict(r.get("composite") or {}).get("summary", {})
        d = dict(r.get("delta") or {})
        out.append({
            "ts": r.get("ts"),
            "label": r.get("label"),
            "preset_name": r.get("preset_name"),
            "timeframe": r.get("timeframe"),
            "forward_bars": r.get("forward_bars"),
            "top_n": r.get("top_n"),
            "baseline_avg_return_pct": b.get("avg_return_pct"),
            "composite_avg_return_pct": c.get("avg_return_pct"),
            "delta_avg_return_pct": d.get("avg_return_pct"),
            "baseline_hit_rate": b.get("hit_rate"),
            "composite_hit_rate": c.get("hit_rate"),
            "delta_hit_rate": d.get("hit_rate"),
            "baseline_total_return_pct": b.get("total_return_pct"),
            "composite_total_return_pct": c.get("total_return_pct"),
            "delta_total_return_pct": d.get("total_return_pct"),
        })
    return out


def summarize_selector_runs_by_preset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}

    for r in rows:
        key = str(r.get("preset_name") or "unknown").strip() or "unknown"
        grouped.setdefault(key, []).append(dict(r))

    out = []
    for preset_name, items in grouped.items():
        items = sorted(items, key=lambda x: str(x.get("ts") or ""))
        latest = items[-1] if items else {}
        best = max(
            items,
            key=lambda x: _safe_float(((x.get("delta") or {}).get("avg_return_pct")), 0.0),
            default={},
        )

        avg_delta_return = sum(_safe_float(((x.get("delta") or {}).get("avg_return_pct")), 0.0) for x in items) / max(len(items), 1)
        avg_delta_hit = sum(_safe_float(((x.get("delta") or {}).get("hit_rate")), 0.0) for x in items) / max(len(items), 1)
        avg_delta_total = sum(_safe_float(((x.get("delta") or {}).get("total_return_pct")), 0.0) for x in items) / max(len(items), 1)

        out.append({
            "preset_name": preset_name,
            "runs": len(items),
            "avg_delta_avg_return_pct": round(avg_delta_return, 4),
            "avg_delta_hit_rate": round(avg_delta_hit, 4),
            "avg_delta_total_return_pct": round(avg_delta_total, 4),
            "best_delta_avg_return_pct": round(_safe_float(((best.get("delta") or {}).get("avg_return_pct")), 0.0), 4),
            "best_run_ts": best.get("ts"),
            "latest_run_ts": latest.get("ts"),
            "latest_label": latest.get("label"),
        })

    out.sort(key=lambda r: r["avg_delta_avg_return_pct"], reverse=True)
    return out
