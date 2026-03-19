from __future__ import annotations

from typing import Any, Literal, TypedDict


HealthState = Literal["ok", "warn", "critical", "unknown"]


class PromotionReadiness(TypedDict):
    as_of: str
    current_stage: str
    current_stage_label: str
    target_stage: str | None
    target_stage_label: str | None
    status: HealthState
    summary: str
    blockers: list[str]
    pass_criteria: list[str]
    rollback_criteria: list[str]


def _fnum(value: Any, default: float = 0.0) -> float:
    try:
        out = float(value)
    except Exception:
        return float(default)
    return out


def _mode_to_stage(mode_value: Any) -> tuple[str, str, str | None, str | None]:
    mode = str(mode_value or "unknown").strip().lower()
    if mode == "paper":
        return "paper", "Paper", "sandbox_live", "Sandbox Live"
    if mode == "sandbox_live":
        return "sandbox_live", "Sandbox Live", "tiny_live", "Tiny Live"
    if mode == "real_live":
        return "tiny_live", "Tiny Live", None, None
    return "paper", "Paper", "sandbox_live", "Sandbox Live"


def _top_row(leaderboard_summary: dict[str, Any]) -> dict[str, Any] | None:
    rows = list((leaderboard_summary or {}).get("rows") or [])
    return dict(rows[0]) if rows else None


def _sandbox_pass_criteria() -> list[str]:
    return [
        "Top strategy remains Keep, not Improve/Freeze/Retire.",
        "Top strategy shows at least 3 closed trades in the current evaluation cycle.",
        "Top strategy stays positive after fees and slippage.",
        "Collector/runtime freshness is not stale or missing.",
        "Kill switch is disarmed before enabling sandbox execution.",
        "execution.live_enabled and sandbox mode are reviewed explicitly, not implied.",
    ]


def _sandbox_rollback_criteria() -> list[str]:
    return [
        "Return immediately to Paper if the kill switch arms or the live boundary blocks.",
        "Return immediately to Paper if collector/runtime freshness degrades to Stale or Missing.",
        "Return immediately to Paper if the promoted strategy flips away from Keep or loses post-cost performance.",
        "Return immediately to Paper if operator telemetry becomes degraded or unknown.",
    ]


def _tiny_live_pass_criteria() -> list[str]:
    return [
        "Sandbox stage has already run cleanly with no active safety blockers.",
        "Top strategy remains Keep with at least 5 closed trades across current evidence.",
        "Top strategy max drawdown stays at or below 8.0%.",
        "Paper/live drift is measured and not high before any tiny-live trial.",
        "ENABLE_LIVE_TRADING=YES and CONFIRM_LIVE=YES are set deliberately.",
        "CBP_EXECUTION_ARMED is set only for the reviewed tiny-live window.",
    ]


def _tiny_live_rollback_criteria() -> list[str]:
    return [
        "Return immediately to Sandbox or Paper if the kill switch arms or the boundary blocks.",
        "Return immediately to Sandbox or Paper if post-cost performance turns negative.",
        "Return immediately to Sandbox or Paper if drawdown breaches the reviewed trial limit.",
        "Return immediately to Sandbox or Paper if collector/runtime freshness degrades or telemetry goes unknown.",
    ]


