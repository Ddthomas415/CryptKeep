from __future__ import annotations

from typing import Any

from services.admin.config_editor import load_user_yaml
from services.market_data.symbol_router import normalize_venue
from services.security.credentials_loader import load_exchange_credentials


def _configured_venues() -> list[str]:
    cfg = load_user_yaml()
    exchanges = cfg.get("exchanges") if isinstance(cfg.get("exchanges"), dict) else {}
    venues = sorted(normalize_venue(str(name)) for name in exchanges if str(name).strip())
    return venues or ["coinbase"]


def credential_source_posture(*, venues: list[str] | tuple[str, ...] | None = None) -> dict[str, Any]:
    """Read-only credential-source report with values redacted by construction."""

    selected = [normalize_venue(str(v)) for v in (venues or _configured_venues()) if str(v).strip()]
    rows: list[dict[str, Any]] = []
    for venue in selected:
        try:
            creds = load_exchange_credentials(venue)
        except Exception as exc:
            rows.append(
                {
                    "venue": venue,
                    "ok": False,
                    "source": "error",
                    "reason": f"credential_load_failed:{type(exc).__name__}",
                    "api_key_present": False,
                    "secret_present": False,
                    "password_present": False,
                }
            )
            continue
        rows.append(
            {
                "venue": venue,
                "ok": bool(creds.get("api_key_present")) and bool(creds.get("secret_present")),
                "source": str(creds.get("source") or "unknown"),
                "api_key_present": bool(creds.get("api_key_present")),
                "secret_present": bool(creds.get("secret_present")),
                "password_present": bool(creds.get("password_present")),
                "api_env": str(creds.get("api_env") or ""),
                "secret_env": str(creds.get("secret_env") or ""),
                "password_env": str(creds.get("password_env") or ""),
                "keyring_error": str(creds.get("keyring_error") or ""),
            }
        )

    env_active = [row["venue"] for row in rows if row.get("source") == "env" and row.get("ok")]
    missing = [row["venue"] for row in rows if not row.get("ok")]
    status = "ok"
    if missing:
        status = "credentials_missing"
    elif env_active:
        status = "env_credentials_active"
    return {
        "ok": not missing,
        "status": status,
        "read_only": True,
        "venues": rows,
        "env_credential_venues": env_active,
        "missing_credential_venues": missing,
        "credential_values_logged": False,
    }
