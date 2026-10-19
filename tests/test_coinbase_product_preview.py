import pytest
from scripts.research.observe_coinbase_product_preview import number, observe, summary, restrict_transport
from scripts.research.observe_coinbase_product_preview import main


@pytest.mark.parametrize("value", [True, "NaN", "Infinity", "1e10000"])
def test_nonfinite_or_extreme_numbers_refused(value):
    with pytest.raises(ValueError):
        number(value)


def test_missing_commission_never_defaults_to_zero():
    with pytest.raises(ValueError, match="missing_commission"):
        summary({"errs": []}, "BTC-USD", "market_taker")
    assert summary({"errs": ["error"]}, "BTC-USD", "market_taker")["status"] == "PREVIEW_ERRORS_UNVERIFIED"


def test_observer_calls_only_product_book_and_preview_methods():
    calls = []
    class Client:
        class Session:
            def request(self, *args, **kwargs):
                raise AssertionError("fixture transport unused")
        session = Session()
        id = "coinbase"
        urls = {"api": {"rest": "https://api.coinbase.com"}}
        def v3PublicGetBrokerageMarketProductsProductId(self, query):
            return {"product_id": query["product_id"], "quote_currency_id": "USD", "quote_increment": "0.01"}
        def v3PublicGetBrokerageMarketProductBook(self, query):
            return {"pricebook": {"product_id": query["product_id"], "bids": [{"price": "100"}]}}
        def v3PrivatePostBrokerageOrdersPreview(self, query):
            calls.append(query)
            assert set(query) == {"product_id", "side", "order_configuration"}
            return {"errs": [], "commission_total": "1.25", "quote_size": "500", "base_size": "5"}
    result = observe(lambda venue: {"apiKey": "fixture", "secret": "fixture"}, lambda *a, **k: Client())
    assert result["status"] == "PREVIEW_LOOKUP_COMPLETE"
    assert len(calls) == 4
    assert result["orders_submitted"] is False
    assert all(row["realized_fee_verified"] is False for row in result["requests"])


def test_exception_text_cannot_leak_credentials():
    def factory(*a, **k):
        raise RuntimeError("secret fixture must not appear")
    result = observe(lambda venue: {"apiKey": "fixture", "secret": "fixture"}, factory)
    assert result["status"] == "PREVIEW_LOOKUP_INCOMPLETE"
    assert "secret fixture" not in str(result)


@pytest.mark.parametrize("field,value", [("quote_size", "-1"), ("base_size", "0"),
                                         ("commission_total", "-1"), ("commission_total", "501")])
def test_impossible_successful_preview_fields_rejected(field, value):
    response = {"errs": [], "commission_total": "2.50", "quote_size": "500", "base_size": "1"}
    response[field] = value
    with pytest.raises(ValueError):
        summary(response, "BTC-USD", "market_taker")


@pytest.mark.parametrize("status", [307, 308])
def test_real_ccxt_dispatch_refuses_redirects(status):
    import ccxt
    from requests import Response
    client = ccxt.coinbase()
    calls = []
    def request(method, url, **kwargs):
        calls.append((method, url, kwargs))
        response = Response()
        response.status_code = status
        response.headers["Location"] = "https://api.coinbase.com/api/v3/brokerage/orders"
        return response
    client.session.request = request
    restrict_transport(client)
    with pytest.raises(ValueError, match="transport_redirect_refused"):
        client.fetch("https://api.coinbase.com/api/v3/brokerage/orders/preview", "POST", {}, "{}")
    assert len(calls) == 1
    assert calls[0][2]["allow_redirects"] is False
    with pytest.raises(ValueError, match="transport_target_refused"):
        client.fetch("https://api.coinbase.com/api/v3/brokerage/orders", "POST", {}, "{}")
    assert len(calls) == 1


@pytest.mark.parametrize("status,rows,expected", [
    ("PREVIEW_LOOKUP_INCOMPLETE", [], 1),
    ("PREVIEW_LOOKUP_COMPLETE", [{"status": "PREVIEW_ERRORS_UNVERIFIED"}] * 4, 1),
    ("PREVIEW_LOOKUP_COMPLETE", [], 1),
    ("PREVIEW_LOOKUP_COMPLETE", [{"status": "PRODUCT_FEE_PREVIEW_ESTIMATE"}] * 4, 0),
])
def test_cli_status_matches_saved_evidence(tmp_path, status, rows, expected):
    import json
    output = tmp_path / "receipt.json"
    result = {"status": status, "requests": rows}
    assert main(["--output", str(output)], observer=lambda: result) == expected
    assert json.loads(output.read_text()) == result
