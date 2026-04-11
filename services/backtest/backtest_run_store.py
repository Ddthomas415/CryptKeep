from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

STORE_DIR = Path(".cbp_state/backtests")
STORE_FILE = STORE_DIR / "historical_selector_runs.jsonl"


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def append_historical_selector_run(
    *,
    result: dict[str, Any],
    label: str = "",
    ranking_config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    STORE_DIR.mkdir(parents=True, exist_ok=True)

    row = {
        "ts": _now(),
        "label": str(label or "").strip(),
        "ranking_config": dict(ranking_config or {}),
        "venue": result.get("venue"),
        "timeframe": result.get("timeframe"),
        "forward_bars": result.get("forward_bars"),
        "top_n": result.get("top_n"),
        "anchors_tested": result.get("anchors_tested"),
        "baseline": result.get("baseline") or {},
        "composite": result.get("composite") or {},
        "delta": result.get("delta") or {},
    }

    with STORE_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row) + "\n")

    return {"ok": True, "row": row, "path": str(STORE_FILE)}


def load_historical_selector_runs(limit: int = 200) -> list[dict[str, Any]]:
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


def summarize_saved_runs(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for r in rows:
        b = dict(r.get("baseline") or {})
        c = dict(r.get("composite") or {})
        d = dict(r.get("delta") or {})
        out.append({
            "ts": r.get("ts"),
            "label": r.get("label"),
            "timeframe": r.get("timeframe"),
            "forward_bars": r.get("forward_bars"),
            "top_n": r.get("top_n"),
            "anchors_tested": r.get("anchors_tested"),
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
