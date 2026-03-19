from __future__ import annotations

DIGEST_SOURCE_MAP = {
    "runtime_truth": "config/trading.yaml + live_guard + collector_runtime",
    "attention_now": "overview summary + operations snapshot + structural freshness",
    "leaderboard_summary": "services.backtest.leaderboard.run_strategy_leaderboard",
    "scorecard_snapshot": "services.backtest.scorecard via run_strategy_leaderboard",
    "crypto_edge_summary": "dashboard.services.crypto_edge_research.load_latest_live_crypto_edge_snapshot",
    "safety_warnings": "live_guard + start_manager + collector_runtime",
    "freshness_panel": "collector runtime + latest live snapshot + synthetic evaluation",
    "mode_truth": "config/trading.yaml + services.bot.start_manager.decide_start + dashboard.services.promotion_ladder.build_promotion_readiness",
    "recent_incidents": "overview warnings + collector runtime + operations snapshot",
    "next_best_action_attention": "attention_now",
    "next_best_action_leaderboard": "strategy_leaderboard",
    "next_best_action_default": "digest",
}
