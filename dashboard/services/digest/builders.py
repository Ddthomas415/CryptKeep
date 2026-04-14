from __future__ import annotations

from typing import Any

from dashboard.services.crypto_edge_research import (
    load_crypto_edge_collector_runtime,
    load_crypto_edge_staleness_digest,
    load_crypto_edge_staleness_summary,
    load_latest_live_crypto_edge_snapshot,
)
from dashboard.services.promotion_ladder import build_promotion_readiness
from dashboard.services.digest.strategy_evidence import load_latest_strategy_evidence
from dashboard.services.digest.contracts import (
    AttentionItem,
    AttentionNowData,
    CryptoEdgeModuleRow,
    CryptoEdgeSummaryData,
    FreshnessPanelData,
    FreshnessRow,
    FreshnessState,
    HealthState,
    HomeDigestData,
    IncidentItem,
    LeaderboardStrategyRow,
    LeaderboardSummaryData,
    ModeTruthData,
    NextBestActionData,
    PageStatusData,
    RuntimeModeValue,
    RuntimeTruthData,
    SafetyWarningItem,
    SafetyWarningsData,
    ScorecardHighlight,
    ScorecardSnapshotData,
    ScorecardSnapshotHighlights,
    TruthPillData,
    RecentIncidentsData,
)
from dashboard.services.digest.source_map import DIGEST_SOURCE_MAP
from dashboard.services.digest.utils import (
    age_seconds as _age_seconds,
    base_section as _base_section,
    coerce_float as _coerce_float,
    fmt_age as _fmt_age,
    fmt_num as _fmt_num,
    fmt_pct as _fmt_pct,
    fmt_pct_abs as _fmt_pct_abs,
    freshness_state_from_age as _freshness_state_from_age,
    freshness_state_from_label as _freshness_state_from_label,
    health_from_freshness as _health_from_freshness,
    normalize_health_state as _normalize_health_state,
    pill as _pill,
    utc_iso as _utc_iso,
)
from dashboard.services.operator import get_operations_snapshot
from dashboard.services.operator_tools import synthetic_ohlcv
from dashboard.services.strategy_evaluation import build_strategy_workbench
from services.admin.config_editor import load_user_yaml
from services.config_loader import load_runtime_trading_config
from services.admin.live_guard import live_allowed
from services.admin.system_guard import get_state as get_system_guard_state
from services.bot.start_manager import decide_start
from services.execution.live_arming import is_live_enabled, live_enabled_and_armed

from services.governance.claim_boundaries import CLAIM_BOUNDARIES  # noqa: F401 (canonical source)
_SEVERITY_RANK = {"critical": 0, "important": 1, "watch": 2, "info": 3}


def _system_guard_health(state: str) -> HealthState:
    normalized = str(state or "").strip().upper()
    if normalized == "RUNNING":
        return "ok"
    if normalized == "HALTING":
        return "warn"
    if normalized == "HALTED":
        return "critical"
    return "unknown"


def _system_guard_label(state: str) -> str:
    return str(state or "unknown").strip().replace("_", " ").title()


def _system_guard_caveat(payload: dict[str, Any]) -> str | None:
    writer = str(payload.get("writer") or "").strip()
    reason = str(payload.get("reason") or "").strip()
    parts: list[str] = []
    if writer:
        parts.append(f"writer={writer}")
    if reason:
        parts.append(f"reason={reason}")
    return " · ".join(parts) or None


def _load_trading_cfg() -> dict[str, Any]:
    return load_runtime_trading_config()


def _runtime_mode_meta(trading_cfg: dict[str, Any]) -> tuple[RuntimeModeValue, str, str]:
    execution_cfg = trading_cfg.get("execution") if isinstance(trading_cfg.get("execution"), dict) else {}
    mode = str(trading_cfg.get("mode") or execution_cfg.get("executor_mode") or "paper").strip().lower()
    live_cfg = trading_cfg.get("live") if isinstance(trading_cfg.get("live"), dict) else {}
    sandbox = bool(live_cfg.get("sandbox", True))
    if mode != "live":
        return "paper", "Paper", "Merged runtime config keeps the runtime in paper mode."
    if sandbox:
        return "sandbox_live", "Sandbox Live", "Merged runtime config requests live mode with sandbox enabled."
    return "real_live", "Real Live", "Merged runtime config requests real live mode and needs explicit confirmations."


def _configured_strategy_name(user_cfg: dict[str, Any], trading_cfg: dict[str, Any]) -> str:
    strategy_cfg = user_cfg.get("strategy") if isinstance(user_cfg.get("strategy"), dict) else {}
    pipeline_cfg = user_cfg.get("pipeline") if isinstance(user_cfg.get("pipeline"), dict) else {}
    trading_strategy = trading_cfg.get("strategy") if isinstance(trading_cfg.get("strategy"), dict) else {}
    for candidate in (
        strategy_cfg.get("name"),
        pipeline_cfg.get("strategy"),
        trading_strategy.get("type"),
    ):
        name = str(candidate or "").strip().lower()
        if name in {"ema_cross", "mean_reversion_rsi", "breakout_donchian"}:
            return name
        if name in {"ema", "ema_crossover"}:
            return "ema_cross"
        if name in {"mean_reversion"}:
            return "mean_reversion_rsi"
        if name in {"breakout", "donchian"}:
            return "breakout_donchian"
    return "ema_cross"


def _strategy_context(*, user_cfg: dict[str, Any], trading_cfg: dict[str, Any]) -> dict[str, Any]:
    configured_strategy = _configured_strategy_name(user_cfg, trading_cfg)
    symbol_rows = list(trading_cfg.get("symbols") or [])
    symbol = str(symbol_rows[0] or "BTC/USD") if symbol_rows else "BTC/USD"
    evidence = load_latest_strategy_evidence()
    if bool(evidence.get("has_artifact")):
        return {
            "configured_strategy": configured_strategy,
            "symbol": symbol,
            "workbench": None,
            "raw_rows": [dict(row) for row in list(evidence.get("rows") or [])],
            "truth_source": "persisted_artifact",
            "source_name": DIGEST_SOURCE_MAP["leaderboard_summary_artifact"],
            "source_as_of": str(evidence.get("as_of") or "") or None,
            "source_age_seconds": evidence.get("age_seconds"),
            "freshness_status": str(evidence.get("freshness_status") or "missing"),
            "caveat": str(evidence.get("caveat") or "Persisted strategy evidence artifact."),
            "artifact_path": str(evidence.get("artifact_path") or ""),
            "window_count": int(evidence.get("window_count") or 0),
            "decisions": [dict(item) for item in list(evidence.get("decisions") or [])],
        }
    workbench = build_strategy_workbench(
        cfg=dict(user_cfg or {}),
        strategy_name=configured_strategy,
        symbol=symbol,
        candles=synthetic_ohlcv(180),
        warmup_bars=50,
        initial_cash=10_000.0,
        fee_bps=10.0,
        slippage_bps=5.0,
    )
    raw_rows = list(((workbench.get("leaderboard") or {}).get("rows") or []))
    return {
        "configured_strategy": configured_strategy,
        "symbol": symbol,
        "workbench": workbench,
        "raw_rows": raw_rows,
        "truth_source": "synthetic_fallback",
        "source_name": DIGEST_SOURCE_MAP["leaderboard_summary_fallback"],
        "source_as_of": None,
        "source_age_seconds": None,
        "freshness_status": "missing",
        "caveat": "Persisted strategy evidence artifact is unavailable; digest is using labeled synthetic fallback built on demand.",
        "artifact_path": str(evidence.get("artifact_path") or ""),
        "window_count": 0,
        "decisions": [],
    }


