"""Offline, as-recorded forecast cash-cost comparison; never a trading signal."""

from datetime import datetime
from decimal import Context, Decimal, DecimalException, Underflow, localcontext

from services.analytics.okx_funding_contract import describe_okx_funding_pair


API_DOCUMENT_SHA256 = "a9a4deb54a6a7cfbb8ea1332b069f359787f8a29991d31956f8ccddd074c55ec"


def _time(value):
    if type(value) is not str or not value.isascii() or not value.isdigit():
        return None
    number = int(value)
    return number if 0 < number <= 253402300799999 else None


def compare_okx_cash_costs(**inputs):
    """Apply documented current-period semantics to a validated saved pair.

    A formula version is not required to express a published per-period cash
    rate in a common unit. This does not invert the premium/crowding formula.
    """
    evidence = describe_okx_funding_pair(**inputs)
    row = evidence["raw_current"]["data"][0]
    source_time = _time(row.get("ts"))
    funding_time = _time(row.get("fundingTime"))
    next_time = _time(row.get("nextFundingTime"))
    received = datetime.fromisoformat(inputs["current_receipt"]["received_at"].replace("Z", "+00:00"))
    received_ms = int(received.timestamp() * 1000)
    reasons = []
    if row.get("method") != "current_period":
        reasons.append("current_period_mechanism_required")
    if evidence["current"]["decimal_rate"] is None:
        reasons.append("forecast_rate_unknown")
    if source_time is None or source_time > received_ms:
        reasons.append("source_time_unknown_or_future")
    if funding_time is None or next_time is None or next_time <= funding_time:
        reasons.append("scheduled_interval_unknown")
    if funding_time is not None and funding_time <= received_ms:
        reasons.append("settlement_not_upcoming_at_receipt")
    interval, normalized = None, None
    if not reasons:
        try:
            with localcontext(Context(prec=50)) as ctx:
                ctx.traps[Underflow] = True
                interval = Decimal(next_time - funding_time) / Decimal(3600000)
                normalized = Decimal(evidence["current"]["decimal_rate"]) * Decimal(8) / interval
            interval, normalized = str(interval), str(normalized)
        except DecimalException:
            interval, normalized = None, None
            reasons.append("cash_cost_arithmetic_unrepresentable")
    return {
        "schema": 1, "contract": "okx_forecast_cash_cost_v1",
        "evidence": evidence, "api_document_sha256": API_DOCUMENT_SHA256,
        "forecast_cash_cost": {
            "calculation_available": not reasons,
            "as_of_receipt": inputs["current_receipt"]["received_at"],
            "source_time_ms": source_time, "funding_time_ms": funding_time,
            "source_field": "fundingRate", "kind": "forecast_not_settled",
            "per_period_decimal_rate": evidence["current"]["decimal_rate"],
            "scheduled_interval_hours": interval, "forecast_rate_per_8h": normalized,
            "positive_rate_means": "long_pays_short", "reasons": reasons,
            "live_freshness_verified": False,
        },
        "reported_settlements": [{
            "funding_time_ms": event["funding_time_ms"],
            "source_field": "realizedRate", "kind": "venue_reported_actual_per_period",
            "per_period_decimal_rate": event["realized"]["decimal_rate"],
            "settled_rate_per_8h": None, "reason": "effective_settled_interval_unverified",
        } for event in evidence["history"]],
        "crowding_comparable": False, "formula_inversion_performed": False,
        "strategy_eligible": False, "execution_authority": False, "annualized_pct": None,
        "limitations": ["forecast_may_change_before_settlement", "caller_origin_not_authenticated",
                        "no_account_payment_or_profit_evidence", "no_future_frequency_guarantee"],
    }
