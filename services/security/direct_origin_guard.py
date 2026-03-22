from __future__ import annotations

from typing import Mapping


ALLOWED_OUTER_ACCESS_CONTROLS = {
    "vpn",
    "tailscale",
    "reverse_proxy",
    "sso",
    "cloudflare_access",
}


def enforce_direct_origin_block(
    *,
    auth_scope: str,
    outer_access_control: str,
    headers: Mapping[str, str] | None = None,
) -> bool:
    scope = str(auth_scope or "").strip().lower()
    outer = str(outer_access_control or "").strip().lower()
    hdrs = {str(k).lower(): str(v) for k, v in (headers or {}).items()}

    if scope != "remote_public_candidate":
        return True

    if outer not in ALLOWED_OUTER_ACCESS_CONTROLS:
        raise PermissionError("remote mode requires enforced outer access control")

    trusted = hdrs.get("x-authenticated-proxy") or hdrs.get("x-cloudflare-access")
    if not trusted:
        raise PermissionError("direct-origin access blocked")

    return True
