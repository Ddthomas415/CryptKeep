"""Opt-in paged balance observation; no client creation or account authority."""

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import inspect
import math
from time import monotonic

from services.execution.coinbase_account_pages import Pager, read_account_pages_async, read_account_pages_sync

POLICY_KEY = "cbp_balance_paging"
POLICY_FIELDS = {"version", "scope", "page_size", "max_pages", "max_rows", "max_json_bytes", "timeout_seconds"}


class BalanceObservationError(RuntimeError):
    pass


def validate_balance_paging_policy(policy, *, venue):
    if venue != "coinbase" or type(policy) is not dict or set(policy) != POLICY_FIELDS:
        raise ValueError("explicit_coinbase_balance_paging_policy_required")
    timeout = policy["timeout_seconds"]
    if type(timeout) not in (int, float) or not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("positive_finite_paging_window_required")
    settings = {key: deepcopy(value) for key, value in policy.items() if key != "timeout_seconds"}
    Pager(**settings, deadline=1, clock=lambda: 0)
    if settings["scope"][0] != "coinbase":
        raise ValueError("coinbase_scope_required")
    return deepcopy(policy)


def _configured(client):
    options = getattr(client, "options", None)
    if not isinstance(options, dict) or POLICY_KEY not in options:
        return None
    venue = str(getattr(client, "id", "") or "").lower().strip()
    return validate_balance_paging_policy(options[POLICY_KEY], venue=venue)


def _budget(policy):
    previous = None
    def clock():
        nonlocal previous
        try:
            now = monotonic()
        except Exception as error:
            raise BalanceObservationError(f"paging_clock_failed:{type(error).__name__}") from None
        if (type(now) not in (int, float) or not math.isfinite(now)
                or previous is not None and now < previous):
            raise BalanceObservationError("invalid_paging_clock")
        previous = now
        return now
    start = clock()
    deadline = start + policy["timeout_seconds"]
    settings = {key: deepcopy(value) for key, value in policy.items() if key != "timeout_seconds"}
    settings.update(deadline=deadline, clock=clock)
    Pager(**settings)  # Reject overflow before any balance endpoint is obtained.
    return settings


def _same_amounts(actual, expected):
    if type(actual) is not dict or actual.keys() != expected.keys():
        return False
    for currency, value in actual.items():
        if type(value) not in (str, int, float, Decimal):
            return False
        try:
            number = Decimal(str(value))
            if not number.is_finite() or number < 0 or Fraction(number) != Fraction(*expected[currency]):
                return False
        except (InvalidOperation, ValueError, TypeError, OverflowError):
            return False
    return True


def _finish(client, result, settings):
    if result.get("status") != "COMPLETE" or type(result.get("view")) is not dict:
        raise BalanceObservationError("complete_supplied_pages_unavailable")
    if settings["clock"]() >= settings["deadline"]:
        raise BalanceObservationError("paging_window_expired")
    view = result["view"]
    try:
        balance = client.parse_custom_balance(deepcopy(view["info"]), {"type": "spot"})
    except Exception as error:
        raise BalanceObservationError(f"balance_parser_failed:{type(error).__name__}") from None
    if inspect.isawaitable(balance):
        if inspect.iscoroutine(balance):
            balance.close()
        raise BalanceObservationError("synchronous_balance_parser_required")
    if (type(balance) is not dict or balance.get("info") != view["info"]
            or not _same_amounts(balance.get("total"), view["total"])
            or result["version"] == "v3" and (
                not _same_amounts(balance.get("free"), view["available"])
                or not _same_amounts(balance.get("used"), view["used"]))):
        raise BalanceObservationError("native_and_parsed_balance_disagree")
    if settings["clock"]() >= settings["deadline"]:
        raise BalanceObservationError("paging_window_expired")
    if POLICY_KEY in balance:
        raise BalanceObservationError("reserved_balance_key_collision")
    balance[POLICY_KEY] = {
        "all_supplied_pages_returned": True, "version": result["version"],
        "scope": deepcopy(result["scope"]), "endpoint_method": result["endpoint_method"],
        "page_callbacks_attempted": result["page_callbacks_attempted"],
        "native_total_fractions": deepcopy(view["total"]),
        "qualification": result["qualification"], "scope_authenticated": False,
        "spendable_verified": False, "transport_limits_verified": False,
        "execution_authority": False,
    }
    return balance


def read_balance_sync(client):
    policy = _configured(client)
    if policy is None:
        return client.fetch_balance()
    settings = _budget(policy)
    return _finish(client, read_account_pages_sync(client, **settings), settings)


async def read_balance_async(client):
    policy = _configured(client)
    if policy is None:
        balance = client.fetch_balance()
        return await balance if inspect.isawaitable(balance) else balance
    settings = _budget(policy)
    return _finish(client, await read_account_pages_async(client, **settings), settings)
