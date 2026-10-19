"""ED-001 WP3 / A3: registry integrity checks (structure only, no market-data calculations) and synthetic-fixture tests
of the point-in-time helpers in scripts/research/market_universe.py."""
import csv
import datetime as dt
import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("market_universe", ROOT / "scripts/research/market_universe.py")
mu = importlib.util.module_from_spec(spec); spec.loader.exec_module(mu)
COLUMNS = ["canonical_asset_id", "raw_ticker", "venue", "market", "quote", "first_observed_candle", "last_observed_candle",
           "verified_first_tradable_date", "eligibility_basis", "daily_rows", "internal_gaps", "largest_gap_days",
           "status_at_fetch", "status_evidence", "asset_type_flag", "identity_status", "identity_evidence",
           "identity_confidence", "settlement_status", "settlement_evidence", "notes"]


def fx(**kw):
    base = {"canonical_asset_id": "UNRESOLVED:x:A-USD", "raw_ticker": "A", "venue": "x", "market": "A-USD", "quote": "USD",
            "first_observed_candle": "2020-01-01", "last_observed_candle": "2021-01-01", "verified_first_tradable_date": "",
            "asset_type_flag": "", "identity_status": "UNRESOLVED", "settlement_status": "NOT_APPLICABLE"}
    base.update(kw); return base


# --- registry structure (reads the file; no prices, no strategy calculations) ---
def registry():
    return mu.load()


def test_registry_columns_exact():
    with open(mu.REGISTRY, newline="") as f:
        assert next(csv.reader(f)) == COLUMNS


def test_registry_enumerations():
    for r in registry():
        assert r["status_at_fetch"] in mu.STATUSES, r["market"]
        assert r["settlement_status"] in mu.SETTLEMENT_STATUSES, r["market"]
        assert r["identity_status"] in mu.IDENTITY_STATUSES, r["market"]
        assert r["venue"] in {"coinbase", "binance"}, r["market"]


def test_registry_markets_unique():
    keys = [(r["venue"], r["market"]) for r in registry()]
    assert len(keys) == len(set(keys))


def test_registry_every_stopped_market_has_explicit_settlement_status():
    for r in registry():
        if r["status_at_fetch"] in mu.STOPPED:
            assert r["settlement_status"] in {"UNKNOWN", "EVIDENCED"}, r["market"]
            assert r["settlement_evidence"].strip(), r["market"]


def test_registry_no_unverified_identity_marked_resolved():
    for r in registry():
        if r["identity_status"] == "RESOLVED":
            assert r["identity_evidence"].strip() and not r["canonical_asset_id"].startswith("UNRESOLVED:"), r["market"]
        else:
            assert r["canonical_asset_id"] == f"UNRESOLVED:{r['venue']}:{r['market']}", r["market"]


def test_registry_eligibility_basis_matches_fields():
    for r in registry():
        assert r["eligibility_basis"] == mu.eligibility_start(r)[1], r["market"]


# --- synthetic fixtures ---
def test_not_eligible_before_start_plus_history():
    r = fx()
    assert not mu.eligible(r, dt.date(2020, 3, 30))
    assert mu.eligible(r, dt.date(2020, 3, 31))


def test_verified_tradable_date_overrides_first_observed_candle():
    r = fx(verified_first_tradable_date="2020-06-01")
    assert mu.eligibility_start(r) == (dt.date(2020, 6, 1), "verified_first_tradable_date")
    assert not mu.eligible(r, dt.date(2020, 8, 29))
    assert mu.eligible(r, dt.date(2020, 8, 30))


def test_not_eligible_after_last_observed_candle():
    r = fx()
    assert mu.eligible(r, dt.date(2021, 1, 4))
    assert not mu.eligible(r, dt.date(2021, 1, 5))


def test_stable_or_wrapped_never_eligible():
    assert not mu.eligible(fx(asset_type_flag="stable_or_wrapped"), dt.date(2020, 6, 1))


def test_same_ticker_unresolved_markets_never_merge():
    a = fx(venue="coinbase", market="ONE-USD", raw_ticker="ONE", canonical_asset_id="UNRESOLVED:coinbase:ONE-USD")
    b = fx(venue="binance", market="ONEUSDT", raw_ticker="ONE", canonical_asset_id="UNRESOLVED:binance:ONEUSDT")
    assert mu.asset_key(a) != mu.asset_key(b)


def test_resolved_identity_groups_and_unresolved_label_cannot_spoof():
    a = fx(venue="coinbase", market="POL-USD", identity_status="RESOLVED", canonical_asset_id="polygon-ecosystem-token")
    b = fx(venue="binance", market="POLUSDT", identity_status="RESOLVED", canonical_asset_id="polygon-ecosystem-token")
    c = fx(venue="binance", market="MATICUSDT", identity_status="UNRESOLVED", canonical_asset_id="polygon-ecosystem-token")
    assert mu.asset_key(a) == mu.asset_key(b)
    assert mu.asset_key(c) != mu.asset_key(a)


def test_unknown_settlement_returns_both_sensitivities():
    assert mu.settlement_values(fx(settlement_status="UNKNOWN"), 2.0) == (1.0, 0.0)


def test_evidenced_settlement_uses_evidence():
    assert mu.settlement_values(fx(settlement_status="EVIDENCED", settlement_value="0.37"), 2.0) == (0.37,)


def test_no_settlement_for_trading_market():
    with pytest.raises(ValueError):
        mu.settlement_values(fx(), 2.0)
