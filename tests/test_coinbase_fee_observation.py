import pytest
import logging

from scripts.research.observe_coinbase_fee_tier import observe, rate, summarize


def test_explicit_names_not_swapped_and_sensitive_values_discarded():
    result = summarize({"fee_tier": {"maker_fee_rate": "0.006", "taker_fee_rate": "0.012"},
                        "total_balance": "secret", "total_volume": "secret"})
    assert result["maker_bps"] == 60 and result["taker_bps"] == 120
    assert "secret" not in str(result)
    assert result["has_promo_fee"] is None


@pytest.mark.parametrize("value", [None, True, "nan", "inf", "abc", "-0.1", "1"])
def test_bad_taker_rates_refused(value):
    with pytest.raises(ValueError): rate(value)


def test_maker_rebate_allowed():
    assert rate("-0.0001", maker=True) == -1


def test_missing_credentials_does_not_build_client():
    result = observe(loader=lambda _: {}, factory=lambda *a, **k: pytest.fail("client built"))
    assert result["status"] == "MISSING_EXISTING_CREDENTIALS"
    assert not result["private_request_attempted"]


def test_single_get_request_and_no_exception_text():
    class Client:
        id = "coinbase"
        urls = {"api": {"rest": "https://api.coinbase.com"}}
        calls = 0
        def v3PrivateGetBrokerageTransactionSummary(self, params):
            assert params == {"product_type": "SPOT"}
            self.calls += 1
            raise RuntimeError("APIKEY SECRET ACCOUNT")
    client = Client()
    result = observe(loader=lambda _: {"apiKey": "key", "secret": "secret"},
                     factory=lambda *a, **kw: client)
    assert client.calls == 1 and result["error_type"] == "RuntimeError"
    assert "APIKEY" not in str(result) and "SECRET" not in str(result)


def test_unexpected_target_refused_before_request():
    class Client:
        id = "coinbase"
        urls = {"api": {"rest": "https://example.com"}}
    result = observe(loader=lambda _: {"apiKey": "key", "secret": "secret"},
                     factory=lambda *a, **kw: Client())
    assert result["status"] == "OBSERVATION_FAILED"
    assert not result["private_request_attempted"]


def test_debug_transport_cannot_emit_secrets_or_change_global_logging(caplog):
    logger = logging.getLogger("ccxt.base.exchange")
    previous = (logger.disabled, logger.level, logger.propagate)
    class Client:
        id = "coinbase"
        urls = {"api": {"rest": "https://api.coinbase.com"}}
        def v3PrivateGetBrokerageTransactionSummary(self, params):
            self.logger.debug("Authorization Bearer SECRETKEY account_balance 123456")
            return {"fee_tier": {"maker_fee_rate": "0.006", "taker_fee_rate": "0.012"}}
    client = Client()
    with caplog.at_level(logging.DEBUG):
        result = observe(loader=lambda _: {"apiKey": "key", "secret": "secret"},
                         factory=lambda *a, **kw: client)
    assert result["status"] == "OBSERVED_ACCOUNT_SPOT_FEE_TIER"
    assert "SECRETKEY" not in caplog.text and "123456" not in caplog.text
    assert (logger.disabled, logger.level, logger.propagate) == previous
    assert client.logger is not logger and client.logger.disabled
