from __future__ import annotations

# CBP_AI_COPILOT_POLICY
# Documents copilot permissions and boundaries.
# The current implementation is read-only by architecture:
# it only collects context and returns text analysis.

READABLE_PATHS = [
    "config/trading.yaml",
    "runtime/flags/",
    "runtime/pids/",
    "data/lifecycle_events.sqlite",
    "data/execution.sqlite",
    "logs/",
    "docs/",
    "services/admin/system_guard.py",
    "services/admin/live_guard.py",
    "services/execution/live_executor.py",
    "services/execution/place_order.py",
    "services/risk/",
    "storage/execution_store_sqlite.py",
]

PROHIBITED_ACTIONS = [
    "arm_live_trading",
    "disarm_kill_switch",
    "submit_order",
    "cancel_order",
    "write_config",
    "merge_code",
    "modify_database",
    "execute_script",
]

MAX_CONTEXT_CHARS = 12_000
COPILOT_MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 1024
