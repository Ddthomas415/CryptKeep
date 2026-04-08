from __future__ import annotations

from pathlib import Path

from services.os.app_paths import config_dir, runtime_dir

MAX_CONTEXT_CHARS = 12_000
DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
COPILOT_MODEL = DEFAULT_MODEL
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

PROTECTED_PATH_PREFIXES = (
    "services/execution/",
    "services/risk/",
    "services/admin/",
    "services/security/",
    "dashboard/auth_gate.py",
    "scripts/",
    "config/",
)

APPROVAL_REQUIRED_PATH_PREFIXES = PROTECTED_PATH_PREFIXES

READ_ONLY_CONTEXT_PATHS = (
    "docs/",
    "tests/",
    "dashboard/",
    "services/",
    ".cbp_state/runtime/",
    ".cbp_state/data/",
)

REPORT_DIRNAME = "ai_reports"
CONFIG_FILENAME = "ai_copilot.yaml"


def _normalize_repo_path(path: str) -> str:
    return str(path or "").replace("\\", "/").lstrip("./")


def is_protected_path(path: str) -> bool:
    return _normalize_repo_path(path).startswith(PROTECTED_PATH_PREFIXES)


def requires_human_approval(path: str) -> bool:
    return _normalize_repo_path(path).startswith(APPROVAL_REQUIRED_PATH_PREFIXES)


def report_root() -> Path:
    root = runtime_dir() / REPORT_DIRNAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def config_path() -> Path:
    root = config_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root / CONFIG_FILENAME
