from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from services.analytics.paper_loss_replay import build_loss_replay
from services.analytics.paper_strategy_evidence_service import load_runtime_status as load_evidence_runtime_status
from services.ai_copilot.policy import report_root
from services.backtest.evidence_cycle import evidence_dir


def _latest_evidence_path() -> Path:
    return (evidence_dir() / "strategy_evidence.latest.json").resolve()


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _rows(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in list(((payload.get("aggregate_leaderboard") or {}).get("rows") or []))
        if isinstance(item, dict)
    ]


def _top_strategy(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return dict(rows[0]) if rows else {}


def _paper_history_summary(payload: dict[str, Any]) -> dict[str, Any]:
    paper_history = dict(payload.get("paper_history") or {})
    return {
        "status": str(paper_history.get("status") or "missing"),
        "fills_count": int(paper_history.get("fills_count") or 0),
        "strategy_count": int(paper_history.get("strategy_count") or 0),
        "journal_path": str(paper_history.get("journal_path") or ""),
        "caveat": str(paper_history.get("caveat") or ""),
    }


def _top_rows_snapshot(rows: list[dict[str, Any]], *, limit: int = 3) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in rows[: max(1, int(limit))]:
        out.append(
            {
                "strategy": str(row.get("strategy") or ""),
                "candidate": str(row.get("candidate") or ""),
                "rank": int(row.get("rank") or 0),
                "decision": str(row.get("decision") or ""),
                "leaderboard_score": float(row.get("leaderboard_score") or 0.0),
                "avg_return_pct": float(row.get("avg_return_pct") or 0.0),
                "max_drawdown_pct": float(row.get("max_drawdown_pct") or 0.0),
                "closed_trades": int(row.get("closed_trades") or 0),
                "evidence_status": str(row.get("evidence_status") or ""),
                "confidence_label": str(row.get("confidence_label") or ""),
                "paper_history_note": str(row.get("paper_history_note") or ""),
                "biggest_weakness": str(row.get("biggest_weakness") or ""),
                "next_improvement": str(row.get("next_improvement") or ""),
            }
        )
    return out


def _collector_runtime_summary() -> dict[str, Any]:
    payload = dict(load_evidence_runtime_status() or {})
    return {
        "ok": bool(payload.get("ok", True)),
        "has_status": bool(payload.get("has_status")),
        "status": str(payload.get("status") or "unknown"),
        "reason": str(payload.get("reason") or ""),
        "summary_text": str(payload.get("summary_text") or ""),
        "completed_strategies": int(payload.get("completed_strategies") or 0),
        "total_strategies": int(payload.get("total_strategies") or 0),
        "results_count": len(list(payload.get("results") or [])),
        "latest_path": str(((payload.get("evidence") or {}).get("latest_path")) or ""),
    }


def _collector_incomplete(runtime: dict[str, Any]) -> bool:
    total = int(runtime.get("total_strategies") or 0)
    completed = int(runtime.get("completed_strategies") or 0)
    return total > 0 and completed < total


def _derive_severity(
    *,
    ok: bool,
    top_row: dict[str, Any],
    paper_history: dict[str, Any],
    collector_runtime: dict[str, Any],
) -> tuple[str, str]:
    if not ok:
        return ("warn", "No persisted strategy evidence leaderboard is available yet.")

    selected_strategy = str(top_row.get("strategy") or "").strip()
    evidence_status = str(top_row.get("evidence_status") or "").strip().lower()
    paper_history_status = str(paper_history.get("status") or "").strip().lower()
    fills_count = int(paper_history.get("fills_count") or 0)

    if _collector_incomplete(collector_runtime):
        completed = int(collector_runtime.get("completed_strategies") or 0)
        total = int(collector_runtime.get("total_strategies") or 0)
        return (
            "warn",
            f"Strategy lab report for `{selected_strategy}` is based on partial evidence; "
            f"the current collector run is only {completed}/{total} complete.",
        )
    if paper_history_status != "available":
        return (
            "warn",
            f"Strategy lab report for `{selected_strategy}` is missing persisted paper-history support.",
        )
    if fills_count < 10 or evidence_status in {"paper_thin", "insufficient", "missing", "strategy_missing"}:
        return (
            "warn",
            f"Strategy lab report for `{selected_strategy}` is still thin and not promotion-grade.",
        )
    return ("ok", f"Strategy lab report built from persisted evidence for `{selected_strategy}`.")


def _recommendations(
    *,
    payload: dict[str, Any],
    top_row: dict[str, Any],
    paper_history: dict[str, Any],
    collector_runtime: dict[str, Any],
    loss_replay: dict[str, Any] | None,
) -> list[str]:
    recommendations: list[str] = []
    if not payload or not top_row:
        return ["Run a fresh strategy evidence cycle before making strategy changes; no persisted lab evidence was available."]

    comparison = dict(payload.get("comparison") or {})
    movement = str(comparison.get("summary_text") or "").strip()
    if movement:
        recommendations.append(movement)

    top_strategy = str(top_row.get("strategy") or "").strip()
    top_decision = str(top_row.get("decision") or "").strip().lower()
    top_evidence_status = str(top_row.get("evidence_status") or "").strip().lower()
    if _collector_incomplete(collector_runtime):
        recommendations.append("Finish the current paper evidence cycle before treating the current top rank as stable.")
    if top_strategy:
        recommendations.append(f"Keep `{top_strategy}` as the current lab focus until a new evidence cycle changes the top ranking.")
    if top_decision == "improve":
        next_improvement = str(top_row.get("next_improvement") or "").strip()
        if next_improvement:
            recommendations.append(next_improvement)
    if top_decision == "freeze":
        recommendations.append("Do not promote the current top strategy; collect more paper evidence before changing guardrails or live scope.")

    if str(paper_history.get("status") or "") != "available":
        recommendations.append("Grow persisted paper-history evidence before treating leaderboard rank as promotion-grade.")
    elif int(paper_history.get("fills_count") or 0) < 10:
        recommendations.append("Paper-history exists but remains thin; add more fills before changing parameters from this report.")
    if top_evidence_status in {"paper_thin", "insufficient", "missing", "strategy_missing"}:
        recommendations.append("Do not treat the current top strategy as promotion-ready while evidence status remains thin or insufficient.")

    if isinstance(loss_replay, dict) and int(loss_replay.get("losing_trade_count") or 0) > 0:
        recommendations.append("Review the latest losing replay rows before changing the top strategy preset or thresholds.")
    elif top_strategy:
        recommendations.append(f"No losing replay rows were found for `{top_strategy}` in the current journal filter.")

    return recommendations


def build_strategy_lab_report(
    *,
    strategy_id: str = "",
    symbol: str = "",
    replay_limit: int = 3,
    include_loss_replay: bool = True,
    journal_path: str = "",
) -> dict[str, Any]:
    latest_path = _latest_evidence_path()
    payload = _load_json(latest_path)
    rows = _rows(payload)
    top_row = _top_strategy(rows)
    selected_strategy = str(strategy_id or top_row.get("strategy") or "").strip()
    selected_symbol = str(symbol or payload.get("symbol") or top_row.get("symbol") or "").strip()
    paper_history = _paper_history_summary(payload)
    comparison = dict(payload.get("comparison") or {})
    collector_runtime = _collector_runtime_summary()

    loss_replay: dict[str, Any] | None = None
    if include_loss_replay and selected_strategy:
        loss_replay = build_loss_replay(
            strategy_id=selected_strategy,
            symbol=selected_symbol,
            journal_path=str(journal_path or ""),
            limit=int(replay_limit or 3),
        )

    ok = bool(payload) and bool(rows)
    severity, summary = _derive_severity(
        ok=ok,
        top_row=top_row,
        paper_history=paper_history,
        collector_runtime=collector_runtime,
    )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "ok": ok,
        "severity": severity,
        "summary": summary,
        "latest_evidence_path": str(latest_path),
        "evidence_as_of": str(payload.get("as_of") or ""),
        "symbol": selected_symbol,
        "selected_strategy": selected_strategy,
        "top_rows": _top_rows_snapshot(rows),
        "collector_runtime": collector_runtime,
        "paper_history": paper_history,
        "comparison": {
            "has_previous": bool(comparison.get("has_previous")),
            "summary_text": str(comparison.get("summary_text") or ""),
            "top_strategy_previous": str(comparison.get("top_strategy_previous") or ""),
            "top_strategy_current": str(comparison.get("top_strategy_current") or ""),
            "top_strategy_changed": bool(comparison.get("top_strategy_changed")),
            "improved_count": int(comparison.get("improved_count") or 0),
            "degraded_count": int(comparison.get("degraded_count") or 0),
            "unchanged_count": int(comparison.get("unchanged_count") or 0),
            "new_count": int(comparison.get("new_count") or 0),
        },
        "loss_replay": {
            "available": bool(loss_replay),
            "losing_trade_count": int(loss_replay.get("losing_trade_count") or 0) if isinstance(loss_replay, dict) else 0,
            "closed_trade_count": int(loss_replay.get("closed_trade_count") or 0) if isinstance(loss_replay, dict) else 0,
            "summary": dict(loss_replay.get("summary") or {}) if isinstance(loss_replay, dict) else {},
            "rows": list(loss_replay.get("loss_replays") or []) if isinstance(loss_replay, dict) else [],
        },
        "recommendations": _recommendations(
            payload=payload,
            top_row=top_row,
            paper_history=paper_history,
            collector_runtime=collector_runtime,
            loss_replay=loss_replay,
        ),
    }