def _regime_extremes(row: dict[str, Any]) -> tuple[str | None, str | None]:
    scores = dict(row.get("regime_scorecards") or {})
    represented = [
        (regime, dict(payload or {}))
        for regime, payload in scores.items()
        if int((payload or {}).get("bars") or 0) > 0
    ]
    if not represented:
        return None, None
    represented.sort(key=lambda item: _coerce_float(item[1].get("net_return_after_costs_pct"), 0.0), reverse=True)
    best = represented[0][0]
    worst = represented[-1][0]
    return best, worst


def _drift_label(value: Any) -> str:
    if value is None:
        return "unknown"
    drift = abs(_coerce_float(value, 0.0))
    if drift <= 1.0:
        return "low"
    if drift <= 5.0:
        return "medium"
    return "high"


def _recommendation_for_row(row: dict[str, Any]) -> str:
    explicit = str(row.get("decision") or "").strip().lower()
    if explicit in {"keep", "improve", "freeze", "retire"}:
        return explicit
    rank = int(row.get("rank") or 0)
    ret = _coerce_float(row.get("net_return_after_costs_pct"), 0.0)
    drawdown = _coerce_float(row.get("max_drawdown_pct"), 0.0)
    robustness = _coerce_float(row.get("regime_robustness"), 0.0)
    slippage = _coerce_float(row.get("slippage_sensitivity_pct"), 0.0)
    if ret < 0.0 or drawdown >= 10.0:
        return "retire"
    if robustness < 0.4 or slippage >= 6.0:
        return "improve"
    if rank == 1 and ret >= 0.0 and robustness >= 0.6:
        return "keep"
    return "freeze"


def _evidence_note_for_row(row: dict[str, Any]) -> str:
    note = str(row.get("evidence_note") or "").strip()
    if note:
        return note
    status = str(row.get("evidence_status") or "").strip().lower()
    if status == "paper_supported":
        return "Persisted paper-history supports the current research decision, but the sample is still not promotion-grade."
    if status == "paper_thin":
        return "Persisted paper-history exists, but the sample is still too thin to confirm the synthetic ranking."
    if status == "synthetic_only":
        return "Persisted paper-history is missing, so the decision still relies on synthetic windows."
    if status == "insufficient":
        return "No realized closed-trade participation exists across the current evidence windows."
    return ""


def _strategy_feedback_note_for_row(row: dict[str, Any]) -> str:
    feedback = dict(row.get("strategy_feedback") or {})
    return str(feedback.get("summary_text") or "").strip()


def _feedback_weighting_note_for_row(row: dict[str, Any]) -> str:
    weighting = dict(row.get("feedback_weighting") or {})
    return str(weighting.get("summary") or "").strip()


def _top_row_research_acceptance_blockers(row: dict[str, Any]) -> list[str]:
    paper_history = dict(row.get("paper_history") or {})
    evidence_status = str(row.get("evidence_status") or "").strip().lower()
    confidence_label = str(row.get("confidence_label") or "").strip().lower()
    paper_closed_trades = int(paper_history.get("closed_trades") or row.get("closed_trades") or 0)
    represented_windows = int(row.get("closed_trade_window_count") or 0)
    post_cost_return = _coerce_float(row.get("net_return_after_costs_pct"), _coerce_float(row.get("avg_return_pct"), 0.0))
    slippage_sensitivity = _coerce_float(row.get("slippage_sensitivity_pct"), 0.0)
    stressed_post_cost_return = post_cost_return - slippage_sensitivity
    max_drawdown = _coerce_float(row.get("max_drawdown_pct"), 0.0)

    blockers: list[str] = []
    if paper_closed_trades < 30:
        blockers.append(f"Persisted paper history only shows {paper_closed_trades} closed trade(s); research floor is 30.")
    if represented_windows < 3:
        blockers.append(f"Only {represented_windows} represented window(s) produced realized participation; research floor is 3.")
    if post_cost_return <= 0.0:
        blockers.append("Post-cost return is not positive.")
    if stressed_post_cost_return <= 0.0:
        blockers.append("Stressed slippage turns the current post-cost result non-positive.")
    if max_drawdown > 10.0:
        blockers.append(f"Max drawdown is {max_drawdown:.2f}%; research floor is 10.00% or less.")
    if evidence_status != "paper_supported":
        blockers.append(f"Evidence status is {evidence_status or 'unknown'}; research floor requires paper_supported.")
    if confidence_label not in {"medium", "high"}:
        blockers.append(f"Confidence is {confidence_label or 'unknown'}; research floor requires at least medium.")
    return blockers


def _candidate_title(value: Any) -> str:
    return str(value or "Unknown").replace("_", " ").title()


def _runtime_context(*, trading_cfg: dict[str, Any], user_cfg: dict[str, Any]) -> dict[str, Any]:
    mode_value, mode_label, mode_note = _runtime_mode_meta(trading_cfg)
    live_cfg = trading_cfg.get("live") if isinstance(trading_cfg.get("live"), dict) else {}
    sandbox = bool(live_cfg.get("sandbox", True))
    normalized_live_enabled = bool(is_live_enabled(user_cfg))
    try:
        start_decision = decide_start("live", trading_cfg) if mode_value != "paper" else decide_start("paper", trading_cfg)
    except Exception as exc:
        start_decision = type(
            "StartDecisionFallback",
            (),
            {"ok": False, "mode": str(mode_value), "status": "BLOCK", "reasons": [f"decide_start_failed:{type(exc).__name__}"], "note": "Runtime start decision unavailable."},
        )()

    try:
        guard_allowed, guard_reason, guard_details = live_allowed()
    except Exception as exc:
        guard_allowed, guard_reason, guard_details = False, f"live_guard_failed:{type(exc).__name__}", {}
    try:
        armed, arming_reason = live_enabled_and_armed()
    except Exception as exc:
        armed, arming_reason = False, f"arming_failed:{type(exc).__name__}"
    try:
        system_guard = dict(get_system_guard_state(fail_closed=True) or {})
    except Exception as exc:
        system_guard = {
            "state": "HALTED",
            "writer": "digest",
            "reason": f"system_guard_failed:{type(exc).__name__}",
            "epoch": 0,
        }

    kill_state = dict(guard_details.get("kill_switch") or {}) if isinstance(guard_details, dict) else {}
    kill_armed = bool(kill_state.get("armed", False))
    system_guard_state = str(system_guard.get("state") or "UNKNOWN").strip().upper()
    return {
        "mode_value": mode_value,
        "mode_label": mode_label,
        "mode_note": mode_note,
        "sandbox": sandbox,
        "normalized_live_enabled": normalized_live_enabled,
        "start_decision": start_decision,
        "guard_allowed": bool(guard_allowed),
        "guard_reason": str(guard_reason or "unknown"),
        "guard_details": dict(guard_details or {}),
        "armed": bool(armed),
        "arming_reason": str(arming_reason or "unknown"),
        "kill_armed": kill_armed,
        "system_guard": system_guard,
        "system_guard_state": system_guard_state,
    }


