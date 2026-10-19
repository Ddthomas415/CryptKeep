"""Conservative daily sampled cohort adapter; no return scoring."""
from scripts.research.cmc_cohort_coverage import classify_appearance
import json


def build_cohorts(envelopes):
    """Consume validated envelopes, union daily presence, retain first observation.

    A malformed list rejects the envelope; it cannot prove an absent day.
    Later captures never retroactively upgrade the first observation's identity.
    """
    daily, first, excluded, context, ambiguous = {}, {}, [], [], set()
    collection_start = None
    for evidence in sorted(envelopes, key=lambda item: (item["snapshot_utc"], item["file"])):
        data = evidence["data"]
        rows = data["trending_hidden_boost"]
        if data.get("trending_status") != "OBSERVED" or data.get("source_errors") or not rows:
            excluded.append({"file": evidence["file"], "reason": "unusable list observation"})
            continue
        if any(not isinstance(row, dict) or row.get("type") not in ("listing", "dex") for row in rows):
            excluded.append({"file": evidence["file"], "reason": "invalid list row type"})
            continue
        context.append({"file": evidence["file"],
                        "dex_rows_outside_listed_event_scope": sum(row["type"] == "dex" for row in rows)})
        rows = [row for row in rows if row["type"] == "listing"]
        if not rows:
            excluded.append({"file": evidence["file"], "reason": "no listed observations"})
            continue
        ids = []
        for row in rows:
            value = row.get("cmc_id") if isinstance(row, dict) else None
            text = str(value)
            if (isinstance(value, bool) or not text.isascii()
                    or not text.isdecimal() or int(text) <= 0):
                break
            ids.append(str(int(text)))
        if len(ids) != len(rows) or len(set(ids)) != len(ids):
            excluded.append({"file": evidence["file"], "reason": "malformed or duplicate CMC IDs"})
            continue
        day = evidence["snapshot_utc"].date()
        if collection_start is None:
            collection_start = evidence["snapshot_utc"]
        daily.setdefault(day, set()).update(ids)
        for coin, row in zip(ids, rows):
            key = (day, coin)
            if key in first:
                previous, previous_row = first[key]
                if previous["snapshot_utc"] == evidence["snapshot_utc"]:
                    before = {"row": previous_row, "btc": previous["data"].get("majors_coinbase", {}).get("BTC")}
                    after = {"row": row, "btc": data.get("majors_coinbase", {}).get("BTC")}
                    if json.dumps(before, sort_keys=True) != json.dumps(after, sort_keys=True):
                        ambiguous.add(key)
            else:
                first[key] = (evidence, row)
    events = []
    for (day, coin), (evidence, row) in sorted(first.items()):
        cohort = classify_appearance(day, coin, daily)
        events.append({"utc_day": day.isoformat(), "cmc_id": coin,
                       "cohort_status": "AMBIGUOUS_FIRST_CAPTURE" if (day, coin) in ambiguous else cohort["status"],
                       "missing_days": [value.isoformat() for value in cohort["missing_days"]],
                       "first_snapshot_file": evidence["file"],
                       "first_snapshot_sha256": evidence["sha256"],
                       "identity_eligible_at_first_observation": row.get("identity_eligible") is True,
                       "scoring_authorized": False})
    return {"events": events, "excluded_lists": excluded, "excluded_context": context,
            "qualified_collection_start_utc": collection_start,
            "observed_utc_days": [day.isoformat() for day in sorted(daily)],
            "scope": "daily_presence_union_not_continuous_absence_or_profit"}