def build_promotion_readiness(
    *,
    as_of: str,
    runtime_context: dict[str, Any],
    leaderboard_summary: dict[str, Any],
    structural_health: dict[str, Any],
    collector_runtime: dict[str, Any],
) -> PromotionReadiness:
    current_stage, current_stage_label, target_stage, target_stage_label = _mode_to_stage(runtime_context.get("mode_value"))
    top = _top_row(leaderboard_summary)
    blockers: list[str] = []

    kill_armed = bool(runtime_context.get("kill_armed"))
    collector_freshness = str(collector_runtime.get("freshness") or "").strip().lower()
    collector_errors = int(_fnum(collector_runtime.get("errors"), 0.0))
    live_enabled = bool(runtime_context.get("normalized_live_enabled"))

    if target_stage == "sandbox_live":
        pass_criteria = _sandbox_pass_criteria()
        rollback_criteria = _sandbox_rollback_criteria()
        if not live_enabled:
            blockers.append("execution.live_enabled remains false for any sandbox promotion.")
        if kill_armed:
            blockers.append("Kill switch is armed.")
        if bool(structural_health.get("needs_attention")):
            blockers.append(str(structural_health.get("summary_text") or "Structural-edge freshness is degraded."))
        if collector_freshness in {"stale", "missing"}:
            blockers.append(f"Collector freshness is {collector_freshness.title()}.")
        if collector_errors > 0:
            blockers.append(f"Collector runtime reported {collector_errors} error(s).")
        if not top:
            blockers.append("No leaderboard summary is available yet.")
        else:
            recommendation = str(top.get("recommendation") or "unknown").strip().lower()
            closed_trades = int(_fnum(top.get("closed_trades"), 0.0))
            post_cost_return = _fnum(top.get("post_cost_return_pct"), 0.0)
            if recommendation != "keep":
                blockers.append(f"Top strategy recommendation is {recommendation or 'unknown'}; require keep.")
            if closed_trades < 3:
                blockers.append(f"Top strategy only has {closed_trades} closed trade(s); require at least 3.")
            if post_cost_return <= 0.0:
                blockers.append("Top strategy is not positive after fees and slippage.")

        if blockers:
            return {
                "as_of": as_of,
                "current_stage": current_stage,
                "current_stage_label": current_stage_label,
                "target_stage": target_stage,
                "target_stage_label": target_stage_label,
                "status": "critical" if kill_armed else "warn",
                "summary": f"Promotion from {current_stage_label} to {target_stage_label} is not ready yet.",
                "blockers": blockers,
                "pass_criteria": pass_criteria,
                "rollback_criteria": rollback_criteria,
            }
        return {
            "as_of": as_of,
            "current_stage": current_stage,
            "current_stage_label": current_stage_label,
            "target_stage": target_stage,
            "target_stage_label": target_stage_label,
            "status": "ok",
            "summary": f"Current evidence is strong enough to review promotion from {current_stage_label} to {target_stage_label}.",
            "blockers": [],
            "pass_criteria": pass_criteria,
            "rollback_criteria": rollback_criteria,
        }

    if target_stage == "tiny_live":
        pass_criteria = _tiny_live_pass_criteria()
        rollback_criteria = _tiny_live_rollback_criteria()
        if current_stage != "sandbox_live":
            blockers.append("Sandbox live has not been exercised as the current operating stage.")
        if not bool(getattr(runtime_context.get("start_decision"), "ok", False)):
            blockers.append("Sandbox/runtime start gate is not clear.")
        if not bool(runtime_context.get("guard_allowed")):
            blockers.append("Outer live gate is not currently clear.")
        if not bool(runtime_context.get("armed")):
            blockers.append("Live path is not armed for any tiny-live trial.")
        if kill_armed:
            blockers.append("Kill switch is armed.")
        if bool(structural_health.get("needs_attention")):
            blockers.append(str(structural_health.get("summary_text") or "Structural-edge freshness is degraded."))
        if collector_freshness in {"stale", "missing"}:
            blockers.append(f"Collector freshness is {collector_freshness.title()}.")
        if collector_errors > 0:
            blockers.append(f"Collector runtime reported {collector_errors} error(s).")
        if not top:
            blockers.append("No leaderboard summary is available yet.")
        else:
            recommendation = str(top.get("recommendation") or "unknown").strip().lower()
            closed_trades = int(_fnum(top.get("closed_trades"), 0.0))
            drawdown = _fnum(top.get("max_drawdown_pct"), 0.0)
            paper_live_drift = str(top.get("paper_live_drift") or "unknown").strip().lower()
            if recommendation != "keep":
                blockers.append(f"Top strategy recommendation is {recommendation or 'unknown'}; require keep.")
            if closed_trades < 5:
                blockers.append(f"Top strategy only has {closed_trades} closed trade(s); require at least 5.")
            if drawdown > 8.0:
                blockers.append(f"Top strategy drawdown is {drawdown:.2f}%; require 8.00% or less.")
            if paper_live_drift in {"unknown", "high"}:
                blockers.append("Paper/live drift is not yet measured tightly enough for tiny live.")

        if blockers:
            return {
                "as_of": as_of,
                "current_stage": current_stage,
                "current_stage_label": current_stage_label,
                "target_stage": target_stage,
                "target_stage_label": target_stage_label,
                "status": "critical" if kill_armed else "warn",
                "summary": f"Promotion from {current_stage_label} to {target_stage_label} is not ready yet.",
                "blockers": blockers,
                "pass_criteria": pass_criteria,
                "rollback_criteria": rollback_criteria,
            }
        return {
            "as_of": as_of,
            "current_stage": current_stage,
            "current_stage_label": current_stage_label,
            "target_stage": target_stage,
            "target_stage_label": target_stage_label,
            "status": "ok",
            "summary": f"Current evidence is strong enough to review promotion from {current_stage_label} to {target_stage_label}.",
            "blockers": [],
            "pass_criteria": pass_criteria,
            "rollback_criteria": rollback_criteria,
        }

    return {
        "as_of": as_of,
        "current_stage": current_stage,
        "current_stage_label": current_stage_label,
        "target_stage": None,
        "target_stage_label": None,
        "status": "critical" if kill_armed else "ok",
        "summary": "Runtime already requests the final reviewed stage. Keep the posture conservative and treat rollback criteria as active.",
        "blockers": ["Kill switch is armed."] if kill_armed else [],
        "pass_criteria": [],
        "rollback_criteria": _tiny_live_rollback_criteria(),
    }
