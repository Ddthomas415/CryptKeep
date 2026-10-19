"""Pure analytical identity helpers; never trading or promotion authority."""
from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

_FIELDS = {
    "version", "cohort_id", "strategy_name", "parameters", "entry_policy",
    "exit_policy", "sizing", "costs", "market", "implementation",
}
_SHA = re.compile(r"[0-9a-f]{64}")
_IMPLEMENTATIONS = {"signal", "resolver", "exits", "paper_engine"}


def _json_value(value: Any) -> None:
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("identity_nonfinite_value")
        return
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str or not key:
                raise ValueError("identity_invalid_key")
            _json_value(child)
        return
    if type(value) is list:
        for child in value:
            _json_value(child)
        return
    raise ValueError("identity_invalid_value_type")


def canonical_identity(payload: dict[str, Any]) -> bytes:
    """Validate and encode explicit resolved policy, not a preset label."""
    if type(payload) is not dict or set(payload) != _FIELDS:
        raise ValueError("identity_schema_fields")
    if type(payload["version"]) is not int or payload["version"] != 1:
        raise ValueError("identity_schema_version")
    for key in ("cohort_id", "strategy_name"):
        value = payload[key]
        if type(value) is not str or not value.strip() or value != value.strip():
            raise ValueError("identity_invalid_name")
    for key in ("parameters", "entry_policy", "exit_policy", "sizing"):
        if type(payload[key]) is not dict or not payload[key]:
            raise ValueError("identity_missing_policy")
    market = payload["market"]
    if type(market) is not dict or set(market) != {"venue", "symbol", "timeframe", "source", "sample_mode"}:
        raise ValueError("identity_market_schema")
    for key in ("venue", "symbol", "timeframe", "source"):
        if type(market[key]) is not str or not market[key].strip() or market[key] != market[key].strip():
            raise ValueError("identity_market_value")
    if type(market["sample_mode"]) is not bool:
        raise ValueError("identity_sample_mode_type")
    costs = payload["costs"]
    if type(costs) is not dict or set(costs) != {"fee_bps", "slippage_bps", "quote_currency", "basis_version"}:
        raise ValueError("identity_cost_schema")
    for key in ("fee_bps", "slippage_bps"):
        if type(costs[key]) not in (int, float) or not math.isfinite(costs[key]) or costs[key] < 0:
            raise ValueError("identity_cost_value")
    for key in ("quote_currency", "basis_version"):
        if type(costs[key]) is not str or not costs[key].strip() or costs[key] != costs[key].strip():
            raise ValueError("identity_cost_value")
    implementation = payload["implementation"]
    if type(implementation) is not dict or set(implementation) != _IMPLEMENTATIONS:
        raise ValueError("identity_implementation_schema")
    if any(type(digest) is not str or not _SHA.fullmatch(digest) for digest in implementation.values()):
        raise ValueError("identity_implementation_hash")
    _json_value(payload)
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def identity_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    raw = canonical_identity(payload)
    return {
        "execution_identity": json.loads(raw),
        "execution_identity_sha256": hashlib.sha256(raw).hexdigest(),
    }


def identity_rejection_reasons(evidence: dict[str, Any], *, expected_sha256: str) -> list[str]:
    """Fail closed for this opt-in analytical contract; do not alter an order."""
    if type(expected_sha256) is not str or not _SHA.fullmatch(expected_sha256):
        return ["invalid_expected_execution_identity"]
    if type(evidence) is not dict:
        return ["missing_execution_identity"]
    if "execution_identity" not in evidence or "execution_identity_sha256" not in evidence:
        return ["missing_execution_identity"]
    try:
        actual = identity_evidence(evidence["execution_identity"])["execution_identity_sha256"]
    except (ValueError, TypeError, OverflowError, RecursionError):
        return ["invalid_execution_identity"]
    if evidence["execution_identity_sha256"] != actual:
        return ["execution_identity_content_mismatch"]
    if actual != expected_sha256:
        return ["execution_identity_mismatch"]
    return []


def fill_identity_evidence(intent_meta: dict[str, Any], *, effective_costs: dict[str, Any]) -> dict[str, Any]:
    """Copy verified intent identity only when actual paper cost policy agrees."""
    if type(intent_meta) is not dict:
        raise ValueError("missing_execution_identity")
    digest = intent_meta.get("execution_identity_sha256")
    reasons = identity_rejection_reasons(intent_meta, expected_sha256=digest)
    if reasons:
        raise ValueError(reasons[0])
    payload = intent_meta["execution_identity"]
    if canonical_identity({**payload, "costs": effective_costs}) != canonical_identity(payload):
        raise ValueError("execution_identity_cost_mismatch")
    return identity_evidence(payload)
