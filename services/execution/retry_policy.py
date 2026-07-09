from __future__ import annotations

import random
import time

try:  # ccxt is the production dependency; classification degrades gracefully without it
    import ccxt as _ccxt
except Exception:  # pragma: no cover - exercised only in environments without ccxt
    _ccxt = None


def _ccxt_types(names: tuple[str, ...]) -> tuple[type, ...]:
    if _ccxt is None:
        return ()
    return tuple(t for t in (getattr(_ccxt, n, None) for n in names) if isinstance(t, type))


# Definitive rejections: the venue understood the request and said no, or the
# request itself is malformed/unauthorized. Retrying cannot succeed and, for
# submits, risks duplicates. InvalidNonce subclasses NetworkError in current
# ccxt (treated as transient upstream), but the legacy policy here is the
# stricter non-retryable stance; it is checked before the transient branch on
# purpose. Operator may relax that precedence in review if nonce-retry is
# desired.
_FATAL_CCXT = _ccxt_types((
    "InsufficientFunds",
    "InvalidOrder",        # covers OrderNotFound and other order-shape rejections
    "AuthenticationError",  # covers PermissionDenied, AccountSuspended
    "BadRequest",           # covers BadSymbol
    "ArgumentsRequired",
    "NotSupported",
    "InvalidNonce",
))

# Transient transport/venue-availability failures where the request may never
# have been processed: NetworkError covers RequestTimeout,
# ExchangeNotAvailable, OnMaintenance, DDoSProtection, RateLimitExceeded.
_TRANSIENT_CCXT = _ccxt_types(("NetworkError",))

# Exact type-name fallback for non-ccxt exceptions (e.g. transport errors
# raised outside the ccxt boundary, or fakes in tests). Exact equality only:
# no substring matching, so message text, order ids, and quantities can never
# influence classification.
_FATAL_TYPE_NAMES = frozenset({
    "insufficientfunds", "invalidorder", "ordernotfound", "badrequest",
    "badsymbol", "authenticationerror", "permissiondenied", "accountsuspended",
    "argumentsrequired", "invalidnonce", "notsupported",
})
_TRANSIENT_TYPE_NAMES = frozenset({
    "networkerror", "requesttimeout", "exchangenotavailable", "onmaintenance",
    "ddosprotection", "ratelimitexceeded", "connecttimeout", "readtimeout",
    "readtimeouterror", "connecttimeouterror",
})


def is_retryable_exception(e: Exception) -> bool:
    """
    Typed, affirmative-only, fail-closed retry classification (substrate #3).

    An exception is retryable only when its *type* marks it transient:
    ccxt ``NetworkError`` and subclasses, builtin ``ConnectionError``/
    ``TimeoutError``, or an exact transient type name for non-ccxt transport
    errors. Everything else — including ccxt's generic ``ExchangeError``/
    ``BaseError`` and any unknown exception — is NOT retryable: the order
    router's verify-before-retry reconcile lane and the reconciler own
    ambiguous outcomes, and a definitive-looking failure must be recorded,
    not blindly resubmitted.

    Message text is never consulted. The legacy classifier matched
    substrings of ``str(e)``, so an order id containing ``429``, a quantity
    containing ``503``, or venue phrasing like ``account service temporarily
    unavailable`` could flip classification; that entire class of hazard is
    removed here.
    """
    if _FATAL_CCXT and isinstance(e, _FATAL_CCXT):
        return False
    if _TRANSIENT_CCXT and isinstance(e, _TRANSIENT_CCXT):
        return True
    if _ccxt is not None and isinstance(e, _ccxt.BaseError):
        # Unknown venue error (generic ExchangeError or new subclass): the
        # request may have been processed. Fail closed; do not blind-retry.
        return False
    if isinstance(e, (ConnectionError, TimeoutError)):
        return True
    name = type(e).__name__.lower()
    if name in _FATAL_TYPE_NAMES:
        return False
    return name in _TRANSIENT_TYPE_NAMES


def backoff_sleep(attempt: int, base_delay_sec: float, max_delay_sec: float) -> float:
    a = max(0, int(attempt))
    base = max(0.05, float(base_delay_sec))
    cap = max(base, float(max_delay_sec))
    delay = min(cap, base * (2 ** a))
    jitter = random.uniform(0.0, min(0.25, delay * 0.15))
    sleep_for = delay + jitter
    time.sleep(sleep_for)
    return float(sleep_for)
