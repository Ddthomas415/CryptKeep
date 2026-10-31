"""Explicit raw-journal pair adapter; no capture, initialization or activation."""

import base64
import binascii
from copy import deepcopy
from datetime import datetime

from services.analytics.funding_observations import encoded, identity, observation
from services.analytics.okx_funding_cash_cost import API_DOCUMENT_SHA256, compare_okx_cash_costs


CONTRACT = "okx_public_pair_journal_v1"


def _journal_inputs(pair, policy):
    captures = [pair[name + "_receipt"]["received_at"] for name in ("current", "history")]
    captured_at = max(captures, key=lambda value: datetime.fromisoformat(value.replace("Z", "+00:00")))
    payload = {
        "contract": CONTRACT, "api_document_sha256": API_DOCUMENT_SHA256,
        "requested_inst_id": pair["requested_inst_id"],
        "responses": {name: {
            "body_base64": base64.b64encode(pair[name + "_body"]).decode("ascii"),
            "receipt": deepcopy(pair[name + "_receipt"]),
        } for name in ("current", "history")},
    }
    return {"venue": "okx", "symbol": policy["evidence"]["inst_id"],
            "captured_at": captured_at, "payload": payload}


def pair_journal_inputs(**pair):
    """Validate the pair before wrapping original bytes in the existing schema."""
    return _journal_inputs(pair, compare_okx_cash_costs(**pair))


def _stored_pair(record, key):
    payload = record["raw_payload"]
    if (type(payload) is not dict or set(payload) != {
            "contract", "api_document_sha256", "requested_inst_id", "responses"}
            or payload["contract"] != CONTRACT or payload["api_document_sha256"] != API_DOCUMENT_SHA256
            or type(payload["responses"]) is not dict or set(payload["responses"]) != {"current", "history"}):
        raise ValueError("stored_okx_pair_contract_invalid")
    pair = {"requested_inst_id": payload["requested_inst_id"]}
    for name in ("current", "history"):
        response = payload["responses"][name]
        if type(response) is not dict or set(response) != {"body_base64", "receipt"}:
            raise ValueError("stored_okx_pair_response_invalid")
        pair[name + "_body"] = base64.b64decode(response["body_base64"], validate=True)
        pair[name + "_receipt"] = response["receipt"]
    policy = compare_okx_cash_costs(**pair)
    rebuilt = observation(**_journal_inputs(pair, policy))
    if encoded(rebuilt) != encoded(record) or identity(record) != key:
        raise ValueError("stored_okx_pair_record_invalid")
    return policy


def append_okx_funding_pairs(store, pairs, *, source, max_rows, max_bytes):
    """Use the existing bounded atomic writer on an explicitly supplied store."""
    if (type(source) is not str or not source or source != source.strip()
            or type(max_rows) is not int or max_rows <= 0
            or type(max_bytes) is not int or max_bytes <= 0):
        raise ValueError("explicit_okx_pair_source_and_budgets_required")
    def prepared():
        for count, pair in enumerate(pairs, start=1):
            if count > max_rows:
                raise ValueError("okx_pair_row_budget_exceeded")
            if type(pair) is not dict:
                raise ValueError("okx_pair_input_required")
            yield pair_journal_inputs(**pair)
    return store.append_raw_funding_observations(
        prepared(), source=source, max_rows=max_rows, max_bytes=max_bytes)


def recent_okx_funding_quotes(store, *, source, limit):
    """Recompute forecasts from raw evidence; do not trust saved derivatives."""
    if (type(source) is not str or not source or source != source.strip()
            or type(limit) is not int or limit <= 0):
        raise ValueError("explicit_okx_pair_source_and_limit_required")
    raw = store.recent_raw_funding_observations(source=source, limit=limit)
    quotes, diagnostics, unrelated = [], [], 0
    for entry in raw["observations"]:
        record = entry["observation"]
        payload = record.get("raw_payload")
        if type(payload) is not dict or payload.get("contract") != CONTRACT:
            unrelated += 1
            continue
        try:
            policy = _stored_pair(record, entry["observation_key"])
        except (KeyError, TypeError, ValueError, OverflowError, binascii.Error) as exc:
            diagnostics.append({"observation_key": entry["observation_key"],
                                "reason": "stored_okx_pair_unusable", "error_type": type(exc).__name__})
            continue
        quotes.append({"observation_key": entry["observation_key"],
                       "captured_at": record["captured_at"], "policy": policy})
    return {"source": source, "scan_limit": limit, "scan_exhaustive": False,
            "scanned": len(raw["observations"]), "unrelated_observations": unrelated,
            "quotes": quotes, "diagnostics": diagnostics,
            "normalization_eligible": False, "strategy_eligible": False, "execution_authority": False}
