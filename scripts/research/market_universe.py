"""Point-in-time market universe helpers over research/market_universe.csv (Coinbase + Binance; ED-001 WP3, 2026-10-16).

Conservative by design (A3 conditions):
- Exchange markets are never merged into assets by ticker. canonical_asset_id stays "UNRESOLVED:<venue>:<market>"
  until identity evidence is recorded; asset_key() groups only RESOLVED ids.
- Eligibility starts at verified_first_tradable_date when recorded; otherwise at first_observed_candle, which is
  archive evidence only and is reported as such (eligibility_basis).
- A stopped or delisted market with settlement_status UNKNOWN has no single settlement value: callers get the
  mandatory sensitivity set (50% and 0% of the last credible value) and must evaluate both.
No liquidity or cost screen is applied here; experiments fix their own. Limits: see
~/Documents/cryptkeep_data_archive/wp3_universe_20261016/README.md.
"""
import csv
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "research/market_universe.csv"
STATUSES = {"trading_at_fetch", "stopped_before_fetch", "delisted_listed_in_api", "no_data"}
STOPPED = {"stopped_before_fetch", "delisted_listed_in_api"}
SETTLEMENT_STATUSES = {"NOT_APPLICABLE", "UNKNOWN", "EVIDENCED"}
IDENTITY_STATUSES = {"UNRESOLVED", "RESOLVED"}
UNKNOWN_RECOVERY_SENSITIVITIES = (0.5, 0.0)


def load(path=REGISTRY):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def eligibility_start(row):
    """(date, basis): the verified first tradable date if recorded, else the first observed candle (archive evidence)."""
    if row.get("verified_first_tradable_date"):
        return dt.date.fromisoformat(row["verified_first_tradable_date"]), "verified_first_tradable_date"
    if row.get("first_observed_candle"):
        return dt.date.fromisoformat(row["first_observed_candle"]), "first_observed_candle_only"
    return None, "no_data"


def eligible(row, day, min_history_days=90, last_candle_tolerance_days=3):
    """True only if the market's eligibility start is at least min_history_days before `day`, it is not a
    stable/wrapped asset, and its last observed candle is not before `day` minus the tolerance."""
    start, _ = eligibility_start(row)
    if start is None or row.get("asset_type_flag"):
        return False
    last = dt.date.fromisoformat(row["last_observed_candle"])
    return start <= day - dt.timedelta(days=min_history_days) and last >= day - dt.timedelta(days=last_candle_tolerance_days)


def asset_key(row):
    """Grouping key for 'same asset'. Unresolved identities are unique per exchange market, so markets that merely
    share a ticker are never combined."""
    if row.get("identity_status") == "RESOLVED" and row.get("canonical_asset_id") and not row["canonical_asset_id"].startswith("UNRESOLVED:"):
        return row["canonical_asset_id"]
    return f"UNRESOLVED:{row['venue']}:{row['market']}"


def settlement_values(row, last_credible_value):
    """Settlement value(s) a simulation must evaluate for a stopped market.
    EVIDENCED -> the evidenced value; UNKNOWN -> the mandatory sensitivity set; never an assumed zero or last close alone."""
    status = row.get("settlement_status")
    if status == "EVIDENCED":
        return (float(row["settlement_value"]),)
    if status == "UNKNOWN":
        return tuple(k * last_credible_value for k in UNKNOWN_RECOVERY_SENSITIVITIES)
    raise ValueError(f"no settlement applies to status {status!r} for {row.get('market')}")
