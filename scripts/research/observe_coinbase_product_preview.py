"""Fee lookup via Coinbase previews only. Never creates or submits an order."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
import json
import logging
from pathlib import Path
import sys
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))


def restrict_transport(client):
    request = client.session.request

    def preview_request(method, url, **kwargs):
        target = urlsplit(url)
        allowed = {
            ("GET", "/api/v3/brokerage/market/products/BTC-USD"),
            ("GET", "/api/v3/brokerage/market/products/ETH-USD"),
            ("GET", "/api/v3/brokerage/market/product_book"),
            ("POST", "/api/v3/brokerage/orders/preview"),
        }
        if (target.scheme != "https" or target.netloc != "api.coinbase.com"
                or target.fragment or (method.upper(), target.path) not in allowed):
            raise ValueError("transport_target_refused")
        kwargs["allow_redirects"] = False
        response = request(method, url, **kwargs)
        if 300 <= response.status_code < 400:
            raise ValueError("transport_redirect_refused")
        return response

    client.session.request = preview_request


def number(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("invalid_numeric_field")
    try:
        result = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("invalid_numeric_field") from None
    if not result.is_finite() or abs(result) > Decimal("1e12") or (positive and result <= 0):
        raise ValueError("invalid_numeric_field")
    return result


def summary(response, product, style):
    if not isinstance(response, dict) or not isinstance(response.get("errs"), list):
        raise ValueError("invalid_preview_response")
    errors = response["errs"]
    row = {"product_id": product, "style": style, "side": "BUY",
           "status": "PREVIEW_ERRORS_UNVERIFIED" if errors else "PRODUCT_FEE_PREVIEW_ESTIMATE",
           "error_count": len(errors), "preview_only": True, "realized_fee_verified": False}
    for field in ("commission_total", "quote_size", "base_size", "est_average_filled_price"):
        if response.get(field) is not None:
            row[field] = str(number(response[field]))
    if not errors and "commission_total" not in row:
        raise ValueError("missing_commission")
    if "commission_total" in row:
        commission = number(row["commission_total"])
        if abs(commission) > Decimal("500") or (style == "market_taker" and commission < 0):
            raise ValueError("invalid_preview_commission")
    for field in ("quote_size", "base_size", "est_average_filled_price"):
        if field in row and not errors:
            number(row[field], positive=True)
    # Coinbase trading rules charge spot fees in the quote asset; this lookup is USD only.
    row["commission_currency"] = "USD"
    return row


def observe(loader=None, factory=None):
    if loader is None:
        from services.security.credentials_loader import load_exchange_credentials
        loader = load_exchange_credentials
    if factory is None:
        from services.security.exchange_factory import make_exchange
        factory = make_exchange
    out = {"observed_at_utc": datetime.now(timezone.utc).isoformat(), "venue": "coinbase",
           "orders_submitted": False, "preview_only": True, "raw_response_saved": False,
           "requests": [], "product_specific_realized_fees": "UNVERIFIED"}
    try:
        creds = loader("coinbase")
        if not creds.get("apiKey") or not creds.get("secret"):
            raise ValueError("existing_credentials_missing")
        client = factory("coinbase", creds, enable_rate_limit=True)
        if client.id != "coinbase" or client.urls.get("api") != {"rest": "https://api.coinbase.com"}:
            raise ValueError("unexpected_api_target")
        client.verbose = False
        client.logger = logging.Logger("coinbase_preview_observer_private_transport")
        client.logger.disabled = True
        client.logger.propagate = False
        client.timeout = 15000
        restrict_transport(client)
        for product in ("BTC-USD", "ETH-USD"):
            info = client.v3PublicGetBrokerageMarketProductsProductId({"product_id": product})
            if info.get("product_id") != product or info.get("quote_currency_id") != "USD":
                raise ValueError("product_identity_invalid")
            tick = number(info["quote_increment"], positive=True)
            book = client.v3PublicGetBrokerageMarketProductBook({"product_id": product, "limit": 1})
            if book.get("pricebook", {}).get("product_id") != product:
                raise ValueError("book_product_identity_invalid")
            bid = number(book["pricebook"]["bids"][0]["price"], positive=True)
            limit = (bid * Decimal("0.99") / tick).to_integral_value(rounding=ROUND_FLOOR) * tick
            if limit <= 0:
                raise ValueError("preview_limit_invalid")
            for style in ("market_taker", "post_only_maker"):
                config = ({"market_market_ioc": {"quote_size": "500"}} if style == "market_taker" else
                          {"limit_limit_gtc": {"quote_size": "500", "limit_price": str(limit), "post_only": True}})
                # The documented preview resource is distinct from the create-order endpoint.
                response = client.v3PrivatePostBrokerageOrdersPreview(
                    {"product_id": product, "side": "BUY", "order_configuration": config})
                out["requests"].append(summary(response, product, style))
        out["status"] = "PREVIEW_LOOKUP_COMPLETE"
    except Exception as exc:
        out["status"] = "PREVIEW_LOOKUP_INCOMPLETE"
        out["error_type"] = type(exc).__name__
    return out


def main(argv=None, observer=observe):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    with args.output.open("x") as stream:
        result = observer()
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))
    return 0 if (result.get("status") == "PREVIEW_LOOKUP_COMPLETE"
                 and len(result.get("requests", [])) == 4
                 and all(row.get("status") == "PRODUCT_FEE_PREVIEW_ESTIMATE"
                         for row in result["requests"])) else 1


if __name__ == "__main__":
    sys.exit(main())
