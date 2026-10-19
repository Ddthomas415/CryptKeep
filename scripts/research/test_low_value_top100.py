"""Frozen CMC-reference cohort screen; not exchange execution or a live strategy."""

import argparse
import hashlib
import json
import math
import random
import statistics
import tarfile
from datetime import date, datetime, timezone
from pathlib import Path


ARMS = ("under_1", "ranks_51_100", "new_entrants", "altcoin_control")
EXCLUDED_IDS = {1, 1027}
EXCLUDED_TAGS = {
    "stablecoin", "asset-backed-stablecoin", "fiat-stablecoin",
    "algorithmic-stablecoin", "usd-stablecoin", "eur-stablecoin",
    "wrapped-tokens", "tokenized-gold", "tokenized-stock", "tokenized-assets",
    "tokenized-commodities", "liquid-staking-derivatives", "bridged-tokens",
    "xstocks-ecosystem",
}
ARCHIVE_HASH = "05223937afcfb02f4c020476c8b3380fcdd7044e5f3812e4938aff858fd41f4b"
PROTOCOL_HASH = "f232050036723229ae9a0fbbc505d1a3df2f0318cd2b13dc12eb92955b1ebf01"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def finite(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        return None
    return float(value) if math.isfinite(value) else None


def price(row):
    value = finite(row[4]) if row is not None else None
    return value if value is not None and value > 0 else None


def eligible(row):
    cap, volume, change = finite(row[6]), finite(row[5]), finite(row[7])
    p = price(row)
    return (
        row[0] not in EXCLUDED_IDS and 1 <= row[3] <= 100 and p is not None
        and cap is not None and cap > 0 and volume is not None and volume >= 1e6
        and not EXCLUDED_TAGS.intersection(row[9])
        and not (0.97 <= p <= 1.03 and change is not None and abs(change) < 1)
    )


def choose(snapshots, index):
    selected = {arm: [] for arm in ARMS}
    for identity, row in sorted(snapshots[index].items()):
        if not eligible(row):
            continue
        selected["altcoin_control"].append(identity)
        if row[4] < 1:
            selected["under_1"].append(identity)
        if 51 <= row[3] <= 100:
            selected["ranks_51_100"].append(identity)
        if index >= 4 and all(
            identity in snapshots[j] and snapshots[j][identity][3] > 100
            for j in range(index - 4, index)
        ):
            selected["new_entrants"].append(identity)
    return selected


def terminal_multiple(entry, exit_price, fee, adverse):
    # One dollar includes entry fee; adverse adjustments are assumptions.
    return exit_price * (1 - adverse) * (1 - fee) / (entry * (1 + adverse) * (1 + fee))


def cycle(identities, selection, entry, exit_snapshot):
    if not identities:
        return {"selected": 0, "funded": 0, "missing_entries": 0,
                "unresolved_exits": 0, "gross_dollars": 0.0,
                "net_dollars_lower": 0.0, "stress_dollars_lower": 0.0,
                "members": []}
    allocation = 1000 / len(identities)
    gross = net = stress = 0.0
    members = []
    for identity in identities:
        row = selection[identity]
        ep, xp = price(entry.get(identity)), price(exit_snapshot.get(identity))
        member = {"id": identity, "symbol": row[1], "slug": row[2],
                  "selection_rank": row[3], "selection_price": row[4],
                  "selection_cap_usd": row[6], "selection_volume24h_usd": row[5],
                  "allocation": allocation, "entry": ep, "exit": xp}
        if ep is None:
            member.update(status="CASH_MISSING_ENTRY", gross_dollars=0.0,
                          net_dollars_lower=0.0, stress_dollars_lower=0.0)
        elif xp is None:
            member.update(status="UNKNOWN_EXIT_ZERO_RECOVERY_BOUND",
                          gross_dollars=-allocation, net_dollars_lower=-allocation,
                          stress_dollars_lower=-allocation)
        else:
            member.update(
                status="MODELLED",
                gross_dollars=allocation * (xp / ep - 1),
                net_dollars_lower=allocation * (terminal_multiple(ep, xp, .005, .0025) - 1),
                stress_dollars_lower=allocation * (terminal_multiple(ep, xp, .012, .0025) - 1),
            )
        gross += member["gross_dollars"]
        net += member["net_dollars_lower"]
        stress += member["stress_dollars_lower"]
        members.append(member)
    return {
        "selected": len(identities), "funded": sum(m["entry"] is not None for m in members),
        "missing_entries": sum(m["entry"] is None for m in members),
        "unresolved_exits": sum(m["entry"] is not None and m["exit"] is None for m in members),
        "gross_dollars": gross, "net_dollars_lower": net,
        "stress_dollars_lower": stress, "members": members,
    }


def load(archive, manifest):
    if digest(archive) != ARCHIVE_HASH:
        raise ValueError("Frozen archive checksum mismatch")
    expected = {line.split(maxsplit=1)[1].strip(): line.split()[0]
                for line in Path(manifest).read_text().splitlines() if line.strip()}
    data, hashes = {}, {}
    with tarfile.open(archive, "r:xz") as tar:
        for item in tar:
            if not item.name.startswith("cmc/weekly/") or not item.name.endswith(".json"):
                continue
            if not item.isfile() or item.name in hashes:
                raise ValueError("Non-regular or duplicated weekly member")
            raw = tar.extractfile(item).read()
            hashes[item.name] = hashlib.sha256(raw).hexdigest()
            if expected.get(item.name) != hashes[item.name]:
                raise ValueError(f"Input hash mismatch: {item.name}")
            day = date.fromisoformat(Path(item.name).stem)
            rows = json.loads(raw)
            snapshot = {}
            for row in rows:
                if (not isinstance(row, list) or len(row) != 10
                        or type(row[0]) is not int or row[0] <= 0
                        or type(row[3]) is not int or row[3] <= 0
                        or not isinstance(row[1], str) or not isinstance(row[2], str)
                        or not isinstance(row[9], list)
                        or not all(isinstance(t, str) for t in row[9])
                        or row[0] in snapshot):
                    raise ValueError(f"Invalid or duplicate row in {item.name}")
                snapshot[row[0]] = row
            if set(range(1, 101)) != {r[3] for r in rows if r[3] <= 100}:
                raise ValueError(f"Top-100 rank coverage incomplete: {item.name}")
            if day in data:
                raise ValueError("Repeated snapshot date")
            data[day] = snapshot
    dates = sorted(data)
    if len(dates) < 10 or any((b - a).days != 7 for a, b in zip(dates, dates[1:])):
        raise ValueError("Weekly archive continuity incomplete")
    expected_weekly = {p for p in expected if p.startswith("cmc/weekly/")}
    if set(hashes) != expected_weekly:
        raise ValueError("Weekly archive member set differs from frozen manifest")
    return dates, [data[d] for d in dates], hashes


def quantile(values, q):
    values = sorted(values)
    position = (len(values) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    return values[low] + (position - low) * (values[high] - values[low])


def interval(series):
    # Retain calendar adjacency; None cycles are not squeezed out of time.
    observed = [x for x in series if x is not None]
    if len(observed) < 12:
        return {"paired_cycles": len(observed), "mean_dollars": statistics.mean(observed) if observed else None,
                "interval_status": "INSUFFICIENT_CYCLES"}
    rng = random.Random(20261018)
    samples = []
    for _ in range(4000):
        draw = []
        while len(draw) < len(series):
            start = rng.randrange(len(series) - 3)
            draw.extend(series[start:start + 4])
        usable = [v for v in draw[:len(series)] if v is not None]
        if usable:
            samples.append(statistics.mean(usable))
    return {
        "paired_cycles": len(observed), "mean_dollars": statistics.mean(observed),
        "ci95": [quantile(samples, .025), quantile(samples, .975)],
        "simultaneous_ci": [quantile(samples, .05 / 6), quantile(samples, 1 - .05 / 6)],
        "interval_status": "EXPLORATORY_CONDITIONAL_ON_RESOLVED_PAIRS",
    }


def describe(cycles):
    if not cycles:
        return {"cycles": 0, "point_status": "NO_CYCLES"}
    values = [c["net_dollars_lower"] for c in cycles]
    complete = [c for c in cycles if c["unresolved_exits"] == 0]
    nonempty = [c for c in cycles if c["funded"] > 0]
    return {
        "cycles": len(cycles), "funded_cycles": len(nonempty), "fully_valued_cycles": len(complete),
        "selections": sum(c["selected"] for c in cycles),
        "distinct_ids": len({m["id"] for c in cycles for m in c["members"]}),
        "funded_selections": sum(c["funded"] for c in cycles),
        "missing_entries": sum(c["missing_entries"] for c in cycles),
        "unresolved_exits": sum(c["unresolved_exits"] for c in cycles),
        "mean_net_dollars_lower": statistics.mean(values),
        "median_net_dollars_lower": statistics.median(values),
        "mean_gross_dollars_lower": statistics.mean(c["gross_dollars"] for c in cycles),
        "mean_stress_dollars_lower": statistics.mean(c["stress_dollars_lower"] for c in cycles),
        "profitable_cycles_lower": sum(v > 0 for v in values),
        "worst_cycle_dollars_lower": min(values),
        "complete_only_mean_net_dollars": statistics.mean(c["net_dollars_lower"] for c in complete) if complete else None,
        "mean_net_interval": interval([c["net_dollars_lower"] if not c["unresolved_exits"] else None for c in cycles]),
        "point_status": "LOWER_BOUND_NOT_POINT_ESTIMATE" if len(complete) != len(cycles) else "MODELLED_POINT_ESTIMATE",
    }


def run(dates, snapshots):
    first = next(i for i, d in enumerate(dates) if d >= date(2019, 1, 1))
    cycles = {arm: [] for arm in ARMS}
    for index in range(max(4, first), len(dates) - 5, 4):
        choices = choose(snapshots, index)
        for arm in ARMS:
            result = cycle(choices[arm], snapshots[index], snapshots[index + 1], snapshots[index + 5])
            result.update(selection_date=dates[index].isoformat(), entry_date=dates[index + 1].isoformat(),
                          exit_date=dates[index + 5].isoformat())
            cycles[arm].append(result)
    summary = {}
    for arm in ARMS:
        full = describe(cycles[arm])
        full["segments"] = {
            label: describe([c for c in cycles[arm] if (c["entry_date"] < "2023") == early])
            for label, early in (("2019_2022", True), ("2023_onward", False))
        }
        if arm != "altcoin_control":
            paired = [
                a["net_dollars_lower"] - b["net_dollars_lower"]
                if a["unresolved_exits"] == b["unresolved_exits"] == 0 else None
                for a, b in zip(cycles[arm], cycles["altcoin_control"])
            ]
            full["paired_vs_control"] = interval(paired)
            full["paired_vs_control"]["excluded_cycles"] = sum(v is None for v in paired)
        summary[arm] = full
    return {"summary": summary, "cycles": cycles,
            "trial_accounting": {"hypotheses": 3, "horizons": 1,
                                 "asset_union": sorted({m["id"] for arm in cycles.values() for c in arm for m in c["members"]}),
                                 "selection_exposures_are_not_independent_trials": True,
                                 "entire_project_effective_trial_count": "UNRESOLVED"}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--input-manifest", type=Path, required=True)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if digest(args.protocol) != PROTOCOL_HASH:
        raise ValueError("Frozen protocol changed")
    dates, snapshots, hashes = load(args.archive, args.input_manifest)
    result = run(dates, snapshots)
    result["provenance"] = {
        "evidence": "MODELLED_EXPLORATORY_CMC_REFERENCE_PRICES",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": digest(__file__), "protocol_sha256": digest(args.protocol),
        "archive_sha256": digest(args.archive), "manifest_sha256": digest(args.input_manifest),
        "weekly_member_sha256": hashes, "snapshots": len(dates),
        "first_snapshot": dates[0].isoformat(), "last_snapshot": dates[-1].isoformat(),
        "cash_per_independent_cycle": 1000, "fee_per_side": .005, "adverse_per_side": .0025,
        "stress_fee_per_side": .012,
    }
    with args.output.open("x") as target:
        json.dump(result, target, indent=2, allow_nan=False)
        target.write("\n")
    print(json.dumps({"summary": result["summary"], "provenance": {
        k: v for k, v in result["provenance"].items() if k != "weekly_member_sha256"
    }}, indent=2))


if __name__ == "__main__":
    main()
