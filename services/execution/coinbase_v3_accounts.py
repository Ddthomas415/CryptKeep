"""Native v3 row compatibility, not account completeness or order authority."""

from decimal import Decimal, InvalidOperation
from fractions import Fraction
import math


def _invalid():
    return RuntimeError("CBP_ORDER_BLOCKED:coinbase_v3_accounts_invalid")


def _text(value):
    if type(value) is not str or not value or value != value.strip():
        raise _invalid()
    return value


def _amount(part, currency):
    if type(part) is not dict or part.get("currency") != currency:
        raise _invalid()
    value = part.get("value")
    if type(value) not in (str, int) or len(str(value)) > 128:
        raise _invalid()
    try:
        number = Decimal(value)
        if not number.is_finite() or number < 0 or abs(number.as_tuple().exponent) > 100:
            raise _invalid()
        return Fraction(number)
    except (InvalidOperation, ValueError, OverflowError):
        raise _invalid() from None


def available_by_currency(balance, portfolio_uuid):
    """Return conservative v3 available amounts, or None for an untouched v2 view."""
    info = balance.get("info") if isinstance(balance, dict) else None
    metadata = balance.get("cbp_balance_paging") if isinstance(balance, dict) else None
    declared_v3 = isinstance(metadata, dict) and metadata.get("version") == "v3"
    if not (isinstance(info, dict) and "accounts" in info) and not declared_v3:
        return None
    if (type(info) is not dict or "data" in info or type(info.get("accounts")) is not list
            or info.get("error") or info.get("errors")):
        raise _invalid()
    portfolio_uuid = _text(portfolio_uuid)
    identities, amounts = {}, {}
    for row in info["accounts"]:
        if type(row) is not dict:
            raise _invalid()
        identity = _text(row.get("uuid"))
        if identity in identities:
            if identities[identity] != row:
                raise _invalid()
            continue
        identities[identity] = row
        currency = _text(row.get("currency"))
        if currency != currency.upper():
            raise _invalid()
        owner = _text(row.get("retail_portfolio_id"))
        available = _amount(row.get("available_balance"), currency)
        _amount(row.get("hold"), currency)  # Held funds never become available.
        eligible = (row.get("active") is True and row.get("ready") is True
                    and "deleted_at" in row and row["deleted_at"] in (None, "")
                    and row.get("type") in ("FIAT", "CRYPTO", "ACCOUNT_TYPE_FIAT", "ACCOUNT_TYPE_CRYPTO")
                    and not str(row.get("name") or "").strip().lower().startswith("staked "))
        if owner == portfolio_uuid and eligible:
            amounts[currency] = amounts.get(currency, Fraction(0)) + available
    result = {}
    for currency, amount in amounts.items():
        value = float(amount)
        if not math.isfinite(value):
            raise _invalid()
        # Funding compares Decimal(str(float)); never round that value above native evidence.
        if Fraction(str(value)) > amount:
            value = math.nextafter(value, 0.0)
        result[currency] = value
    return result
