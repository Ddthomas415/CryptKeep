from __future__ import annotations

MAX_CONTEXT_CHARS = 12_000
COPILOT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024

PROHIBITED_ACTIONS = [
    "arm_live_trading",
    "disarm_kill_switch",
    "submit_order",
    "cancel_order",
    "write_config",
    "merge_code",
    "modify_database",
]
