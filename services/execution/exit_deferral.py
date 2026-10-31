"""Unwired, pure exit planner. No submissions, persistence or execution authority."""

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction

from services.markets.math_utils import decimal_value


FLAGS = ("trading_disabled", "cancel_only", "limit_only", "post_only", "auction_mode")


def _integer(value, *, positive=False):
    if type(value) is not int or value < (1 if positive else 0):
        raise ValueError("explicit_valid_integer_required")
    return value


def _units(value):
    if type(value) not in (str, int, Decimal):
        raise ValueError("exact_quantity_required")
    result = Fraction(decimal_value(value, name="quantity"))
    if result < 0:
        raise ValueError("negative_quantity")
    return result


@dataclass(frozen=True)
class ExitPolicy:
    max_metadata_age_ms: int
    base_retry_ms: int
    max_retry_ms: int
    max_attempts: int

    def __post_init__(self):
        for value in (self.max_metadata_age_ms, self.base_retry_ms, self.max_retry_ms, self.max_attempts):
            _integer(value, positive=True)
        if self.max_retry_ms < self.base_retry_ms:
            raise ValueError("retry_cap_below_base")


def plan_exit(intent, observation, progress, *, now_ms, policy):
    """Evaluate caller-supplied evidence, without changing the intent or progress.

    progress: intent_id, venue, product_id, attempts, last_attempt_ms, outcome,
    confirmed_filled_quantity.
    Outcomes: never_submitted, rejected, cancelled, open, unknown, filled.
    Evidence is asserted by the caller, not independently authenticated here.
    ELIGIBLE_FOR_EXISTING_GATES is not an order or permission to submit.
    """
    now = _integer(now_ms)
    if not isinstance(policy, ExitPolicy):
        raise ValueError("explicit_exit_policy_required")
    if not isinstance(intent, dict) or not isinstance(progress, dict):
        raise ValueError("explicit_intent_and_progress_required")
    for key in ("intent_id", "product_id"):
        if type(intent.get(key)) is not str or not intent[key].strip():
            raise ValueError("intent_identity_required")
    if intent.get("venue") != "coinbase" or intent.get("side") != "sell":
        raise ValueError("coinbase_sell_intent_required")
    if any(progress.get(key) != intent[key] for key in ("intent_id", "venue", "product_id")):
        raise ValueError("progress_identity_mismatch")
    if intent.get("order_type") not in ("market", "limit"):
        raise ValueError("unsupported_order_type")
    quantity = _units(intent.get("quantity"))
    if quantity <= 0:
        raise ValueError("positive_exit_quantity_required")
    if intent["order_type"] == "limit" and _units(intent.get("limit_price")) <= 0:
        raise ValueError("positive_limit_price_required")
    attempts = _integer(progress.get("attempts"))
    last = progress.get("last_attempt_ms")
    filled = _units(progress.get("confirmed_filled_quantity"))
    outcome = progress.get("outcome")
    if filled > quantity:
        raise ValueError("filled_exceeds_original")
    if attempts == 0:
        if last is not None or outcome != "never_submitted" or filled:
            raise ValueError("inconsistent_initial_progress")
    elif (_integer(last) > now or outcome not in ("rejected", "cancelled", "open", "unknown", "filled")):
        raise ValueError("invalid_attempt_progress")
    if outcome == "filled" and filled != quantity:
        raise ValueError("inconsistent_terminal_fill")
    remaining = quantity - filled

    def decision(status, reason, next_check=None):
        return {
            "status": status, "reason": reason, "intent": deepcopy(intent),
            "progress": deepcopy(progress), "remaining_units": [remaining.numerator, remaining.denominator],
            "next_check_ms": next_check, "request": None, "execution_authority": False,
            "evidence_authenticated": False,
            "alert_event": ({"type": "exit_deferred", "intent_id": intent["intent_id"],
                "product_id": intent["product_id"], "reason": reason, "delivery_verified": False}
                if status in ("DEFER", "RECONCILE", "NEEDS_OPERATOR") else None),
        }

    if outcome in ("open", "unknown"):
        return decision("RECONCILE", "existing_order_open_or_uncertain")
    if not remaining:
        if outcome != "filled":
            return decision("RECONCILE", "terminal_fill_not_confirmed")
        return decision("COMPLETE", "caller_confirmed_filled")
    if attempts >= policy.max_attempts:
        return decision("NEEDS_OPERATOR", "attempt_budget_exhausted")
    if attempts:
        # Saturate the exponent before shifting, even for a very large counter.
        delay = min(policy.max_retry_ms, policy.base_retry_ms << min(attempts - 1, policy.max_retry_ms.bit_length()))
        due = last + delay
        if now < due:
            return decision("DEFER", "retry_not_due", due)

    next_check = now + policy.base_retry_ms
    if not isinstance(observation, dict) or observation.get("venue") != "coinbase":
        return decision("DEFER", "metadata_unknown", next_check)
    received = observation.get("received_at_ms")
    if type(received) is not int or received < 0 or received > now:
        return decision("DEFER", "metadata_clock_unknown", next_check)
    if now - received > policy.max_metadata_age_ms:
        return decision("DEFER", "metadata_stale", next_check)
    product = observation.get("product")
    if not isinstance(product, dict) or product.get("id") != intent["product_id"]:
        return decision("DEFER", "metadata_product_mismatch", next_check)
    if (type(product.get("status")) is not str or not product["status"]
            or any(type(product.get(flag)) is not bool for flag in FLAGS)
            or ("view_only" in product and type(product["view_only"]) is not bool)):
        return decision("DEFER", "metadata_flags_unknown", next_check)
    if product["status"] != "online" or product["trading_disabled"] or product.get("view_only", False):
        return decision("DEFER", "product_not_tradable", next_check)
    if product["cancel_only"]:
        return decision("DEFER", "cancel_only", next_check)
    if product["auction_mode"] or product["post_only"]:
        return decision("DEFER", "unsupported_auction_or_post_only", next_check)
    if product["limit_only"] and intent["order_type"] != "limit":
        return decision("DEFER", "market_exit_disallowed", next_check)
    return decision("ELIGIBLE_FOR_EXISTING_GATES", "supplied_evidence_allows_reassessment")