def build_runtime_truth_digest(
    *,
    as_of: str,
    runtime_context: dict[str, Any],
    structural_health: dict[str, Any],
    collector_runtime: dict[str, Any],
    strategy_context: dict[str, Any],
) -> RuntimeTruthData:
    mode_value = str(runtime_context.get("mode_value") or "unknown")
    mode_label = str(runtime_context.get("mode_label") or "Unknown")
    mode_note = str(runtime_context.get("mode_note") or "No runtime summary available.")
    if mode_value == "paper":
        mode_state: HealthState = "ok"
    elif str(runtime_context.get("start_decision").status if hasattr(runtime_context.get("start_decision"), "status") else "").upper() == "BLOCK":
        mode_state = "warn"
    else:
        mode_state = "ok"

    kill_armed = bool(runtime_context.get("kill_armed"))
    system_guard = dict(runtime_context.get("system_guard") or {})
    system_guard_state = str(runtime_context.get("system_guard_state") or "UNKNOWN").strip().upper()
    kill_switch = _pill(
        value="Armed" if kill_armed else "Disarmed",
        label="Kill Switch",
        state="critical" if kill_armed else "ok",
        caveat=str(runtime_context.get("guard_reason") or "") if kill_armed else None,
    )
    system_guard_pill = _pill(
        value=_system_guard_label(system_guard_state),
        label="System Guard",
        state=_system_guard_health(system_guard_state),
        caveat=_system_guard_caveat(system_guard),
    )

    if mode_value == "paper":
        boundary_value = "Healthy"
        boundary_state = "ok"
        boundary_caveat = "Final live-order boundary is present but inactive while runtime remains in paper mode."
    elif system_guard_state in {"HALTING", "HALTED"}:
        boundary_value = "Blocked"
        boundary_state = _system_guard_health(system_guard_state)
        boundary_caveat = (
            f"System Guard is {_system_guard_label(system_guard_state).lower()}; "
            "live submit is fail-closed until the shared guard returns to running."
        )
    elif bool(runtime_context.get("guard_allowed")):
        boundary_value = "Healthy"
        boundary_state = "ok"
        boundary_caveat = "Outer live gate and final boundary both allow guarded submission paths."
    else:
        boundary_value = "Blocked"
        boundary_state = "critical" if kill_armed else "warn"
        boundary_caveat = str(getattr(runtime_context.get("start_decision"), "note", "") or runtime_context.get("guard_reason") or "Live boundary status unavailable.")

    collector_age = _age_seconds(collector_runtime.get("ts"))
    collector_freshness_state = _freshness_state_from_label(
        collector_runtime.get("freshness"),
        age_seconds=collector_age,
    )
    collector_value = {
        "fresh": "Fresh",
        "aging": "Aging",
        "stale": "Stale",
        "missing": "Missing",
        "not_active": "Not Active",
    }[collector_freshness_state]

    strategy_truth_source = str(strategy_context.get("truth_source") or "synthetic_fallback")
    strategy_truth_age = strategy_context.get("source_age_seconds")
    if strategy_truth_source == "persisted_artifact":
        leaderboard_pill = _pill(
            value=_fmt_age(strategy_truth_age),
            label="Leaderboard Age",
            state=_health_from_freshness(str(strategy_context.get("freshness_status") or "missing")),  # type: ignore[arg-type]
            caveat=str(strategy_context.get("caveat") or "Persisted strategy evidence artifact."),
            age_seconds=strategy_truth_age if isinstance(strategy_truth_age, int) else None,
        )
    else:
        leaderboard_pill = _pill(
            value="Fallback",
            label="Leaderboard Age",
            state="warn",
            caveat=str(strategy_context.get("caveat") or "Persisted evidence is unavailable; synthetic fallback was rebuilt on demand."),
            age_seconds=None,
        )

    trust_caveat = "Copilot answer-level provenance is present on the inspected gateway path, but not yet proven universal across every future surface."
    return RuntimeTruthData(
        **_base_section(
            as_of=as_of,
            caveat="Runtime truth reflects config, guard posture, and read-only freshness summaries.",
            source_name=DIGEST_SOURCE_MAP["runtime_truth"],
            source_age_seconds=max(filter(lambda x: x is not None, [collector_age]), default=None),
        ),
        mode=_pill(value=mode_label, label="Runtime Mode", state=mode_state, caveat=mode_note),
        live_order_authority=_pill(
            value=boundary_value,
            label="Live-Order Authority",
            state=boundary_state,
            caveat=boundary_caveat,
        ),
        kill_switch=kill_switch,
        system_guard=system_guard_pill,
        collector_freshness=_pill(
            value=collector_value,
            label="Collector Freshness",
            state=_health_from_freshness(collector_freshness_state),
            caveat=str(collector_runtime.get("summary_text") or structural_health.get("summary_text") or "No collector summary available."),
            age_seconds=collector_age,
        ),
        leaderboard_age=leaderboard_pill,
        copilot_trust_layer=_pill(
            value="Partial",
            label="Copilot Trust Layer",
            state="warn",
            caveat=trust_caveat,
        ),
    )


