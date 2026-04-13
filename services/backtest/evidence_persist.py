from __future__ import annotations

import json
import math
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from statistics import pstdev
from typing import Any, Dict, Iterable, List

from services.analytics.journal_analytics import fifo_pnl_from_fills
from services.analytics.strategy_feedback import (
    build_strategy_feedback_weighting,
    load_strategy_feedback_ledger,
)
from services.backtest.leaderboard import rank_strategy_rows, run_strategy_leaderboard
from services.backtest.walk_forward import run_anchored_walk_forward
from services.os.app_paths import code_root, data_dir, ensure_dirs
from services.strategies.presets import apply_preset
from services.strategies.hypotheses import get_strategy_hypothesis


from services.backtest.evidence_shared import (
    _now_iso,
    _fnum,
    _top_strategy_name,
    _load_recent_history_payloads,
    _build_recent_trend,
)

def evidence_dir() -> Path:
    ensure_dirs()
    path = data_dir() / "strategy_evidence"
    path.mkdir(parents=True, exist_ok=True)
    return path


def _load_evidence_payload(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return dict(payload) if isinstance(payload, dict) else {}


def _decision_weight(value: Any) -> int:
    mapping = {
        "keep": 4,
        "improve": 3,
        "freeze": 2,
        "retire": 1,
    }
    return int(mapping.get(str(value or "").strip().lower(), 0))


def _row_movement(*, current: dict[str, Any], previous: dict[str, Any] | None) -> str:
    if not previous:
        return "new"
    current_decision = _decision_weight(current.get("decision"))
    previous_decision = _decision_weight(previous.get("decision"))
    if current_decision > previous_decision:
        return "improved"
    if current_decision < previous_decision:
        return "degraded"

    current_rank = int(_fnum(current.get("rank"), 0.0))
    previous_rank = int(_fnum(previous.get("rank"), 0.0))
    if previous_rank > 0 and current_rank > 0:
        if current_rank < previous_rank:
            return "improved"
        if current_rank > previous_rank:
            return "degraded"

    score_delta = _fnum(current.get("leaderboard_score"), 0.0) - _fnum(previous.get("leaderboard_score"), 0.0)
    if score_delta > 1e-9:
        return "improved"
    if score_delta < -1e-9:
        return "degraded"
    return "unchanged"


def build_evidence_comparison(
    current_report: dict[str, Any],
    *,
    previous_report: dict[str, Any] | None = None,
    previous_history_reports: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    current_payload = dict(current_report or {})
    previous_payload = dict(previous_report or {})
    recent_trend = _build_recent_trend(current_payload, previous_history_reports=previous_history_reports)
    previous_rows = {
        str(item.get("strategy") or ""): dict(item)
        for item in list(((previous_payload.get("aggregate_leaderboard") or {}).get("rows") or []))
        if isinstance(item, dict) and str(item.get("strategy") or "").strip()
    }
    current_rows = [
        dict(item)
        for item in list(((current_payload.get("aggregate_leaderboard") or {}).get("rows") or []))
        if isinstance(item, dict) and str(item.get("strategy") or "").strip()
    ]
    previous_as_of = str(previous_payload.get("as_of") or "").strip() or None
    current_as_of = str(current_payload.get("as_of") or "").strip() or None

    if not previous_rows or not previous_as_of:
        return {
            "has_previous": False,
            "previous_as_of": previous_as_of,
            "current_as_of": current_as_of,
            "summary_text": "No prior persisted strategy evidence artifact is available for comparison.",
            "improved_count": 0,
            "degraded_count": 0,
            "unchanged_count": 0,
            "new_count": int(len(current_rows)),
            "changes": [],
            "top_strategy_previous": None,
            "top_strategy_current": _top_strategy_name(current_payload),
            "top_strategy_changed": False,
            "recent_trend": recent_trend,
        }

    changes: list[dict[str, Any]] = []
    improved = 0
    degraded = 0
    unchanged = 0
    new_count = 0
    for row in current_rows:
        strategy = str(row.get("strategy") or "").strip()
        if not strategy:
            continue
        previous = previous_rows.get(strategy)
        movement = _row_movement(current=row, previous=previous)
        if movement == "improved":
            improved += 1
        elif movement == "degraded":
            degraded += 1
        elif movement == "new":
            new_count += 1
        else:
            unchanged += 1
        changes.append(
            {
                "strategy": strategy,
                "movement": movement,
                "current_rank": int(_fnum(row.get("rank"), 0.0)) or None,
                "previous_rank": int(_fnum(previous.get("rank"), 0.0)) or None if previous else None,
                "rank_delta": (
                    int(_fnum(previous.get("rank"), 0.0)) - int(_fnum(row.get("rank"), 0.0))
                    if previous and int(_fnum(previous.get("rank"), 0.0)) > 0 and int(_fnum(row.get("rank"), 0.0)) > 0
                    else None
                ),
                "current_decision": str(row.get("decision") or ""),
                "previous_decision": str(previous.get("decision") or "") if previous else "",
                "decision_changed": str(row.get("decision") or "") != str(previous.get("decision") or "") if previous else True,
                "current_score": float(_fnum(row.get("leaderboard_score"), 0.0)),
                "previous_score": float(_fnum(previous.get("leaderboard_score"), 0.0)) if previous else None,
                "score_delta": (
                    float(_fnum(row.get("leaderboard_score"), 0.0) - _fnum(previous.get("leaderboard_score"), 0.0))
                    if previous
                    else None
                ),
                "current_avg_return_pct": float(_fnum(row.get("avg_return_pct"), 0.0)),
                "previous_avg_return_pct": float(_fnum(previous.get("avg_return_pct"), 0.0)) if previous else None,
                "avg_return_pct_delta": (
                    float(_fnum(row.get("avg_return_pct"), 0.0) - _fnum(previous.get("avg_return_pct"), 0.0))
                    if previous
                    else None
                ),
                "current_evidence_status": str(row.get("evidence_status") or ""),
                "previous_evidence_status": str(previous.get("evidence_status") or "") if previous else "",
            }
        )

    previous_top = next(iter(previous_rows.values()), {})
    current_top = current_rows[0] if current_rows else {}
    top_previous = str(previous_top.get("strategy") or "").strip() or None
    top_current = str(current_top.get("strategy") or "").strip() or None
    top_changed = bool(top_previous and top_current and top_previous != top_current)
    if top_changed:
        summary_text = f"Top strategy changed from {top_previous} to {top_current} versus the prior persisted evidence run."
    elif degraded > 0 and improved == 0:
        summary_text = f"{degraded} strategy comparison(s) degraded versus the prior persisted evidence run."
    elif improved > 0 and degraded == 0:
        summary_text = f"{improved} strategy comparison(s) improved versus the prior persisted evidence run."
    elif improved > 0 or degraded > 0:
        summary_text = (
            f"{improved} strategy comparison(s) improved and {degraded} degraded versus the prior persisted evidence run."
        )
    else:
        summary_text = "Current strategy evidence is unchanged versus the prior persisted evidence run."

    return {
        "has_previous": True,
        "previous_as_of": previous_as_of,
        "current_as_of": current_as_of,
        "summary_text": summary_text,
        "improved_count": int(improved),
        "degraded_count": int(degraded),
        "unchanged_count": int(unchanged),
        "new_count": int(new_count),
        "changes": changes,
        "top_strategy_previous": top_previous,
        "top_strategy_current": top_current,
        "top_strategy_changed": top_changed,
        "recent_trend": recent_trend,
    }


def persist_strategy_evidence(report: dict[str, Any], *, latest_path: str = "") -> dict[str, Any]:
    payload = dict(report or {})
    evidence_root = evidence_dir()
    ts_token = str(payload.get("as_of") or _now_iso()).replace(":", "").replace("-", "").replace("Z", "Z")
    latest = Path(latest_path).expanduser().resolve() if latest_path else (evidence_root / "strategy_evidence.latest.json").resolve()
    history = (evidence_root / f"strategy_evidence.{ts_token}.json").resolve()
    previous_payload = _load_evidence_payload(latest) if latest.exists() else {}
    previous_history = _load_recent_history_payloads(evidence_root, limit=4)
    comparison = build_evidence_comparison(
        payload,
        previous_report=previous_payload,
        previous_history_reports=previous_history,
    )
    payload["comparison"] = comparison
    if isinstance(report, dict):
        report["comparison"] = comparison
    latest.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    history.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "latest_path": str(latest),
        "history_path": str(history),
    }


def default_decision_record_path(*, report: dict[str, Any] | None = None) -> Path:
    payload = dict(report or {})
    as_of = str(payload.get("as_of") or _now_iso())
    date_token = as_of.split("T", 1)[0]
    return (code_root() / "docs" / "strategies" / f"decision_record_{date_token}.md").resolve()


def render_decision_record(report: dict[str, Any], *, artifact_path: str = "") -> str:
    payload = dict(report or {})
    rows = [dict(item) for item in list(((payload.get("aggregate_leaderboard") or {}).get("rows") or []))]
    decisions = [dict(item) for item in list(payload.get("decisions") or [])]
    windows = [dict(item) for item in list(payload.get("windows") or [])]
    paper_history = dict(payload.get("paper_history") or {})
    strategy_feedback_ledger = dict(payload.get("strategy_feedback_ledger") or {})
    comparison = dict(payload.get("comparison") or {})
    as_of = str(payload.get("as_of") or _now_iso())
    date_token = as_of.split("T", 1)[0]

    keep = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "keep"]
    improve = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "improve"]
    freeze = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "freeze"]
    retire = [f"`{item['strategy']}`" for item in decisions if str(item.get("decision") or "") == "retire"]

    out: list[str] = [
        f"# Strategy Decision Record — {date_token}",
        "",
        "## Scope",
        "",
        f"This record reflects the current repo state on {date_token}.",
        "",
        "Guardrails:",
        "- crypto-first scope",
        "- paper-heavy defaults remain active",
        "- live trading is guarded and fail-closed",
        "- stock support is not proven",
        "- shorting is not fully validated",
        "- this is not a profitability claim",
        "",
        "## Safety Gate",
        "",
        "Phase 1 safety pack should be rerun before relying on this record.",
        "",
        "## Evaluation Inputs",
        "",
        f"- symbol: `{str(payload.get('symbol') or '')}`",
        f"- windows: `{int(payload.get('window_count') or 0)}` deterministic synthetic windows",
        f"- initial cash: `{_fnum(payload.get('initial_cash'), 0.0):.0f}`",
        f"- fees: `{_fnum(payload.get('fee_bps'), 0.0):.0f} bps`",
        f"- slippage: `{_fnum(payload.get('slippage_bps'), 0.0):.0f} bps`",
    ]
    if paper_history:
        out.append(f"- paper-history source: `{str(paper_history.get('source') or 'unknown')}`")
        out.append(f"- paper-history status: `{str(paper_history.get('status') or 'missing')}`")
        out.append(f"- paper-history journal: `{str(paper_history.get('journal_path') or '')}`")
        out.append(f"- paper-history fills: `{int(paper_history.get('fills_count') or 0)}`")
    if strategy_feedback_ledger:
        out.append(f"- strategy-feedback source: `{str(strategy_feedback_ledger.get('source') or 'unknown')}`")
        out.append(f"- strategy-feedback status: `{str(strategy_feedback_ledger.get('status') or 'missing')}`")
        out.append(f"- strategy-feedback journal: `{str(strategy_feedback_ledger.get('journal_path') or '')}`")
        out.append(f"- strategy-feedback strategies: `{int(strategy_feedback_ledger.get('strategy_count') or 0)}`")
    if artifact_path:
        out.append(f"- evidence artifact: `{artifact_path}`")
    out.extend(
        [
            "",
            "Window set:",
        ]
    )
    for window in windows:
        out.append(
            f"- `{str(window.get('window_id') or '')}`: {str(window.get('label') or '')} ({int(window.get('bars') or 0)} bars)"
        )
    out.extend(
        [
            "",
            "Important limitation:",
            "- these windows are deterministic synthetic benchmarks, not live or market-history proof",
            "- this cycle is stronger than a single-window pass, but it still does not prove profitability or promotion readiness by itself",
            f"- persisted paper-history status for this run is `{str(paper_history.get('status') or 'missing')}`",
            "",
        ]
    )
    if comparison:
        out.extend(
            [
                "## Run-to-Run Comparison",
                "",
                f"- previous run: `{str(comparison.get('previous_as_of') or 'none')}`",
                f"- current run: `{str(comparison.get('current_as_of') or as_of)}`",
                f"- top strategy previous: `{str(comparison.get('top_strategy_previous') or 'none')}`",
                f"- top strategy current: `{str(comparison.get('top_strategy_current') or 'none')}`",
                f"- top strategy changed: `{'yes' if bool(comparison.get('top_strategy_changed')) else 'no'}`",
                f"- improved comparisons: `{int(comparison.get('improved_count') or 0)}`",
                f"- degraded comparisons: `{int(comparison.get('degraded_count') or 0)}`",
                f"- unchanged comparisons: `{int(comparison.get('unchanged_count') or 0)}`",
                f"- new comparisons: `{int(comparison.get('new_count') or 0)}`",
                "",
                f"Summary: {str(comparison.get('summary_text') or 'No comparison summary available.')}",
                "",
            ]
        )
        recent_trend = dict(comparison.get("recent_trend") or {})
        if recent_trend:
            out.extend(
                [
                    f"- recent persisted runs considered: `{int(recent_trend.get('run_count') or 0)}`",
                    f"- distinct recent top strategies: `{int(recent_trend.get('distinct_top_strategy_count') or 0)}`",
                    f"- current top streak: `{int(recent_trend.get('current_top_streak') or 0)}`",
                    "",
                    f"Recent trend: {str(recent_trend.get('summary_text') or 'No recent trend summary available.')}",
                    "",
                ]
            )
        changes = [dict(item) for item in list(comparison.get("changes") or []) if isinstance(item, dict)]
        if changes:
            out.extend(["Comparison detail:"])
            for item in changes[:5]:
                out.append(
                    "- "
                    f"`{str(item.get('strategy') or '')}` moved `{str(item.get('movement') or 'unchanged')}`; "
                    f"rank `{str(item.get('previous_rank') or '-')}` -> `{str(item.get('current_rank') or '-')}`, "
                    f"decision `{str(item.get('previous_decision') or '-')}` -> `{str(item.get('current_decision') or '-')}`."
                )
            out.extend([""])
    out.extend(
        [
            "## Results",
            "",
        ]
    )
    for row in rows:
        out.extend(
            [
                f"### `{str(row.get('strategy') or '')}`",
                f"- candidate: `{str(row.get('candidate') or '')}`",
                f"- rank: `{int(row.get('rank') or 0)}`",
                f"- aggregate leaderboard score: `{_fnum(row.get('leaderboard_score'), 0.0):.6f}`",
                f"- base leaderboard score: `{_fnum(row.get('base_leaderboard_score'), _fnum(row.get('leaderboard_score'), 0.0)):.6f}`",
                f"- average net return after costs: `{_fnum(row.get('avg_return_pct'), 0.0):+.2f}%`",
                f"- worst-window return: `{_fnum(row.get('worst_window_return_pct'), 0.0):+.2f}%`",
                f"- worst drawdown: `{_fnum(row.get('max_drawdown_pct'), 0.0):.2f}%`",
                f"- closed trades: `{int(row.get('closed_trades') or 0)}`",
                f"- active windows: `{int(row.get('active_window_count') or 0)}` / `{int(row.get('window_count') or 0)}`",
                f"- positive windows: `{int(row.get('positive_window_count') or 0)}` / `{int(row.get('window_count') or 0)}`",
                f"- best window: `{str(row.get('best_window_id') or 'unknown')}`",
                f"- worst window: `{str(row.get('worst_window_id') or 'unknown')}`",
                f"- evidence status: `{str(row.get('evidence_status') or 'unknown')}`",
                f"- confidence: `{str(row.get('confidence_label') or 'unknown')}`",
                f"- paper-history: {str(row.get('paper_history_note') or 'No strategy-attributed persisted paper-history fills are available yet.')}",
                f"- strategy feedback: {str(((row.get('strategy_feedback') or {}).get('summary_text')) or 'No persisted strategy feedback summary recorded.')}",
                f"- feedback weighting: `{str(((row.get('feedback_weighting') or {}).get('status')) or 'unknown')}`",
                f"- research acceptance: `{str(((row.get('research_acceptance') or {}).get('status')) or 'unknown')}`",
                f"- research summary: {str(((row.get('research_acceptance') or {}).get('summary')) or 'No research-acceptance summary recorded.')}",
                f"- walk-forward: `{str(((row.get('walk_forward') or {}).get('status')) or 'unknown')}`",
                f"- walk-forward windows: `{int(((row.get('walk_forward') or {}).get('window_count')) or 0)}`",
                "",
                f"Decision: `{str(row.get('decision') or 'unknown')}`",
                "",
                "Reason:",
                f"- {str(row.get('decision_reason') or 'No reason recorded.')}",
                f"- Evidence note: {str(row.get('evidence_note') or 'No evidence note recorded.')}",
                f"- Feedback weighting: {str(((row.get('feedback_weighting') or {}).get('summary')) or 'No feedback weighting summary recorded.')}",
                f"- Biggest weakness: {str(row.get('biggest_weakness') or 'Unknown.')}",
                "",
                "Next work:",
                f"- {str(row.get('next_improvement') or 'Rerun the evidence cycle after the next smallest change.')}",
                "",
            ]
        )
        for blocker in list(((row.get("research_acceptance") or {}).get("blockers")) or []):
            out.append(f"- Research blocker: {str(blocker)}")
        walk_forward = dict(row.get("walk_forward") or {})
        walk_forward_summary = dict(walk_forward.get("summary") or {})
        if bool(walk_forward.get("available")):
            out.append(
                "- Walk-forward summary: "
                f"{float(walk_forward_summary.get('avg_test_return_pct') or 0.0):+.2f}% average test return, "
                f"{float(walk_forward_summary.get('avg_test_max_drawdown_pct') or 0.0):.2f}% average test drawdown, "
                f"{int(round(float(walk_forward_summary.get('non_negative_test_window_ratio') or 0.0) * 100.0))}% non-negative test windows, "
                f"{int(walk_forward_summary.get('total_test_closed_trades') or 0)} closed test trade(s)."
            )
        elif str(walk_forward.get("status") or "").strip():
            out.append(f"- Walk-forward status: {str(walk_forward.get('status') or '').strip()}")
        out.extend([""])
    out.extend(
        [
            "## Forced Decision Set",
            "",
            "Keep:",
            *([f"- {item}" for item in keep] or ["- none"]),
            "",
            "Improve:",
            *([f"- {item}" for item in improve] or ["- none"]),
            "",
            "Freeze:",
            *([f"- {item}" for item in freeze] or ["- none"]),
            "",
            "Retire:",
            *([f"- {item}" for item in retire] or ["- none"]),
            "",
            "## Operator Interpretation",
            "",
            "What this does **not** mean:",
            "- no strategy is proven profitable",
            "- no strategy is approved for real-live promotion",
            "- no claim is made about validated short support",
            "",
            "What it **does** mean:",
            "- the strategy ranking now reflects multiple deterministic windows instead of one benchmark pass",
            "- inactive or low-participation candidates are easier to challenge with explicit evidence",
            "- persisted paper-history evidence is included when available, but missing paper history is now explicit instead of silent",
            "- promotion decisions should still remain conservative until broader paper or sandbox evidence exists",
            "",
            "## Follow-up Gaps",
            "",
            "The next improvement to the evaluation layer should be:",
            "- extend persisted evidence comparison beyond the immediately previous artifact",
            "- grow the trade journal so paper-history evidence is no longer missing or thin",
            "- improve deterministic windows where strategies still show no realized closed-trade participation",
            "",
        ]
    )
    return "\n".join(out)


def write_decision_record(report: dict[str, Any], *, path: str = "", artifact_path: str = "") -> dict[str, Any]:
    target = Path(path).expanduser().resolve() if path else default_decision_record_path(report=report)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_decision_record(report, artifact_path=artifact_path), encoding="utf-8")
    return {
        "ok": True,
        "path": str(target),
    }
