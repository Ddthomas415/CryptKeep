"""Compose reviewed helpers; diagnostic quotes never authorize capital."""
from scripts.research.cmc_endpoint_timing import select_endpoint
from scripts.research.cmc_quote_evidence import inspect_quote
from scripts.research.cmc_return_math import paired_excess


def evaluate(event, endpoints, horizon_days):
    """Event contains cohort status, capture-time identity and coin/BTC quotes.

    Endpoints carry explicit identity eligibility and coin/BTC quotes. Callers
    must obtain cohort classification from validated daily source observations.
    No list history, quote provenance or freshness is inferred here.
    """
    scope = "DIAGNOSTIC_ONLY_NOT_EXECUTABLE_PROFIT_OR_PROMOTION"
    if event["cohort_status"] != "PRIMARY_COHORT_CANDIDATE":
        return {"status": "EXCLUDED_COHORT", "scope": scope}
    if event.get("identity_eligible") is not True:
        return {"status": "EXCLUDED_IDENTITY", "scope": scope}
    entry = inspect_quote(event["coin_quote"])
    btc_entry = inspect_quote(event["btc_quote"])
    if entry["status"] != "STRUCTURALLY_VALID" or btc_entry["status"] != "STRUCTURALLY_VALID":
        return {"status": "INVALID_ENTRY_QUOTE", "scope": scope}
    if abs((btc_entry["received_utc"]-entry["received_utc"]).total_seconds()) > 60:
        return {"status": "UNMATCHED_ENTRY_TIMES", "scope": scope}
    candidates = []
    for endpoint in endpoints:
        if endpoint.get("identity_eligible") is not True:
            continue
        coin, btc = inspect_quote(endpoint["coin_quote"]), inspect_quote(endpoint["btc_quote"])
        if (coin["status"] == btc["status"] == "STRUCTURALLY_VALID"
                and abs((btc["received_utc"]-coin["received_utc"]).total_seconds()) <= 60):
            candidates.append((coin["received_utc"], (coin, btc)))
    selected = select_endpoint(entry["received_utc"], horizon_days, candidates)
    if selected["status"] == "MISSING":
        return {**selected, "scope": scope}
    coin, btc = selected.pop("reference")
    return {**selected, **paired_excess(entry["ask"], coin["bid"], btc_entry["ask"], btc["bid"]),
            "status": "DIAGNOSTIC", "scope": scope, "freshness": "UNVERIFIED",
            "btc_entry_time": btc_entry["received_utc"], "btc_exit_time": btc["received_utc"],
            "btc_entry_offset_seconds": (btc_entry["received_utc"]-entry["received_utc"]).total_seconds(),
            "btc_exit_offset_seconds": (btc["received_utc"]-coin["received_utc"]).total_seconds(),
            "maximum_pair_offset_seconds": 60,
            "scoring_authorized": False}