def _build_attention_candidates(
    *,
    as_of: str,
    overview_summary: dict[str, Any],
    runtime_context: dict[str, Any],
    strategy_context: dict[str, Any],
    structural_health: dict[str, Any],
    structural_digest: dict[str, Any],
    collector_runtime: dict[str, Any],
    operations_snapshot: dict[str, Any],
) -> list[AttentionItem]:
    items: list[AttentionItem] = []
    mode_value = str(runtime_context.get("mode_value") or "unknown")
    mode_label = str(runtime_context.get("mode_label") or "Unknown")
    start_decision = runtime_context.get("start_decision")
    start_note = str(getattr(start_decision, "note", "") or "").strip()
    start_reasons = [str(item) for item in list(getattr(start_decision, "reasons", []) or [])]

    if mode_value == "paper":
        items.append(
            {
                "id": "mode-paper",
                "severity": "watch",
                "title": "Runtime is paper-first",
                "why_it_matters": "The repo remains paper-heavy by default; live posture is not active.",
                "next_action": "Use paper or sandbox evidence before considering any guarded live promotion.",
                "source": "mode",
                "as_of": as_of,
                "link_target": "/Overview",
            }
        )

    strategy_truth_source = str(strategy_context.get("truth_source") or "synthetic_fallback")
    if strategy_truth_source != "persisted_artifact":
        items.append(
            {
                "id": "strategy-evidence-fallback",
                "severity": "watch",
                "title": "Persisted strategy evidence is unavailable",
                "why_it_matters": str(strategy_context.get("caveat") or "Digest is relying on labeled synthetic fallback strategy truth."),
                "next_action": "Run `make strategy-evidence-cycle` before relying on strategy rankings or promotion readiness.",
                "source": "strategy_evidence",
                "as_of": as_of,
                "link_target": "/Home",
            }
        )
    elif str(strategy_context.get("freshness_status") or "") == "stale":
        items.append(
            {
                "id": "strategy-evidence-stale",
                "severity": "watch",
                "title": "Persisted strategy evidence is stale",
                "why_it_matters": str(strategy_context.get("caveat") or "The saved strategy evidence artifact is old enough to challenge current operator confidence."),
                "next_action": "Rerun `make strategy-evidence-cycle` before using the digest for promotion or strategy decisions.",
                "source": "strategy_evidence",
                "as_of": as_of,
                "link_target": "/Home",
            }
        )
    top_raw_rows = [dict(row) for row in list(strategy_context.get("raw_rows") or []) if isinstance(row, dict)]
    if top_raw_rows:
        top_row = top_raw_rows[0]
        top_evidence_status = str(top_row.get("evidence_status") or "").strip().lower()
        if top_evidence_status in {"synthetic_only", "paper_thin", "insufficient"}:
            items.append(
                {
                    "id": f"strategy-evidence-{top_evidence_status}",
                    "severity": "important" if top_evidence_status == "paper_thin" else "watch",
                    "title": f"Top strategy evidence is {top_evidence_status.replace('_', ' ')}",
                    "why_it_matters": _evidence_note_for_row(top_row) or "Current strategy evidence is too weak for promotion review.",
                    "next_action": "Collect more real paper-history evidence, then rerun `make strategy-evidence-cycle`.",
                    "source": "strategy_evidence",
                    "as_of": as_of,
                    "link_target": "/Home",
                }
            )
        research_blockers = _top_row_research_acceptance_blockers(top_row)
        if research_blockers:
            items.append(
                {
                    "id": "strategy-research-not-accepted",
                    "severity": "important",
                    "title": "Top strategy is not research-accepted",
                    "why_it_matters": str(top_row.get("evidence_note") or research_blockers[0] or "Current strategy evidence is still too thin to treat as a credible edge."),
                    "next_action": "Finish the evidence cycle and clear the research-acceptance blockers before treating the current edge claim as credible.",
                    "source": "strategy_evidence",
                    "as_of": as_of,
                    "link_target": "/Copilot_Reports",
                }
            )
    if not bool(getattr(start_decision, "ok", False)):
        items.append(
            {
                "id": "live-start-blocked",
                "severity": "critical" if mode_label == "Real Live" else "important",
                "title": f"{mode_label} start is blocked",
                "why_it_matters": start_note or "Runtime start gate is blocking the requested mode.",
                "next_action": "Review the live-mode blockers before changing execution posture.",
                "source": "mode",
                "as_of": as_of,
                "link_target": "/Operations",
            }
        )

    if mode_value != "paper" and not bool(runtime_context.get("armed")):
        items.append(
            {
                "id": "live-not-armed",
                "severity": "important",
                "title": "Live path is not armed",
                "why_it_matters": f"Arming state is {str(runtime_context.get('arming_reason') or 'unknown')}",
                "next_action": "Keep runtime in research-safe posture until arming is explicit and reviewed.",
                "source": "safety",
                "as_of": as_of,
                "link_target": "/Operations",
            }
        )

    if bool(runtime_context.get("kill_armed")):
        items.append(
            {
                "id": "kill-switch-armed",
                "severity": "critical",
                "title": "Kill switch is armed",
                "why_it_matters": "Live submission is fail-closed while the kill switch stays armed.",
                "next_action": "Review the kill-switch source and clear it only after confirming the safety posture.",
                "source": "safety",
                "as_of": as_of,
                "link_target": "/Operations",
            }
        )

    blocked_trades = int(overview_summary.get("blocked_trades_count") or 0)
    if blocked_trades > 0:
        items.append(
            {
                "id": "blocked-trades",
                "severity": "important",
                "title": f"{blocked_trades} trade(s) are blocked",
                "why_it_matters": "The current risk policy is actively preventing trade progression.",
                "next_action": "Review blocked-trade reasons before changing mode or risk posture.",
                "source": "risk",
                "as_of": as_of,
                "link_target": "/Trades",
            }
        )

    for idx, warning in enumerate(list(overview_summary.get("active_warnings") or [])[:3]):
        text = str(warning or "").strip()
        if text:
            items.append(
                {
                    "id": f"warning-{idx}",
                    "severity": "watch",
                    "title": text[:96],
                    "why_it_matters": text,
                    "next_action": "Review the current workspace warning before escalating execution or promotion decisions.",
                    "source": "risk",
                    "as_of": as_of,
                    "link_target": "/Overview",
                }
            )

    if bool(structural_health.get("needs_attention")):
        items.append(
            {
                "id": "structural-stale",
                "severity": "important",
                "title": "Structural-edge freshness needs attention",
                "why_it_matters": str(structural_health.get("summary_text") or "Structural-edge freshness is degraded."),
                "next_action": str(structural_health.get("action_text") or "Refresh the read-only collector loop."),
                "source": "collector",
                "as_of": as_of,
                "link_target": "/Research",
            }
        )
    elif bool(structural_digest.get("needs_attention")):
        items.append(
            {
                "id": "structural-digest",
                "severity": "watch",
                "title": str(structural_digest.get("headline") or "Structural-edge digest needs review"),
                "why_it_matters": str(structural_digest.get("while_away_summary") or "Structural-edge status changed while you were away."),
                "next_action": str(structural_digest.get("action_text") or "Review the latest research snapshot."),
                "source": "collector",
                "as_of": as_of,
                "link_target": "/Research",
            }
        )

    attention_services = int(operations_snapshot.get("attention_services") or 0)
    if attention_services > 0:
        items.append(
            {
                "id": "ops-attention",
                "severity": "important",
                "title": f"{attention_services} service(s) need operator attention",
                "why_it_matters": "Tracked service health is degraded or failed.",
                "next_action": "Review the Operations workspace before relying on stale or degraded runtime state.",
                "source": "operations",
                "as_of": as_of,
                "link_target": "/Operations",
            }
        )

    unknown_services = int(operations_snapshot.get("unknown_services") or 0)
    if unknown_services > 0:
        items.append(
            {
                "id": "ops-unknown",
                "severity": "watch",
                "title": f"{unknown_services} service(s) have unknown health",
                "why_it_matters": "Telemetry freshness is incomplete for part of the operator surface.",
                "next_action": "Inspect service health and refresh diagnostics before trusting missing telemetry.",
                "source": "operations",
                "as_of": as_of,
                "link_target": "/Operations",
            }
        )

    collector_errors = int(collector_runtime.get("errors") or 0)
    if collector_errors > 0:
        items.append(
            {
                "id": "collector-errors",
                "severity": "important",
                "title": f"Collector loop reported {collector_errors} error(s)",
                "why_it_matters": str(collector_runtime.get("summary_text") or "Collector runtime is degraded."),
                "next_action": "Review collector runtime and restart the read-only loop if needed.",
                "source": "collector",
                "as_of": as_of,
                "link_target": "/Research",
            }
        )

    deduped: list[AttentionItem] = []
    seen: set[str] = set()
    for item in items:
        key = f"{item['title']}::{item['why_it_matters']}"
        if key not in seen:
            seen.add(key)
            deduped.append(item)
    deduped.sort(
        key=lambda item: (
            _SEVERITY_RANK.get(str(item.get("severity") or "info"), 99),
            str(item.get("as_of") or ""),
        )
    )
    return deduped[:5]


def build_attention_now_digest(
    *,
    as_of: str,
    overview_summary: dict[str, Any],
    runtime_context: dict[str, Any],
    strategy_context: dict[str, Any],
    structural_health: dict[str, Any],
    structural_digest: dict[str, Any],
    collector_runtime: dict[str, Any],
    operations_snapshot: dict[str, Any],
) -> AttentionNowData:
    items = _build_attention_candidates(
        as_of=as_of,
        overview_summary=overview_summary,
        runtime_context=runtime_context,
        strategy_context=strategy_context,
        structural_health=structural_health,
        structural_digest=structural_digest,
        collector_runtime=collector_runtime,
        operations_snapshot=operations_snapshot,
    )
    if not items:
        items = [
            {
                "id": "attention-clear",
                "severity": "info",
                "title": "No urgent items right now",
                "why_it_matters": "Current summaries do not show any critical operator action.",
                "next_action": "Review the top strategy snapshot and structural freshness before making changes.",
                "source": "digest",
                "as_of": as_of,
                "link_target": "/Overview",
            }
        ]
    return AttentionNowData(
        **_base_section(
            as_of=as_of,
            caveat="Attention items are sorted by severity first, then recency at digest build time.",
            source_name=DIGEST_SOURCE_MAP["attention_now"],
            source_age_seconds=0,
        ),
        items=items,
    )


