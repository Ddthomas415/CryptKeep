"""One read-only fee observation; never log credentials or account totals."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import json
import logging
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def rate(value, *, maker=False):
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        raise ValueError("invalid_fee_rate")
    try:
        parsed = Decimal(str(value))
    except InvalidOperation:
        raise ValueError("invalid_fee_rate") from None
    if not parsed.is_finite() or not (Decimal(-1) if maker else Decimal(0)) <= parsed < 1:
        raise ValueError("invalid_fee_rate")
    return float(parsed*10000)


def summarize(response):
    if not isinstance(response, dict) or not isinstance(response.get("fee_tier"), dict):
        raise ValueError("missing_fee_tier")
    tier = response["fee_tier"]
    # Do not use fetch_trading_fees: installed CCXT 4.5.48 swaps these names.
    return {"status": "OBSERVED_ACCOUNT_SPOT_FEE_TIER",
            "maker_bps": rate(tier.get("maker_fee_rate"), maker=True),
            "taker_bps": rate(tier.get("taker_fee_rate")),
            "has_promo_fee": response.get("has_promo_fee") if isinstance(response.get("has_promo_fee"), bool) else None,
            "has_cost_plus_commission": response.get("has_cost_plus_commission") if isinstance(response.get("has_cost_plus_commission"), bool) else None,
            "product_specific_all_in_fees": "UNVERIFIED",
            "historical_fee_tier": "UNVERIFIED",
            "raw_response_saved": False}


def observe(loader=None, factory=None):
    if loader is None:
        from services.security.credentials_loader import load_exchange_credentials
        loader = load_exchange_credentials
    if factory is None:
        from services.security.exchange_factory import make_exchange
        factory = make_exchange
    result = {"venue": "coinbase", "product_type": "SPOT", "research_only": True,
              "observed_at_utc": datetime.now(timezone.utc).isoformat(),
              "private_request_attempted": False, "orders_submitted": False}
    try:
        creds = loader("coinbase")
        result["credential_source"] = str(creds.get("source") or "unknown")
        if not creds.get("apiKey") or not creds.get("secret"):
            result["status"] = "MISSING_EXISTING_CREDENTIALS"
            return result
        client = factory("coinbase", creds, enable_rate_limit=True)
        if client.id != "coinbase" or client.urls.get("api") != {"rest": "https://api.coinbase.com"}:
            raise ValueError("unexpected_api_target")
        client.verbose = False
        # CCXT logger.debug is independent of verbose; use an isolated logger.
        client.logger = logging.Logger("coinbase_fee_observer_private_transport")
        client.logger.disabled = True
        client.logger.propagate = False
        client.timeout = 15000
        result["private_request_attempted"] = True
        result.update(summarize(client.v3PrivateGetBrokerageTransactionSummary({"product_type": "SPOT"})))
    except Exception as exc:
        # Exception text can contain response bodies or request details.
        result["status"] = "OBSERVATION_FAILED"
        result["error_type"] = type(exc).__name__
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Reserve output before any private request; no overwrite or duplicate retry.
    with args.output.open("x") as stream:
        result = observe()
        json.dump(result, stream, indent=2, allow_nan=False)
    print(json.dumps(result))


if __name__ == "__main__":
    main()
