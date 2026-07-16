from __future__ import annotations

from pathlib import Path

from services.os.app_paths import config_dir, runtime_dir

MAX_CONTEXT_CHARS = 12_000
DEFAULT_PROVIDER = "anthropic"
DEFAULT_MODEL = "claude-sonnet-4-20250514"
COPILOT_MODEL = DEFAULT_MODEL
MAX_TOKENS = 1024
EXTERNAL_PROVIDER_ALLOWLIST_ENV = "CBP_COPILOT_ALLOWED_PROVIDERS"
SUPPORTED_EXTERNAL_PROVIDERS = ("anthropic", "openai", "google")

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


def _normalize_provider_name(provider: str) -> str:
    return str(provider or "").strip().lower()


def parse_external_provider_allowlist(raw: str | None) -> dict:
    """Resolve the operator-declared external-provider allow-list.

    Missing/blank preserves the existing supported-provider set. A configured
    list must contain only known provider names; garbage blocks provider calls
    instead of silently widening external disclosure.
    """
    if raw is None or str(raw).strip() == "":
        return {
            "ok": True,
            "providers": list(SUPPORTED_EXTERNAL_PROVIDERS),
            "source": "default_supported",
        }

    parts = [_normalize_provider_name(part) for part in str(raw).split(",")]
    if any(not part for part in parts):
        return {"ok": False, "providers": [], "source": "env", "reason": "blank_provider"}

    if len(parts) == 1 and parts[0] in {"none", "off", "disabled"}:
        return {"ok": True, "providers": [], "source": "env_disabled"}

    unknown = sorted({part for part in parts if part not in SUPPORTED_EXTERNAL_PROVIDERS})
    if unknown:
        return {
            "ok": False,
            "providers": [],
            "source": "env",
            "reason": "unsupported_provider_in_allowlist:" + ",".join(unknown),
        }

    ordered = list(dict.fromkeys(parts))
    return {"ok": True, "providers": ordered, "source": "env"}


def external_provider_policy(provider: str, *, allowlist_raw: str | None = None) -> dict:
    requested = _normalize_provider_name(provider)
    allowlist = parse_external_provider_allowlist(allowlist_raw)
    if not bool(allowlist.get("ok")):
        return {
            "ok": False,
            "provider": requested,
            "reason": f"invalid_provider_allowlist:{allowlist.get('reason')}",
            "allowed_providers": [],
            "policy_source": allowlist.get("source"),
        }

    allowed = list(allowlist.get("providers") or [])
    if not requested:
        return {
            "ok": False,
            "provider": requested,
            "reason": "missing_provider",
            "allowed_providers": allowed,
            "policy_source": allowlist.get("source"),
        }
    if requested not in SUPPORTED_EXTERNAL_PROVIDERS:
        return {
            "ok": False,
            "provider": requested,
            "reason": f"unsupported_provider:{requested}",
            "allowed_providers": allowed,
            "policy_source": allowlist.get("source"),
        }
    if requested not in allowed:
        return {
            "ok": False,
            "provider": requested,
            "reason": f"provider_not_allowed:{requested}",
            "allowed_providers": allowed,
            "policy_source": allowlist.get("source"),
        }
    return {
        "ok": True,
        "provider": requested,
        "reason": "provider_allowed",
        "allowed_providers": allowed,
        "policy_source": allowlist.get("source"),
    }


def report_root() -> Path:
    root = runtime_dir() / REPORT_DIRNAME
    root.mkdir(parents=True, exist_ok=True)
    return root


def config_path() -> Path:
    root = config_dir()
    root.mkdir(parents=True, exist_ok=True)
    return root / CONFIG_FILENAME