def build_leaderboard_summary_digest(*, as_of: str, strategy_context: dict[str, Any]) -> LeaderboardSummaryData:
    raw_rows = list(strategy_context.get("raw_rows") or [])
    row_as_of = str(strategy_context.get("source_as_of") or as_of)
    source_name = str(strategy_context.get("source_name") or DIGEST_SOURCE_MAP["leaderboard_summary_fallback"])
    caveat = str(strategy_context.get("caveat") or "Strategy truth is unavailable.")
    rows: list[LeaderboardStrategyRow] = []
    for raw in raw_rows[:5]:
        best_regime, worst_regime = _regime_extremes(raw)
        row_caveat_parts = [
            part
            for part in (
                _evidence_note_for_row(raw),
                _strategy_feedback_note_for_row(raw),
                _feedback_weighting_note_for_row(raw),
                caveat,
            )
            if part
        ]
        rows.append(
            {
                "strategy_id": str(raw.get("strategy") or raw.get("candidate") or "unknown"),
                "name": _candidate_title(raw.get("candidate") or raw.get("strategy") or "Unknown"),
                "rank": int(raw.get("rank") or 0) or None,
                "score": _coerce_float(raw.get("leaderboard_score"), 0.0),
                "score_label": f"{_coerce_float(raw.get('leaderboard_score'), 0.0):.2f}",
                "post_cost_return_pct": _coerce_float(raw.get("net_return_after_costs_pct"), 0.0),
                "max_drawdown_pct": _coerce_float(raw.get("max_drawdown_pct"), 0.0),
                "closed_trades": int(_coerce_float(raw.get("closed_trades"), 0.0)),
                "best_regime": best_regime,
                "worst_regime": worst_regime,
                "paper_live_drift": _drift_label(raw.get("paper_live_drift_pct")),
                "recommendation": _recommendation_for_row(raw),
                "as_of": row_as_of,
                "caveat": " ".join(row_caveat_parts),
            }
        )
    return LeaderboardSummaryData(
        **_base_section(
            as_of=as_of,
            caveat=caveat,
            source_name=source_name,
            source_age_seconds=strategy_context.get("source_age_seconds"),
        ),
        rows=rows,
    )


def _empty_highlight(label: str, caveat: str) -> ScorecardHighlight:
    return {
        "label": label,
        "strategy_name": None,
        "value": None,
        "context": None,
        "state": "unknown",
        "caveat": caveat,
    }


def _highlight_for_row(
    *,
    label: str,
    row: dict[str, Any],
    value: str,
    context: str,
    state: HealthState,
    caveat: str | None = None,
) -> ScorecardHighlight:
    return {
        "label": label,
        "strategy_name": _candidate_title(row.get("candidate") or row.get("strategy") or "Unknown"),
        "value": value,
        "context": context,
        "state": state,
        "caveat": caveat,
    }


def build_scorecard_snapshot_digest(*, as_of: str, strategy_context: dict[str, Any]) -> ScorecardSnapshotData:
    raw_rows = list(strategy_context.get("raw_rows") or [])
    source_name = (
        DIGEST_SOURCE_MAP["scorecard_snapshot_artifact"]
        if str(strategy_context.get("truth_source") or "") == "persisted_artifact"
        else DIGEST_SOURCE_MAP["scorecard_snapshot_fallback"]
    )
    caveat = str(strategy_context.get("caveat") or "Strategy scorecard truth is unavailable.")
    if not raw_rows:
        highlights: ScorecardSnapshotHighlights = {
            "best_post_cost": _empty_highlight("Best post-cost performer", "Run strategy evaluation first."),
            "lowest_drawdown": _empty_highlight("Lowest drawdown", "Run strategy evaluation first."),
            "most_regime_fragile": _empty_highlight("Most regime-fragile", "Run strategy evaluation first."),
            "most_slippage_sensitive": _empty_highlight("Most slippage-sensitive", "Run strategy evaluation first."),
            "most_stable": _empty_highlight("Most stable", "Run strategy evaluation first."),
            "most_changed": _empty_highlight("Most changed", "No persisted leaderboard delta is available yet."),
        }
    else:
        best_post_cost = max(raw_rows, key=lambda row: _coerce_float(row.get("net_return_after_costs_pct"), 0.0))
        lowest_drawdown = min(raw_rows, key=lambda row: _coerce_float(row.get("max_drawdown_pct"), 0.0))
        most_fragile = min(
            raw_rows,
            key=lambda row: (
                _coerce_float(row.get("regime_robustness"), 0.0),
                -_coerce_float(row.get("regime_return_dispersion_pct"), 0.0),
            ),
        )
        most_slippage = max(raw_rows, key=lambda row: _coerce_float(row.get("slippage_sensitivity_pct"), 0.0))
        most_stable = max(
            raw_rows,
            key=lambda row: (
                _coerce_float(row.get("regime_robustness"), 0.0),
                -_coerce_float(row.get("regime_return_dispersion_pct"), 0.0),
                -_coerce_float(row.get("max_drawdown_pct"), 0.0),
            ),
        )
        highlights = {
            "best_post_cost": _highlight_for_row(
                label="Best post-cost performer",
                row=best_post_cost,
                value=_fmt_pct(best_post_cost.get("net_return_after_costs_pct")),
                context="after fees/slippage",
                state="ok" if _coerce_float(best_post_cost.get("net_return_after_costs_pct"), 0.0) >= 0.0 else "warn",
            ),
            "lowest_drawdown": _highlight_for_row(
                label="Lowest drawdown",
                row=lowest_drawdown,
                value=_fmt_pct_abs(lowest_drawdown.get("max_drawdown_pct")),
                context="peak-to-trough loss",
                state="ok" if _coerce_float(lowest_drawdown.get("max_drawdown_pct"), 0.0) <= 5.0 else "warn",
            ),
            "most_regime_fragile": _highlight_for_row(
                label="Most regime-fragile",
                row=most_fragile,
                value=f"{_coerce_float(most_fragile.get('regime_robustness'), 0.0):.2f}",
                context="regime robustness",
                state="warn",
            ),
            "most_slippage_sensitive": _highlight_for_row(
                label="Most slippage-sensitive",
                row=most_slippage,
                value=_fmt_pct_abs(most_slippage.get("slippage_sensitivity_pct")),
                context="return loss under stressed slippage",
                state="warn" if _coerce_float(most_slippage.get("slippage_sensitivity_pct"), 0.0) >= 3.0 else "ok",
            ),
            "most_stable": _highlight_for_row(
                label="Most stable",
                row=most_stable,
                value=f"{_coerce_float(most_stable.get('regime_robustness'), 0.0):.2f}",
                context="robustness across represented regimes",
                state="ok",
            ),
            "most_changed": _empty_highlight("Most changed", "No persisted leaderboard delta is available yet."),
        }
    return ScorecardSnapshotData(
        **_base_section(
            as_of=as_of,
            caveat=caveat,
            source_name=source_name,
            source_age_seconds=strategy_context.get("source_age_seconds"),
        ),
        highlights=highlights,
    )


def build_crypto_edge_summary_digest(*, as_of: str, live_snapshot: dict[str, Any]) -> CryptoEdgeSummaryData:
    meta_map = {
        "funding": {
            "name": "Funding analytics",
            "meta": dict(live_snapshot.get("funding_meta") or {}),
            "summary": f"Bias {str((live_snapshot.get('funding') or {}).get('dominant_bias') or 'flat').replace('_', ' ').title()} / carry {float(((live_snapshot.get('funding') or {}).get('annualized_carry_pct') or 0.0)):.2f}%"
            if isinstance(live_snapshot.get("funding"), dict)
            else None,
        },
        "basis": {
            "name": "Basis monitor",
            "meta": dict(live_snapshot.get("basis_meta") or {}),
            "summary": f"Average basis {float(((live_snapshot.get('basis') or {}).get('avg_basis_bps') or 0.0)):.2f} bps"
            if isinstance(live_snapshot.get("basis"), dict)
            else None,
        },
        "dislocations": {
            "name": "Cross-venue dislocation",
            "meta": dict(live_snapshot.get("quote_meta") or {}),
            "summary": f"Positive gaps {int(((live_snapshot.get('dislocations') or {}).get('positive_count') or 0))}"
            if isinstance(live_snapshot.get("dislocations"), dict)
            else None,
        },
    }
    rows: list[CryptoEdgeModuleRow] = []
    section_ages: list[int] = []
    report_reason = str(live_snapshot.get("reason") or "")
    for module_id, item in meta_map.items():
        meta = dict(item.get("meta") or {})
        capture_ts = meta.get("capture_ts")
        age = _age_seconds(capture_ts)
        if age is not None:
            section_ages.append(age)
        status = _freshness_state_from_age(age) if capture_ts else "missing"
        caveat = None
        if not capture_ts:
            caveat = "No live-public snapshot stored yet." if bool(live_snapshot.get("ok")) else report_reason or "Live-public snapshot unavailable."
        rows.append(
            {
                "module_id": module_id,
                "name": str(item.get("name") or module_id),
                "status": status,
                "last_update_ts": str(capture_ts) if capture_ts else None,
                "age_seconds": age,
                "summary": str(item.get("summary") or "Not yet active" if status == "not_active" else item.get("summary") or "Missing"),
                "caveat": caveat,
            }
        )
    return CryptoEdgeSummaryData(
        **_base_section(
            as_of=as_of,
            caveat="Rows track live-public research freshness only; missing rows mean snapshots are unavailable, not that the feature is unsupported.",
            source_name=DIGEST_SOURCE_MAP["crypto_edge_summary"],
            source_age_seconds=max(section_ages) if section_ages else None,
        ),
        rows=rows,
    )


