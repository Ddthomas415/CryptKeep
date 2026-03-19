from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from dashboard.services.crypto_edge_research import (
    load_crypto_edge_collector_runtime,
    load_crypto_edge_staleness_digest,
    load_crypto_edge_staleness_summary,
)
from dashboard.services.operator import get_operations_snapshot
from dashboard.services.operator_tools import synthetic_ohlcv
from dashboard.services.strategy_evaluation import build_leaderboard_table_rows, build_strategy_workbench
from services.admin.config_editor import load_user_yaml
from services.admin.live_guard import live_allowed
from services.bot.start_manager import decide_start
from services.execution.live_arming import is_live_enabled, live_enabled_and_armed


REPO_ROOT = Path(__file__).resolve().parents[2]
TRADING_CFG_PATH = REPO_ROOT / "config" / "trading.yaml"


def _load_trading_cfg() -> dict[str, Any]:
    try:
        payload = yaml.safe_load(TRADING_CFG_PATH.read_text(encoding="utf-8")) or {}
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _runtime_mode_payload(trading_cfg: dict[str, Any]) -> tuple[str, str]:
    mode = str(trading_cfg.get("mode") or "paper").strip().lower()
    live_cfg = trading_cfg.get("live") if isinstance(trading_cfg.get("live"), dict) else {}
    sandbox = bool(live_cfg.get("sandbox", True))

    if mode != "live":
        return "Paper", "config/trading.yaml keeps runtime in paper mode."
    if sandbox:
        return "Sandbox Live", "config/trading.yaml requests live mode with sandbox enabled."
    return "Real Live", "config/trading.yaml requests real live mode and needs explicit confirmations."