def render_strategy_lab_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# CryptKeep Strategy Lab",
        "",
        f"- Generated: {report.get('generated_at')}",
        f"- Severity: {report.get('severity')}",
        f"- OK: {bool(report.get('ok'))}",
        f"- Strategy: {report.get('selected_strategy') or '(none)'}",
        f"- Symbol: {report.get('symbol') or '(none)'}",
        "",
        "## Summary",
        str(report.get("summary") or ""),
        "",
        "## Top Rows",
    ]
    top_rows = list(report.get("top_rows") or [])
    if top_rows:
        for row in top_rows:
            lines.append(
                f"- `{row.get('strategy')}` rank `{row.get('rank')}` decision `{row.get('decision')}` "
                f"score `{float(row.get('leaderboard_score') or 0.0):.6f}` drawdown `{float(row.get('max_drawdown_pct') or 0.0):.2f}%`"
            )
    else:
        lines.append("- `(none)`")

    paper_history = dict(report.get("paper_history") or {})
    collector_runtime = dict(report.get("collector_runtime") or {})
    lines.extend(
        [
            "",
            "## Evidence Runtime",
            f"- status: `{collector_runtime.get('status')}`",
            f"- completed: `{collector_runtime.get('completed_strategies')}` / `{collector_runtime.get('total_strategies')}`",
        ]
    )
    if str(collector_runtime.get("summary_text") or "").strip():
        lines.append(f"- summary: {collector_runtime.get('summary_text')}")

    lines.extend(
        [
            "",
            "## Paper History",
            f"- status: `{paper_history.get('status')}`",
            f"- fills: `{paper_history.get('fills_count')}`",
            f"- strategy count: `{paper_history.get('strategy_count')}`",
        ]
    )
    if str(paper_history.get("caveat") or "").strip():
        lines.append(f"- caveat: {paper_history.get('caveat')}")

    comparison = dict(report.get("comparison") or {})
    lines.extend(
        [
            "",
            "## Comparison",
            f"- summary: {comparison.get('summary_text') or '(none)'}",
            f"- top changed: `{bool(comparison.get('top_strategy_changed'))}`",
            f"- improved: `{comparison.get('improved_count')}`",
            f"- degraded: `{comparison.get('degraded_count')}`",
        ]
    )

    loss_replay = dict(report.get("loss_replay") or {})
    lines.extend(
        [
            "",
            "## Loss Replay",
            f"- available: `{bool(loss_replay.get('available'))}`",
            f"- losing trades: `{loss_replay.get('losing_trade_count')}`",
            f"- closed trades: `{loss_replay.get('closed_trade_count')}`",
        ]
    )

    lines.extend(["", "## Recommendations"])
    lines.extend(f"- {item}" for item in list(report.get("recommendations") or []))
    return "\n".join(lines) + "\n"


def write_strategy_lab_report(report: dict[str, Any], *, stem: str | None = None) -> dict[str, str]:
    root = report_root()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_stem = str(stem or f"strategy_lab_{ts}").strip().replace(" ", "_")
    json_path = root / f"{safe_stem}.json"
    markdown_path = root / f"{safe_stem}.md"
    json_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    markdown_path.write_text(render_strategy_lab_markdown(report), encoding="utf-8")
    return {"json_path": str(json_path), "markdown_path": str(markdown_path)}