def build_safety_warnings_digest(
    *,
    as_of: str,
    overview_summary: dict[str, Any],
    runtime_context: dict[str, Any],
    strategy_context: dict[str, Any],
    structural_health: dict[str, Any],
    collector_runtime: dict[str, Any],
    operations_snapshot: dict[str, Any],
) -> SafetyWarningsData:
    items: list[SafetyWarningItem] = []
    mode_value = str(runtime_context.get("mode_value") or "unknown")
    start_decision = runtime_context.get("start_decision")
    system_guard = dict(runtime_context.get("system_guard") or {})
    system_guard_state = str(runtime_context.get("system_guard_state") or "UNKNOWN").strip().upper()
    if bool(runtime_context.get("kill_armed")):
        items.append(
            {
                "severity": "critical",
                "title": "Kill switch is armed",
                "summary": "The final live-order boundary will fail closed until the kill switch is cleared.",
                "source": "live_guard",
                "as_of": as_of,
                "caveat": str(runtime_context.get("guard_reason") or None),
            }
        )
    if system_guard_state in {"HALTING", "HALTED"}:
        items.append(
            {
                "severity": "important" if system_guard_state == "HALTING" else "critical",
                "title": f"System Guard is {_system_guard_label(system_guard_state)}",
                "summary": "Live submit is fail-closed on the shared guard state until the runtime returns to RUNNING.",
                "source": "system_guard",
                "as_of": as_of,
                "caveat": _system_guard_caveat(system_guard),
            }
        )
    if mode_value != "paper" and not bool(getattr(start_decision, "ok", False)):
        items.append(
            {
                "severity": "important",
                "title": "Requested live mode is blocked",
                "summary": str(getattr(start_decision, "note", "") or "Runtime start gate is blocking live mode."),
                "source": "start_manager",
                "as_of": as_of,
                "caveat": ", ".join(str(item) for item in list(getattr(start_decision, "reasons", []) or [])) or None,
            }
        )
    strategy_rows = [dict(row) for row in list(strategy_context.get("raw_rows") or []) if isinstance(row, dict)]
    if strategy_rows:
        top_row = strategy_rows[0]
        top_evidence_status = str(top_row.get("evidence_status") or "").strip().lower()
        if top_evidence_status in {"synthetic_only", "paper_thin", "insufficient"}:
            items.append(
                {
                    "severity": "watch",
                    "title": "Promotion evidence is not paper-supported",
                    "summary": _evidence_note_for_row(top_row) or "Top strategy evidence is too weak for promotion review.",
                    "source": "strategy_evidence",
                    "as_of": as_of,
                    "caveat": None,
                }
            )
    if bool(structural_health.get("needs_attention")):
        items.append(
            {
                "severity": "watch",
                "title": "Structural research freshness is degraded",
                "summary": str(structural_health.get("summary_text") or "Structural-edge freshness needs attention."),
                "source": "collector",
                "as_of": as_of,
                "caveat": str(structural_health.get("action_text") or None),
            }
        )
    if int(collector_runtime.get("errors") or 0) > 0:
        items.append(
            {
                "severity": "watch",
                "title": "Collector loop reported errors",
                "summary": str(collector_runtime.get("summary_text") or "Collector runtime is degraded."),
                "source": "collector",
                "as_of": as_of,
                "caveat": None,
            }
        )
    if int(operations_snapshot.get("unknown_services") or 0) > 0:
        items.append(
            {
                "severity": "watch",
                "title": "Telemetry is partially missing",
                "summary": f"{int(operations_snapshot.get('unknown_services') or 0)} tracked service(s) have unknown health state.",
                "source": "operations",
                "as_of": as_of,
                "caveat": None,
            }
        )
    if not items:
        items.append(
            {
                "severity": "info",
                "title": "No active safety warnings",
                "summary": "Current summaries do not show a live-boundary or kill-switch escalation.",
                "source": "digest",
                "as_of": as_of,
                "caveat": None,
            }
        )
    live_boundary_status = (
        "healthy"
        if mode_value == "paper" or (bool(runtime_context.get("guard_allowed")) and system_guard_state == "RUNNING")
        else "blocked"
    )
    kill_switch_state = "armed" if bool(runtime_context.get("kill_armed")) else "disarmed"
    return SafetyWarningsData(
        **_base_section(
            as_of=as_of,
            caveat="Warnings stay conservative and do not imply unsupported live capabilities.",
            source_name=DIGEST_SOURCE_MAP["safety_warnings"],
            source_age_seconds=0,
        ),
        items=items[:6],
        live_boundary_status=live_boundary_status,
        kill_switch_state=kill_switch_state,
        system_guard_state=str(system_guard_state or "unknown").lower(),
    )


