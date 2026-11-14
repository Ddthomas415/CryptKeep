"""Group B's data contract, without ranking or execution imports."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path

POLICY = "group_b_weekly_v1"
UNIVERSE = tuple(base + "/USD" for base in (
    "BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "ADA", "AVAX", "LINK", "DOT",
    "LTC", "MATIC", "UNI", "ATOM", "FIL", "APT", "OP", "ARB", "INJ", "SUI",
    "PEPE", "WIF", "JTO", "BONK", "PYTH",
))
FROZEN = {
    "services/signals/market_ranker.py": "d6fc1860f53a3ef7f688be047b9084ea479e63cf38cd599e996b22bb1ec0fec9",
    "services/signals/signal_library.py": "64405797a2aa1a703dcd7995476547b4d3437139ec1ded9faa71eb9ef3d3af4c",
    "services/analytics/multi_symbol_paper_campaign_generator.py": "f3b6b2384a82fc03742bbfc58a44193daf369deb663b8f0505336e9900cc3d9c",
    "config/candidate_universe.yaml": "2ae33fcbea648ee55315ebbe10cb312cb4a058aa675bce0de80aa59be9a07bd6",
}
MAX_BYTES = 4 * 1024 * 1024
PRODUCER_FILES = ("services/market_data/group_b_selection.py",
                  "services/analytics/group_b_weekly_selection.py",
                  "scripts/research/build_group_b_weekly_selection.py")


def producer_identity():
    root = Path(__file__).resolve().parents[2]
    return {name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in PRODUCER_FILES}


def instant(value):
    if not isinstance(value, str):
        raise ValueError("invalid_timestamp")
    out = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if out.tzinfo is None or out.utcoffset() != timedelta(0):
        raise ValueError("utc_timestamp_required")
    return out


def week_at(now):
    now = instant(now)
    start = now.replace(hour=0, minute=5, second=0, microsecond=0) - timedelta(days=now.weekday())
    return start if now >= start else start - timedelta(days=7)


def weekly_name(now):
    return "selection_" + week_at(now).strftime("%Y%m%dT%H%M%SZ") + ".json"


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"),
                                     allow_nan=False).encode()).hexdigest()


def finite(value, *, low=None, high=None):
    if type(value) not in (int, float) or not math.isfinite(value):
        raise ValueError("invalid_number")
    if (low is not None and value < low) or (high is not None and value > high):
        raise ValueError("number_out_of_range")
    return value


def assign_slots(picks, previous):
    if (type(previous) is not list or len(previous) != 3
            or any(x is not None and x not in UNIVERSE for x in previous)
            or len([x for x in previous if x]) != len(set(x for x in previous if x))):
        raise ValueError("invalid_previous_slots")
    slots = [x if x in picks else None for x in previous]
    new = iter(x for x in picks if x not in slots)
    return [x if x is not None else next(new, None) for x in slots]


def validate_inputs(inputs, rank_at):
    """No partial universe, ticker default-to-zero, or invented candles."""
    cutoff = instant(rank_at).replace(minute=0, second=0, microsecond=0)
    if type(inputs) is not list or [x.get("symbol") for x in inputs] != list(UNIVERSE):
        raise ValueError("complete_ordered_universe_required")
    rows = []
    for item in inputs:
        if type(item) is not dict or not isinstance(item.get("metadata_sha256"), str) or len(item["metadata_sha256"]) != 64:
            raise ValueError("market_metadata_evidence_required")
        if not cutoff <= instant(item["observed_at"]) <= instant(rank_at):
            raise ValueError("input_outside_ranking_window")
        if item.get("product_id") is None:
            if item.get("exclusion") != "no_coinbase_usd_pair" or "ohlcv" in item:
                raise ValueError("invalid_pair_exclusion")
            continue
        if item.get("product_id") != item["symbol"].replace("/", "-") or item.get("exclusion") is not None:
            raise ValueError("product_identity_mismatch")
        finite(item["symbol_return_pct"])
        candles = item["ohlcv"]
        if type(candles) is not list or len(candles) != 200:
            raise ValueError("completed_200_required")
        for i, bar in enumerate(candles):
            expected = int((cutoff - timedelta(hours=200 - i)).timestamp() * 1000)
            if type(bar) is not list or len(bar) != 6 or type(bar[0]) is not int or bar[0] != expected:
                raise ValueError("completed_hour_sequence_required")
            o, h, l, c = [finite(x, low=1e-300) for x in bar[1:5]]
            finite(bar[5], low=0)
            if l > min(o, c) or h < max(o, c) or l > h:
                raise ValueError("invalid_ohlc")
        rows.append({"symbol": item["symbol"], "ohlcv": candles,
                     "symbol_return_pct": item["symbol_return_pct"]})
    return rows


def validate_selection(artifact, *, now):
    """Validate the published evidence, not whether its ranking predicts profit."""
    if type(artifact) is not dict:
        raise ValueError("invalid_selection")
    body = {k: v for k, v in artifact.items() if k != "sha256"}
    if artifact.get("sha256") != digest(body):
        raise ValueError("selection_hash_mismatch")
    start = week_at(now)
    if (artifact.get("policy") != POLICY or artifact.get("venue") != "coinbase"
            or artifact.get("code") != FROZEN or artifact.get("producer_code") != producer_identity()
            or instant(artifact["rank_at"]) != start
            or not start <= instant(artifact["generated_at"]) <= instant(now)
            or instant(artifact["valid_until"]) != start + timedelta(days=7)):
        raise ValueError("selection_identity_or_week")
    rows = validate_inputs(artifact["inputs"], artifact["rank_at"])
    ranked = artifact["ranked"]
    if type(ranked) is not list or len(ranked) != len(rows):
        raise ValueError("incomplete_ranking")
    expected = {x["symbol"] for x in rows}
    if set(x["symbol"] for x in ranked) != expected or len(expected) != len(ranked):
        raise ValueError("ranking_identity")
    for row in ranked:
        finite(row["composite_score"], low=0, high=100)
        if type(row.get("scores")) is not dict or not row["scores"]:
            raise ValueError("scores_required")
        for score in row["scores"].values():
            finite(score)
        finite(row["symbol_return_pct"])
    if ranked != sorted(ranked, key=lambda x: (-x["composite_score"], UNIVERSE.index(x["symbol"]))):
        raise ValueError("ranking_order")
    picks = [x["symbol"] for x in ranked if x["composite_score"] >= 38][:3]
    if artifact["slots"] != assign_slots(picks, artifact["previous_slots"]):
        raise ValueError("slot_assignment")
    return artifact
