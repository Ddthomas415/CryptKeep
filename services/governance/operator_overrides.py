from __future__ import annotations

from services.profiles.bundles import apply_bundle


def apply_override(base_cfg: dict, bundle_name: str, *, overrides: dict) -> dict:
    risk = dict((overrides or {}).get("risk") or {})
    max_order_quote = risk.get("max_order_quote")
    if max_order_quote is not None and float(max_order_quote) > 1_000_000:
        raise ValueError("risk escalation rejected")
    return apply_bundle(base_cfg, bundle_name, overrides=overrides or {})