def build_freshness_panel_digest(
    *,
    as_of: str,
    summary: dict[str, Any],
    collector_runtime: dict[str, Any],
    live_snapshot: dict[str, Any],
    operations_snapshot: dict[str, Any],
    strategy_context: dict[str, Any],
    leaderboard_summary: LeaderboardSummaryData,
    scorecard_snapshot: ScorecardSnapshotData,
) -> FreshnessPanelData:
    rows: list[FreshnessRow] = []
    collector_ts = collector_runtime.get("ts")
    collector_age = _age_seconds(collector_ts)
    rows.append(
        {
            "source_id": "collector_loop",
            "name": "Collector loop",
            "status": _freshness_state_from_label(collector_runtime.get("freshness"), age_seconds=collector_age),
            "last_update_ts": str(collector_ts) if collector_ts else None,
            "age_seconds": collector_age,
            "caveat": str(collector_runtime.get("summary_text") or None),
        }
    )
    module_map = {
        "funding_meta": "Funding analytics",
        "basis_meta": "Basis monitor",
        "quote_meta": "Cross-venue dislocation",
    }
    for meta_key, label in module_map.items():
        meta = dict(live_snapshot.get(meta_key) or {})
        capture_ts = meta.get("capture_ts")
        age = _age_seconds(capture_ts)
        rows.append(
            {
                "source_id": meta_key,
                "name": label,
                "status": _freshness_state_from_age(age) if capture_ts else "missing",
                "last_update_ts": str(capture_ts) if capture_ts else None,
                "age_seconds": age,
                "caveat": None if capture_ts else "No live-public snapshot stored yet.",
            }
        )
    rows.extend(
        [
            {
                "source_id": "strategy_leaderboard",
                "name": "Strategy leaderboard",
                "status": (
                    str(strategy_context.get("freshness_status") or "missing")
                    if str(strategy_context.get("truth_source") or "") == "persisted_artifact"
                    else "missing"
                ),
                "last_update_ts": strategy_context.get("source_as_of"),
                "age_seconds": strategy_context.get("source_age_seconds"),
                "caveat": leaderboard_summary.get("caveat"),
            },
            {
                "source_id": "strategy_scorecard",
                "name": "Strategy scorecard",
                "status": (
                    str(strategy_context.get("freshness_status") or "missing")
                    if str(strategy_context.get("truth_source") or "") == "persisted_artifact"
                    else "missing"
                ),
                "last_update_ts": strategy_context.get("source_as_of"),
                "age_seconds": strategy_context.get("source_age_seconds"),
                "caveat": scorecard_snapshot.get("caveat"),
            },
            {
                "source_id": "paper_pnl",
                "name": "Paper PnL",
                "status": "missing",
                "last_update_ts": None,
                "age_seconds": None,
                "caveat": "No paper PnL timestamp is exposed yet.",
            },
            {
                "source_id": "telemetry_snapshot",
                "name": "Telemetry snapshot",
                "status": _freshness_state_from_age(_age_seconds(operations_snapshot.get("last_health_ts"))),
                "last_update_ts": str(operations_snapshot.get("last_health_ts") or "") or None,
                "age_seconds": _age_seconds(operations_snapshot.get("last_health_ts")),
                "caveat": None if operations_snapshot.get("last_health_ts") else "No health timestamp recorded yet.",
            },
        ]
    )
    return FreshnessPanelData(
        **_base_section(
            as_of=as_of,
            caveat="Freshness rows surface missing timestamps explicitly instead of assuming healthy data.",
            source_name=DIGEST_SOURCE_MAP["freshness_panel"],
            source_age_seconds=0,
        ),
        rows=rows,
    )


def build_mode_truth_digest(
    *,
    as_of: str,
    runtime_context: dict[str, Any],
    promotion_readiness: dict[str, Any],
    strategy_context: dict[str, Any],
) -> ModeTruthData:
    mode_value = str(runtime_context.get("mode_value") or "unknown")
    mode_label = str(runtime_context.get("mode_label") or "Unknown")
    start_decision = runtime_context.get("start_decision")
    reasons = [str(item) for item in list(getattr(start_decision, "reasons", []) or [])]
    allowed = ["read-only collectors", "research analytics", "synthetic strategy evaluation"]
    blocked: list[str] = []
    if mode_value == "paper":
        allowed.insert(0, "paper execution")
        blocked.extend(["sandbox live submission", "real live submission"])
    elif mode_value == "sandbox_live":
        if bool(getattr(start_decision, "ok", False)):
            allowed.insert(0, "exchange sandbox operations")
        else:
            blocked.append("sandbox order submission until gates clear")
        blocked.append("real live submission")
    elif mode_value == "real_live":
        if bool(getattr(start_decision, "ok", False)) and bool(runtime_context.get("guard_allowed")) and bool(runtime_context.get("armed")):
            allowed.insert(0, "guarded real live submission")
        else:
            blocked.append("real live submission until confirmations and gates clear")
        blocked.append("unguarded live promotion")
    else:
        blocked.append("Mode truth unavailable")
    if not bool(runtime_context.get("normalized_live_enabled")):
        reasons.append("normalized live enablement remains false")
    if mode_value != "paper" and not bool(runtime_context.get("armed")):
        reasons.append(str(runtime_context.get("arming_reason") or "live_not_armed"))
    reasons.extend(str(item) for item in list(promotion_readiness.get("blockers") or []) if str(item or "").strip())
    promotion_status = _normalize_health_state(promotion_readiness.get("status"))
    strategy_rows = [dict(row) for row in list(strategy_context.get("raw_rows") or []) if isinstance(row, dict)]
    if strategy_rows:
        top_row = strategy_rows[0]
        research_acceptance = dict(top_row.get("research_acceptance") or {})
        research_summary = str(research_acceptance.get("summary") or "").strip()
        research_blockers = [
            str(item).strip()
            for item in list(research_acceptance.get("blockers") or _top_row_research_acceptance_blockers(top_row))
            if str(item).strip()
        ]
        if research_blockers:
            reasons.append(
                research_summary
                or "Top strategy is not research-accepted yet; promotion readiness does not make the current edge claim credible."
            )
            if promotion_status == "ok":
                promotion_status = "warn"
    return ModeTruthData(
        **_base_section(
            as_of=as_of,
            caveat=str(getattr(start_decision, "note", "") or runtime_context.get("mode_note") or None),
            source_name=DIGEST_SOURCE_MAP["mode_truth"],
            source_age_seconds=0,
        ),
        current_mode=mode_value,  # type: ignore[arg-type]
        label=mode_label,
        allowed=allowed,
        blocked=blocked,
        promotion_stage=str(promotion_readiness.get("current_stage_label") or "Paper"),
        promotion_target=str(promotion_readiness.get("target_stage_label") or "") or None,
        promotion_status=promotion_status,
        promotion_summary=str(promotion_readiness.get("summary") or "Promotion readiness is unavailable."),
        promotion_pass_criteria=[str(item) for item in list(promotion_readiness.get("pass_criteria") or []) if str(item or "").strip()],
        promotion_rollback_criteria=[str(item) for item in list(promotion_readiness.get("rollback_criteria") or []) if str(item or "").strip()],
        promotion_blockers=list(dict.fromkeys(reason for reason in reasons if reason)),
    )


def build_recent_incidents_digest(
    *,
    as_of: str,
    overview_summary: dict[str, Any],
    collector_runtime: dict[str, Any],
    operations_snapshot: dict[str, Any],
    attention_now: AttentionNowData,
) -> RecentIncidentsData:
    items: list[IncidentItem] = []
    for idx, warning in enumerate(list(overview_summary.get("active_warnings") or [])[:3]):
        text = str(warning or "").strip()
        if text:
            items.append(
                {
                    "id": f"incident-warning-{idx}",
                    "ts": as_of,
                    "severity": "watch",
                    "title": text[:96],
                    "summary": text,
                    "source": "risk",
                }
            )
    if int(collector_runtime.get("errors") or 0) > 0:
        items.append(
            {
                "id": "incident-collector-errors",
                "ts": str(collector_runtime.get("ts") or as_of),
                "severity": "important",
                "title": "Collector loop reported errors",
                "summary": str(collector_runtime.get("summary_text") or "Collector runtime is degraded."),
                "source": "collector",
            }
        )
    if int(operations_snapshot.get("attention_services") or 0) > 0:
        items.append(
            {
                "id": "incident-ops-attention",
                "ts": str(operations_snapshot.get("last_health_ts") or as_of),
                "severity": "important",
                "title": "Operator services need attention",
                "summary": f"{int(operations_snapshot.get('attention_services') or 0)} tracked service(s) are degraded or failed.",
                "source": "operations",
            }
        )
    if not items:
        items.append(
            {
                "id": "incident-none",
                "ts": as_of,
                "severity": "info",
                "title": "No recent incidents",
                "summary": "No recent collector, mode, or warning incident was promoted into the digest.",
                "source": "digest",
            }
        )
    return RecentIncidentsData(
        **_base_section(
            as_of=as_of,
            caveat="Recent incidents are synthesized from current warning and runtime summaries until a dedicated incident stream exists.",
            source_name=DIGEST_SOURCE_MAP["recent_incidents"],
            source_age_seconds=0,
        ),
        items=items[:6],
    )