def _execution_truth_payload(
    *,
    trading_cfg: dict[str, Any],
    user_cfg: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    mode = str(trading_cfg.get("mode") or "paper").strip().lower()
    live_cfg = trading_cfg.get("live") if isinstance(trading_cfg.get("live"), dict) else {}
    sandbox = bool(live_cfg.get("sandbox", True))
    normalized_live_enabled = bool(is_live_enabled(user_cfg))
    start_decision = decide_start("live", trading_cfg) if mode == "live" else decide_start("paper", trading_cfg)

    if mode != "live":
        return (
            "Paper Only",
            "Trading runner and router defaults remain paper-first; live execution is not active.",
            {
                "start_decision": start_decision,
                "normalized_live_enabled": normalized_live_enabled,
                "sandbox": sandbox,
            },
        )

    if sandbox:
        label = "Sandbox Live Guarded" if bool(start_decision.ok) else "Sandbox Live Blocked"
    else:
        label = "Real Live Guarded" if bool(start_decision.ok) else "Real Live Blocked"

    detail = str(start_decision.note or "").strip()
    reasons = ", ".join(str(item) for item in list(start_decision.reasons or [])[:2])
    if reasons:
        detail = f"{detail} Reasons: {reasons}" if detail else reasons
    if not normalized_live_enabled:
        detail = f"{detail} Normalized live enablement is still false.".strip()

    return (
        label,
        detail or "Live-mode truth could not be summarized.",
        {
            "start_decision": start_decision,
            "normalized_live_enabled": normalized_live_enabled,
            "sandbox": sandbox,
        },
    )


def _live_safety_payload(*, mode_label: str) -> tuple[str, str, dict[str, Any]]:
    allowed, guard_reason, guard_details = live_allowed()
    armed, arming_reason = live_enabled_and_armed()

    if mode_label == "Paper":
        return (
            "Inactive",
            "Paper mode is active; live submission gates remain idle until mode changes.",
            {
                "allowed": allowed,
                "guard_reason": guard_reason,
                "guard_details": guard_details,
                "armed": armed,
                "arming_reason": arming_reason,
            },
        )

    if allowed and armed:
        label = "Armed"
    elif allowed:
        label = "Not Armed"
    else:
        label = "Blocked"

    return (
        label,
        f"Guard {guard_reason}; arming {arming_reason}.",
        {
            "allowed": allowed,
            "guard_reason": guard_reason,
            "guard_details": guard_details,
            "armed": armed,
            "arming_reason": arming_reason,
        },
    )


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


def _strategy_snapshot_payload(
    *,
    user_cfg: dict[str, Any],
    trading_cfg: dict[str, Any],
) -> tuple[str, str, dict[str, Any]]:
    configured_strategy = _configured_strategy_name(user_cfg, trading_cfg)
    symbol_rows = list(trading_cfg.get("symbols") or [])
    symbol = str(symbol_rows[0] or "BTC/USD") if symbol_rows else "BTC/USD"
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
    leaderboard_rows = build_leaderboard_table_rows(dict(workbench.get("leaderboard") or {}))
    top_row = dict(leaderboard_rows[0] or {}) if leaderboard_rows else {}

    if top_row:
        label = str(top_row.get("candidate") or top_row.get("strategy") or "No benchmark").replace("_", " ").title()
        detail = (
            f"Synthetic benchmark leader for {symbol}: "
            f"{float(top_row.get('return_pct') or 0.0):.2f}% after costs, "
            f"{float(top_row.get('max_drawdown_pct') or 0.0):.2f}% max drawdown."
        )
    else:
        label = configured_strategy.replace("_", " ").title()
        detail = f"Synthetic benchmark only. No leaderboard candidate row was available for {symbol}."

    return label, detail, {"workbench": workbench, "leaderboard_rows": leaderboard_rows, "symbol": symbol}


def _attention_items(
    *,
    overview_summary: dict[str, Any],
    mode_label: str,
    execution_truth_label: str,
    execution_truth_note: str,
    live_safety_label: str,
    live_safety_note: str,
    structural_health: dict[str, Any],
    structural_digest: dict[str, Any],
    collector_runtime: dict[str, Any],
    operations_snapshot: dict[str, Any],
) -> list[str]:
    items: list[str] = []

    if mode_label == "Paper":
        items.append("Runtime remains paper-first. Use paper or sandbox evidence before considering guarded live mode.")
    elif "Blocked" in execution_truth_label:
        items.append(f"Live start is blocked. {execution_truth_note}")

    if live_safety_label in {"Blocked", "Not Armed"} and mode_label != "Paper":
        items.append(f"Live safety is {live_safety_label.lower()}. {live_safety_note}")

    for warning in list(overview_summary.get("active_warnings") or []):
        text = str(warning or "").strip()
        if text:
            items.append(text)

    blocked_trades = int(overview_summary.get("blocked_trades_count") or 0)
    if blocked_trades > 0:
        items.append(f"{blocked_trades} trade(s) are currently blocked by the active risk policy.")

    if bool(structural_health.get("needs_attention")):
        text = str(structural_health.get("summary_text") or "").strip()
        if text:
            items.append(text)

    if bool(structural_digest.get("needs_attention")):
        text = str(structural_digest.get("action_text") or "").strip()
        if text:
            items.append(text)

    attention_services = int(operations_snapshot.get("attention_services") or 0)
    if attention_services > 0:
        items.append(f"{attention_services} tracked service(s) need operator attention.")

    unknown_services = int(operations_snapshot.get("unknown_services") or 0)
    if unknown_services > 0:
        items.append(f"{unknown_services} tracked service(s) have no current health state.")

    collector_errors = int(collector_runtime.get("errors") or 0)
    if collector_errors > 0:
        items.append(f"Collector loop reported {collector_errors} error(s).")

    seen: set[str] = set()
    deduped: list[str] = []
    for item in items:
        key = item.strip()
        if key and key not in seen:
            seen.add(key)
            deduped.append(key)
    return deduped or ["No immediate operator attention items were detected."]


def load_home_digest(overview_summary: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = overview_summary if isinstance(overview_summary, dict) else {}
    user_cfg = load_user_yaml()
    trading_cfg = _load_trading_cfg()
    mode_label, mode_note = _runtime_mode_payload(trading_cfg)
    execution_truth_label, execution_truth_note, execution_meta = _execution_truth_payload(
        trading_cfg=trading_cfg,
        user_cfg=user_cfg,
    )
    live_safety_label, live_safety_note, live_safety_meta = _live_safety_payload(mode_label=mode_label)
    strategy_label, strategy_note, strategy_meta = _strategy_snapshot_payload(
        user_cfg=user_cfg,
        trading_cfg=trading_cfg,
    )
    structural_health = load_crypto_edge_staleness_summary()
    structural_digest = load_crypto_edge_staleness_digest()
    collector_runtime = load_crypto_edge_collector_runtime()
    operations_snapshot = get_operations_snapshot()
    attention_items = _attention_items(
        overview_summary=summary,
        mode_label=mode_label,
        execution_truth_label=execution_truth_label,
        execution_truth_note=execution_truth_note,
        live_safety_label=live_safety_label,
        live_safety_note=live_safety_note,
        structural_health=structural_health,
        structural_digest=structural_digest,
        collector_runtime=collector_runtime,
        operations_snapshot=operations_snapshot,
    )

    return {
        "ok": True,
        "runtime_mode_label": mode_label,
        "runtime_mode_note": mode_note,
        "execution_truth_label": execution_truth_label,
        "execution_truth_note": execution_truth_note,
        "live_safety_label": live_safety_label,
        "live_safety_note": live_safety_note,
        "strategy_label": strategy_label,
        "strategy_note": strategy_note,
        "structural_freshness_label": str(structural_health.get("live_snapshot_freshness") or "Unknown"),
        "structural_freshness_note": str(
            structural_digest.get("headline") or structural_digest.get("while_away_summary") or "Unknown"
        ),
        "collector_status_label": str(collector_runtime.get("status") or "not_started").replace("_", " ").title(),
        "collector_status_note": str(collector_runtime.get("freshness") or "Unknown"),
        "attention_items": attention_items,
        "claim_boundaries": [
            "Crypto-first platform.",
            "Paper-heavy defaults remain active.",
            "Live trading stays guarded and fail-closed.",
            "Stock support is not proven.",
            "Home strategy summary is a synthetic benchmark, not live performance proof.",
        ],
        "top_action": str(
            structural_health.get("action_text")
            or structural_digest.get("action_text")
            or "Review the top opportunity and structural freshness before changing execution posture."
        ),
        "operations_snapshot": operations_snapshot,
        "structural_health": structural_health,
        "structural_digest": structural_digest,
        "collector_runtime": collector_runtime,
        "strategy_snapshot": strategy_meta,
        "execution_truth": execution_meta,
        "live_safety": live_safety_meta,
    }
