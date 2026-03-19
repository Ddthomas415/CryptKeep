from __future__ import annotations

DIGEST_SOURCE_MAP = {
    "runtime_truth": "config/trading.yaml + live_guard + collector_runtime",
    "attention_now": "overview summary + operations snapshot + structural freshness",
    "leaderboard_summary_artifact": "dashboard.services.digest.strategy_evidence.load_latest_strategy_evidence",
    "leaderboard_summary_fallback": "dashboard.services.strategy_evaluation.build_strategy_workbench synthetic fallback",
    "scorecard_snapshot_artifact": "dashboard.services.digest.strategy_evidence.load_latest_strategy_evidence aggregate leaderboard",
    "scorecard_snapshot_fallback": "dashboard.services.strategy_evaluation.build_strategy_workbench synthetic fallback",
    "crypto_edge_summary": "dashboard.services.crypto_edge_research.load_latest_live_crypto_edge_snapshot",
    "safety_warnings": "live_guard + start_manager + collector_runtime",
    "freshness_panel": "collector runtime + latest live snapshot + strategy evidence artifact or labeled synthetic fallback",
    "mode_truth": "config/trading.yaml + services.bot.start_manager.decide_start + dashboard.services.promotion_ladder.build_promotion_readiness",
    "recent_incidents": "overview warnings + collector runtime + operations snapshot",
    "next_best_action_attention": "attention_now",
    "next_best_action_leaderboard": "strategy_leaderboard",
    "next_best_action_default": "digest",
}