def build_next_best_action_digest(
    *,
    as_of: str,
    attention_now: AttentionNowData,
    leaderboard_summary: LeaderboardSummaryData,
    mode_truth: ModeTruthData,
) -> NextBestActionData:
    items = list(attention_now.get("items") or [])
    primary = next((item for item in items if str(item.get("severity") or "") != "info"), None)
    if primary:
        return NextBestActionData(
            **_base_section(
                as_of=as_of,
                caveat="Next action is derived from the highest-severity current digest item.",
                source_name=DIGEST_SOURCE_MAP["next_best_action_attention"],
                source_age_seconds=0,
            ),
            title=str(primary.get("title") or "Review current blockers"),
            why=str(primary.get("why_it_matters") or "Current digest requires operator review."),
            recommended_action=str(primary.get("next_action") or "Review the highlighted issue."),
            secondary_actions=[str(item.get("next_action") or "") for item in items[1:3] if str(item.get("next_action") or "").strip()],
            source=str(primary.get("source") or "digest"),
        )

    top_row = next(iter(list(leaderboard_summary.get("rows") or [])), None)
    if top_row:
        top_row_caveat = str(top_row.get("caveat") or "").strip()
        return NextBestActionData(
            **_base_section(
                as_of=as_of,
                caveat="Action is derived from the top leaderboard row when no higher-severity attention item is active.",
                source_name=DIGEST_SOURCE_MAP["next_best_action_leaderboard"],
                source_age_seconds=0,
            ),
            title=f"Review {_candidate_title(top_row.get('name') or top_row.get('strategy_id') or 'top strategy')}",
            why=top_row_caveat or "It currently leads the synthetic benchmark and is the best available candidate for deeper review.",
            recommended_action=(
                "Review the top strategy hypothesis, persisted feedback weighting, and regime weaknesses before considering sandbox promotion."
                if top_row_caveat
                else "Review the top strategy hypothesis and regime weaknesses before considering sandbox promotion."
            ),
            secondary_actions=[
                "Check structural-edge freshness before trusting the digest.",
                "Keep current execution posture conservative until blockers are clear.",
            ],
            source="strategy_leaderboard",
        )

    return NextBestActionData(
        **_base_section(
            as_of=as_of,
            caveat="Insufficient current summaries are available for a stronger recommendation.",
            source_name=DIGEST_SOURCE_MAP["next_best_action_default"],
            source_age_seconds=0,
        ),
        title="No single next action available",
        why="The current digest does not have enough populated summaries for a stronger recommendation.",
        recommended_action="Refresh the current summaries and verify collector/runtime freshness.",
        secondary_actions=[],
        source="digest",
    )


def _page_status(
    *,
    attention_now: AttentionNowData,
    safety_warnings: SafetyWarningsData,
    freshness_panel: FreshnessPanelData,
) -> PageStatusData:
    attention_items = list(attention_now.get("items") or [])
    warning_items = list(safety_warnings.get("items") or [])
    freshness_rows = list(freshness_panel.get("rows") or [])
    if any(str(item.get("severity") or "") == "critical" for item in attention_items + warning_items):
        return {"state": "critical", "caveat": "One or more digest sections require immediate operator attention."}
    if any(str(row.get("status") or "") == "stale" for row in freshness_rows):
        return {"state": "warn", "caveat": "One or more digest sources are stale."}
    if any(str(item.get("severity") or "") in {"important", "watch"} for item in attention_items + warning_items):
        return {"state": "warn", "caveat": "Digest is usable, but some sections need operator review."}
    return {"state": "ok", "caveat": "Digest inputs are present and no major warning is active."}


def build_home_digest(overview_summary: dict[str, Any] | None = None) -> HomeDigestData:
    summary = overview_summary if isinstance(overview_summary, dict) else {}
    if not summary:
        try:
            from dashboard.services.view_data import get_overview_view

            overview_view = get_overview_view()
            summary = overview_view.get("summary") if isinstance(overview_view.get("summary"), dict) else {}
        except Exception:
            summary = {}
    as_of = _utc_iso()
    user_cfg = load_user_yaml()
    trading_cfg = _load_trading_cfg()
    runtime_context = _runtime_context(trading_cfg=trading_cfg, user_cfg=user_cfg)
    strategy_context = _strategy_context(user_cfg=user_cfg, trading_cfg=trading_cfg)
    live_snapshot = load_latest_live_crypto_edge_snapshot()
    structural_health = load_crypto_edge_staleness_summary()
    structural_digest = load_crypto_edge_staleness_digest()
    collector_runtime = load_crypto_edge_collector_runtime()
    try:
        operations_snapshot = get_operations_snapshot()
    except PermissionError:
        operations_snapshot = {}
    except Exception:
        operations_snapshot = {}
    leaderboard_summary = build_leaderboard_summary_digest(as_of=as_of, strategy_context=strategy_context)
    runtime_truth = build_runtime_truth_digest(
        as_of=as_of,
        runtime_context=runtime_context,
        structural_health=structural_health,
        collector_runtime=collector_runtime,
        strategy_context=strategy_context,
    )
    promotion_readiness = build_promotion_readiness(
        as_of=as_of,
        runtime_context=runtime_context,
        leaderboard_summary=leaderboard_summary,
        structural_health=structural_health,
        collector_runtime=collector_runtime,
        strategy_truth=strategy_context,
    )
    attention_now = build_attention_now_digest(
        as_of=as_of,
        overview_summary=summary,
        runtime_context=runtime_context,
        strategy_context=strategy_context,
        structural_health=structural_health,
        structural_digest=structural_digest,
        collector_runtime=collector_runtime,
        operations_snapshot=operations_snapshot,
    )
    scorecard_snapshot = build_scorecard_snapshot_digest(as_of=as_of, strategy_context=strategy_context)
    crypto_edge_summary = build_crypto_edge_summary_digest(as_of=as_of, live_snapshot=live_snapshot)
    safety_warnings = build_safety_warnings_digest(
        as_of=as_of,
        overview_summary=summary,
        runtime_context=runtime_context,
        strategy_context=strategy_context,
        structural_health=structural_health,
        collector_runtime=collector_runtime,
        operations_snapshot=operations_snapshot,
    )
    freshness_panel = build_freshness_panel_digest(
        as_of=as_of,
        summary=summary,
        collector_runtime=collector_runtime,
        live_snapshot=live_snapshot,
        operations_snapshot=operations_snapshot,
        strategy_context=strategy_context,
        leaderboard_summary=leaderboard_summary,
        scorecard_snapshot=scorecard_snapshot,
    )
    mode_truth = build_mode_truth_digest(
        as_of=as_of,
        runtime_context=runtime_context,
        promotion_readiness=promotion_readiness,
        strategy_context=strategy_context,
    )
    recent_incidents = build_recent_incidents_digest(
        as_of=as_of,
        overview_summary=summary,
        collector_runtime=collector_runtime,
        operations_snapshot=operations_snapshot,
        attention_now=attention_now,
    )
    next_best_action = build_next_best_action_digest(
        as_of=as_of,
        attention_now=attention_now,
        leaderboard_summary=leaderboard_summary,
        mode_truth=mode_truth,
    )
    page_status = _page_status(
        attention_now=attention_now,
        safety_warnings=safety_warnings,
        freshness_panel=freshness_panel,
    )

    return HomeDigestData(
        as_of=as_of,
        page_status=page_status,
        claim_boundaries=list(CLAIM_BOUNDARIES),
        runtime_truth=runtime_truth,
        attention_now=attention_now,
        leaderboard_summary=leaderboard_summary,
        scorecard_snapshot=scorecard_snapshot,
        crypto_edge_summary=crypto_edge_summary,
        safety_warnings=safety_warnings,
        freshness_panel=freshness_panel,
        mode_truth=mode_truth,
        recent_incidents=recent_incidents,
        next_best_action=next_best_action,
    )


load_home_digest = build_home_digest
