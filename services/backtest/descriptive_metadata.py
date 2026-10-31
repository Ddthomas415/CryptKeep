"""Pure public-metadata rules for ED-002; no fetching or account authority."""
import hashlib
import json

from services.backtest import shared_cash_research as ledger


HOUR = 3_600_000
POLICY = "ed002-descriptive-receipt-one-hour-v1"
FLAGS = ("trading_disabled", "cancel_only", "limit_only", "post_only", "auction_mode")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate_json_key")
        result[key] = value
    return result


def _reject_constant(value):
    raise ValueError("nonfinite_json_constant")


def _identity(expected):
    if not isinstance(expected, dict):
        return False
    fields = ("product_id", "base_currency", "quote_currency", "identity_evidence_sha256")
    if any(not isinstance(expected.get(k), str) or not expected[k] for k in fields):
        return False
    evidence = expected["identity_evidence_sha256"]
    return (expected["quote_currency"] == "USD" and len(evidence) == 64
            and all(c in "0123456789abcdef" for c in evidence))


def map_public_metadata(snapshots, *, identities):
    """Map supplied raw Exchange product responses, without opening any source.

    snapshots: [{received_at_ms: int, products_bytes: bytes}].
    identities: {study_symbol: {product_id, base_currency, quote_currency,
                              identity_evidence_sha256}}, or None if unresolved.
    Identity references bind caller evidence, not independently authenticate it.
    Unknown rows intentionally shadow older eligible rows in ledger.rule_at.
    """
    if (not isinstance(identities, dict) or not identities
            or any(not isinstance(s, str) or not s for s in identities)
            or not isinstance(snapshots, (list, tuple)) or not snapshots):
        raise ValueError("explicit_identity_universe_and_snapshots_required")
    try:
        identity_bytes = json.dumps(identities, sort_keys=True, allow_nan=False).encode()
    except (TypeError, ValueError):
        raise ValueError("invalid_identity_mapping") from None
    valid_ids = [r["product_id"] for r in identities.values() if _identity(r)]
    if len(valid_ids) != len(set(valid_ids)):
        raise ValueError("duplicate_product_assignment")
    receipts = []
    for snapshot in snapshots:
        if not isinstance(snapshot, dict) or not isinstance(snapshot.get("products_bytes"), bytes):
            raise ValueError("raw_product_bytes_required")
        receipts.append(ledger.timestamp(snapshot.get("received_at_ms")))
    if len(receipts) != len(set(receipts)):
        raise ValueError("ambiguous_receipt_timestamp")

    rules, observations = {s: [] for s in sorted(identities)}, []
    for snapshot in sorted(snapshots, key=lambda r: r["received_at_ms"]):
        received, raw = snapshot["received_at_ms"], snapshot["products_bytes"]
        source_hash = hashlib.sha256(raw).hexdigest()
        try:
            products = json.loads(raw, object_pairs_hook=_unique_object,
                                  parse_constant=_reject_constant)
            if not isinstance(products, list) or not all(isinstance(p, dict) for p in products):
                raise ValueError("invalid_products_schema")
        except (ValueError, UnicodeError):
            products = None
        for symbol, expected in sorted(identities.items()):
            # An invalid newer observation must not fall back to old permission.
            row = {"known_at_ms": received, "valid_from_ms": received,
                   "valid_until_ms": received + HOUR, "venue": "coinbase", "quote": "USD",
                   "eligible": None, "metadata_policy": POLICY, "source_sha256": source_hash}
            flags, reason = {}, None
            if not _identity(expected):
                reason = "unresolved_identity_evidence"
            elif products is None:
                reason = "unreadable_products_capture"
            else:
                matches = [p for p in products if p.get("id") == expected["product_id"]]
                if len(matches) != 1:
                    reason = "missing_or_duplicate_product"
                else:
                    product = matches[0]
                    if any(product.get(k) != expected[k] for k in ("base_currency", "quote_currency")):
                        reason = "product_identity_mismatch"
                    elif (not isinstance(product.get("status"), str) or not product["status"]
                          or any(type(product.get(k)) is not bool for k in FLAGS)):
                        reason = "unknown_status_or_flags"
                    elif "view_only" in product and type(product["view_only"]) is not bool:
                        reason = "unknown_view_only_flag"
                    else:
                        flags = {k: product[k] for k in FLAGS}
                        if "view_only" in product:
                            flags["view_only"] = product["view_only"]
                        try:
                            lot = ledger.number(product.get("base_increment"), positive=True)
                        except ValueError:
                            reason = "unknown_base_increment"
                        else:
                            row.update({"eligible": product["status"] == "online" and not any(flags.values()),
                                        "lot_step": lot, "quote_step": ledger.number("0.01"),
                                        "minimum_qty": ledger.ZERO, "minimum_notional_gross": ledger.ZERO})
                            reason = "eligible_under_model" if row["eligible"] else "known_ineligible"
            row["metadata_reason"] = reason
            rules[symbol].append(row)
            observations.append({"symbol": symbol, "received_at_ms": received,
                "product_id": expected.get("product_id") if isinstance(expected, dict) else None,
                "source_sha256": source_hash, "status": "INCOMPLETE" if row["eligible"] is None else "COMPLETE",
                "reason": reason, "eligible": row["eligible"], "observed_flags": flags})
    return {"policy": POLICY, "qualification": "PUBLIC_METADATA_MODEL_NOT_ACCOUNT_PERMISSION",
            "identity_mapping_sha256": hashlib.sha256(identity_bytes).hexdigest(),
            "identity_authenticity_verified": False, "rules": rules, "observations": observations}
