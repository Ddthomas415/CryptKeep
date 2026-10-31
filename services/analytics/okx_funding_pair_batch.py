"""Explicit multi-symbol funding capture budget; no scheduler or store creation."""

import base64
import re
import subprocess
import time

from services.analytics.okx_funding_journal import pair_journal_inputs
from services.analytics.okx_funding_pair_producer import _seconds, _utc, collect_okx_funding_pair


def validate_okx_pair_plan(plan_rows, options):
    """Return validated copies without clocks, capture, storage or side effects."""
    keys = {"max_requests", "total_timeout_seconds", "request_timeout_seconds", "max_response_bytes"}
    if type(plan_rows) is not list or not plan_rows or type(options) is not dict or set(options) != keys:
        raise ValueError("explicit_pair_plan_and_options_required")
    options = dict(options)
    rows = []
    seen = set()
    for item in plan_rows:
        if (type(item) is not dict or item.get("venue") != "okx"
                or type(item.get("symbol")) is not str or not item["symbol"].strip()
                or type(item.get("inst_id")) is not str
                or re.fullmatch(r"[A-Z0-9]+-[A-Z0-9]+-SWAP", item["inst_id"]) is None
                or item["inst_id"] in seen):
            raise ValueError("explicit_distinct_okx_native_id_required")
        seen.add(item["inst_id"])
        rows.append(dict(item))
    if (type(options["max_requests"]) is not int or options["max_requests"] != 2 * len(rows)
            or not _seconds(options["total_timeout_seconds"], 30)
            or not _seconds(options["request_timeout_seconds"], 10)
            or type(options["max_response_bytes"]) is not int
            or not 0 < options["max_response_bytes"] <= 1048576):
        raise ValueError("explicit_whole_batch_request_and_time_budgets_required")
    return rows, options


def collect_okx_pair_batch(plan_rows, options, *, run=None, utc=None, monotonic=None):
    """Prevalidate all identities/options before any capture; preserve failures."""
    rows, options = validate_okx_pair_plan(plan_rows, options)
    utc = _utc if utc is None else utc
    monotonic = time.monotonic if monotonic is None else monotonic
    if not callable(utc) or not callable(monotonic) or (run is not None and not callable(run)):
        raise ValueError("pair_dependencies_must_be_callable")
    start = monotonic()
    deadline = start + options["total_timeout_seconds"]
    transport = subprocess.run if run is None else run
    def bounded_run(command, **kwargs):
        remaining = deadline - monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired(command, 0)
        timeout = min(kwargs["timeout"], remaining)
        command = list(command)
        command[command.index("--max-time") + 1] = str(timeout)
        command[command.index("--connect-timeout") + 1] = str(min(5, timeout))
        return transport(command, **(kwargs | {"timeout": timeout}))
    inputs, checks = [], []
    attempted, successes = 0, 0
    for row in rows:
        remaining = deadline - monotonic()
        if remaining <= 0:
            result = {"ok": False, "reason": "okx_pair_batch_deadline_exhausted",
                      "requests_attempted": 0, "captures": []}
        else:
            result = collect_okx_funding_pair(
                inst_id=row["inst_id"], enabled=True, max_requests=2,
                total_timeout_seconds=remaining,
                request_timeout_seconds=options["request_timeout_seconds"],
                max_response_bytes=options["max_response_bytes"], run=bounded_run, utc=utc, monotonic=monotonic)
            if result["ok"] and monotonic() >= deadline:
                result = {**result, "ok": False, "reason": "okx_pair_batch_deadline_exhausted"}
        attempted += result["requests_attempted"]
        successes += int(result["ok"])
        checks.append({"kind": "funding", "venue": "okx", "symbol": row["symbol"],
                       "inst_id": row["inst_id"], "ok": result["ok"], "reason": result["reason"],
                       "requests_attempted": result["requests_attempted"], "diagnostic_only": True,
                       "normalization_eligible": False})
        if result["ok"]:
            inputs.append(pair_journal_inputs(**result["pair"]))
        else:
            captures = [{key: value for key, value in capture.items() if key != "body"}
                        | {"body_base64": base64.b64encode(capture["body"]).decode("ascii")}
                        for capture in result["captures"]]
            inputs.append({"venue": "okx", "symbol": row["inst_id"], "captured_at": utc(),
                           "payload": {"contract": "okx_public_pair_attempt_v1",
                                       "requested_inst_id": row["inst_id"], "configured_symbol": row["symbol"],
                                       "reason": result["reason"], "captures": captures}})
    return inputs, checks, {
        "ok": successes == len(rows), "planned_pairs": len(rows), "successful_pairs": successes,
        "failed_pairs": len(rows) - successes, "requests_attempted": attempted,
        "request_budget": options["max_requests"], "capture_budget_seconds": options["total_timeout_seconds"],
        "elapsed_capture_seconds": monotonic() - start, "execution_authority": False,
    }
