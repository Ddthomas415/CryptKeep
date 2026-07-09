"""
Substrate backlog #3 proofs: typed, fail-closed retry classification.

Retry eligibility is decided by exception *type* only. Message text —
order ids, quantities, venue phrasing — must never influence
classification. Unknown exceptions, including ccxt's generic
ExchangeError base, are not retryable: definitive-looking failures are
recorded, and the router's verify-before-retry reconcile lane owns
ambiguity.
"""
from __future__ import annotations

import ccxt
import pytest

from services.execution.retry_policy import is_retryable_exception


# ---------------------------------------------------------------------------
# typed ccxt classification
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("exc_cls", [
    ccxt.NetworkError,
    ccxt.RequestTimeout,
    ccxt.ExchangeNotAvailable,
    ccxt.OnMaintenance,
    ccxt.DDoSProtection,
    ccxt.RateLimitExceeded,
])
def test_transient_ccxt_types_are_retryable(exc_cls):
    assert is_retryable_exception(exc_cls("x")) is True


@pytest.mark.parametrize("exc_cls", [
    ccxt.InsufficientFunds,
    ccxt.InvalidOrder,
    ccxt.OrderNotFound,
    ccxt.AuthenticationError,
    ccxt.PermissionDenied,
    ccxt.AccountSuspended,
    ccxt.BadRequest,
    ccxt.BadSymbol,
    ccxt.ArgumentsRequired,
    ccxt.NotSupported,
])
def test_fatal_ccxt_types_are_not_retryable(exc_cls):
    assert is_retryable_exception(exc_cls("x")) is False


def test_generic_exchange_error_fails_closed():
    """
    Contract change vs the legacy substring classifier: an unknown venue
    error may have been processed, so it must not be blind-retried.
    """
    assert is_retryable_exception(ccxt.ExchangeError("x")) is False
    assert is_retryable_exception(ccxt.BaseError("x")) is False


def test_invalid_nonce_stays_non_retryable_despite_ccxt_hierarchy():
    """
    ccxt classes InvalidNonce under NetworkError (transient); the legacy
    policy here is the stricter non-retryable stance, checked before the
    transient branch on purpose.
    """
    assert issubclass(ccxt.InvalidNonce, ccxt.NetworkError)  # hierarchy fact
    assert is_retryable_exception(ccxt.InvalidNonce("x")) is False


# ---------------------------------------------------------------------------
# message immunity: type wins, text never consulted
# ---------------------------------------------------------------------------


def test_fatal_type_with_transient_looking_message_is_not_retryable():
    for msg in ("connection reset", "timeout", "429 too many requests", "503"):
        assert is_retryable_exception(ccxt.InvalidOrder(msg)) is False


def test_transient_type_with_fatal_looking_message_is_retryable():
    """
    Legacy-bug regression: the substring classifier checked hard-no words
    first, so a NetworkError mentioning "account" (e.g. "account service
    temporarily unavailable") was misclassified as non-retryable.
    """
    for msg in ("account service temporarily unavailable", "insufficientfunds mentioned", "invalid order id 429"):
        assert is_retryable_exception(ccxt.NetworkError(msg)) is True


def test_plain_exceptions_with_scary_messages_are_not_retryable():
    """
    Legacy-bug regression: substring matching let order ids or quantities
    containing 429/503/"timeout" flip an arbitrary exception to retryable.
    """
    for exc in (
        RuntimeError("429 too many requests"),
        ValueError("order oid-503-x timed out"),
        Exception("temporary"),
        KeyError("connection reset"),
    ):
        assert is_retryable_exception(exc) is False


# ---------------------------------------------------------------------------
# non-ccxt transient transport errors
# ---------------------------------------------------------------------------


def test_builtin_connection_and_timeout_errors_are_retryable():
    assert is_retryable_exception(ConnectionError("x")) is True
    assert is_retryable_exception(ConnectionResetError("x")) is True
    assert is_retryable_exception(TimeoutError("x")) is True


def test_exact_type_name_fallback_for_non_ccxt_fakes():
    class RequestTimeout(Exception):
        pass

    class InsufficientFunds(Exception):
        pass

    class RequestTimeoutish(Exception):  # not an exact name match
        pass

    assert is_retryable_exception(RequestTimeout("x")) is True
    assert is_retryable_exception(InsufficientFunds("x")) is False
    assert is_retryable_exception(RequestTimeoutish("x")) is False


def test_unknown_exception_default_is_not_retryable():
    class VenueBurpedError(Exception):
        pass

    assert is_retryable_exception(VenueBurpedError("totally transient we promise")) is False
