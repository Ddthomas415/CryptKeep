"""Read-only timestamp/hash audit. No extraction, signals, returns or network."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import signal
import tarfile
import time

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
ARCHIVES = ROOT / "docs/research/raw_archives_20261009"
SNAPSHOT = ROOT / "research/coinbase_metadata_20261027/20261027T211732_235339Z_01ee9d4c/comparison.json"
HOUR = 3600


def sha(path):
    result = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def epoch(text):
    return int(datetime.fromisoformat(text).replace(tzinfo=timezone.utc).timestamp())


def iso(ts):
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def runs(times):
    result = []
    for ts in sorted(times):
        if result and ts == result[-1][1]:
            result[-1][1] += HOUR
        else:
            result.append([ts, ts + HOUR])
    return [{"start_utc": iso(a), "end_exclusive_utc": iso(b), "hours": (b-a)//HOUR}
            for a, b in result]


def summarize(rows, start, end):
    if not isinstance(rows, list):
        raise ValueError("expected_candle_list")
    malformed = sum(not isinstance(r, list) or len(r) != 6 for r in rows)
    ts = [r[0] for r in rows if isinstance(r, list) and len(r) == 6]
    invalid = sum(type(t) is not int or t % HOUR != 0 for t in ts)
    valid = [t for t in ts if type(t) is int and t % HOUR == 0]
    within = {t for t in valid if start <= t < end}
    expected = set(range(start, end, HOUR))
    internal = set(range(min(within), max(within)+HOUR, HOUR)) - within if within else set()
    result = {"rows": len(rows), "malformed_rows": malformed, "invalid_timestamps": invalid,
        "duplicate_timestamps": len(valid)-len(set(valid)),
        "strictly_ascending": all(a < b for a, b in zip(valid, valid[1:])),
        "outside_declared_window": sum(not start <= t < end for t in valid),
        "expected_hours": len(expected), "observed_unique_hours": len(within),
        "first_open_utc": iso(min(within)) if within else None,
        "last_open_utc": iso(max(within)) if within else None,
        "leading_unobserved_hours": (min(within)-start)//HOUR if within else None,
        "trailing_unobserved_hours": (end-HOUR-max(within))//HOUR if within else None,
        "internal_missing_hours": len(internal), "internal_missing_runs": runs(internal),
        "total_missing_hours": len(expected-within), "empty": not rows,
        "final_300_hours_complete": set(range(end-300*HOUR,end,HOUR)) <= within,
        "per_candle_availability_in_schema": False}
    result["full_declared_window_complete"] = not (expected-within or malformed or invalid
        or result["duplicate_timestamps"] or result["outside_declared_window"]
        or not result["strictly_ascending"])
    return result, within


def main():
    output = HERE / "result.json"
    if output.exists():
        raise FileExistsError("preserve existing audit result; no overwrite")
    # Minimal fixtures verify gap/empty/duplicate classification, not market behavior.
    row = lambda t: [t, 1, 1, 1, 1, 0]
    test, _ = summarize([row(0),row(7200)], 0, 10800)
    assert test["internal_missing_hours"] == 1 and not test["full_declared_window_complete"]
    test, _ = summarize([], 0, 10800)
    assert test["empty"] and test["total_missing_hours"] == 3
    test, _ = summarize([row(0),row(0)], 0, 3600)
    assert test["duplicate_timestamps"] == 1 and not test["full_declared_window_complete"]
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError("120s_audit_budget")))
    signal.alarm(120)
    snapshot = json.loads(SNAPSHOT.read_text())
    assets = re.findall(r"^    - ([A-Z0-9]+)/USDT$", (ROOT/"config/candidate_universe.yaml").read_text(), re.M)
    assert len(assets) == len(set(assets)) == 25
    assert {r["configured_label"] for r in snapshot["rows"]} == set(assets)
    candidates = {r["configured_label"]:r["candidate_product_id"] for r in snapshot["rows"]
                  if r["observed_product_fields"]["status"] == "online"}
    assert len(candidates) == 24
    sums = lambda path: {line.split(None,1)[1]:line.split(None,1)[0]
                         for line in path.read_text().splitlines() if line.strip()}
    archive_sums = sums(ARCHIVES/"SHA256SUMS_archives.txt")
    member_sums = sums(ARCHIVES/"SHA256SUMS_inputs.txt")
    windows = [("coinbase_hourly_last60d.tar.xz","cb",epoch("2026-08-10"),epoch("2026-10-09")),
               ("coinbase_hourly_prior10m.tar.xz","cb2",epoch("2025-10-09"),epoch("2026-08-10"))]
    results, sources, transfer = {}, {str(SNAPSHOT.relative_to(ROOT)):sha(SNAPSHOT)}, 0
    for archive, prefix, start, end in windows:
        path = ARCHIVES/archive
        actual = sha(path)
        if actual != archive_sums[archive]:
            raise ValueError("archive_hash_mismatch:"+archive)
        sources[str(path.relative_to(ROOT))] = actual
        wanted = {f"{prefix}/h1/{pid}.json":asset for asset,pid in candidates.items()}
        found, observed = {}, {}
        with tarfile.open(path, mode="r|xz") as stream:
            for member in stream:
                if member.name not in wanted:
                    continue
                if member.name in found or not member.isfile() or member.size > 8*1024*1024:
                    raise ValueError("unsafe_or_duplicate_selected_member")
                body = stream.extractfile(member).read(8*1024*1024+1)
                transfer += len(body)
                if len(body) != member.size or transfer > 128*1024*1024:
                    raise ValueError("selected_payload_budget")
                digest = hashlib.sha256(body).hexdigest()
                if digest != member_sums.get(member.name):
                    raise ValueError("member_hash_mismatch:"+member.name)
                info, times = summarize(json.loads(body), start, end)
                asset = wanted[member.name]
                found[member.name] = {"asset":asset,"product_id":candidates[asset],
                                      "sha256":digest,**info}
                observed[asset] = times
        if set(found) != set(wanted):
            raise ValueError("indexed_member_not_in_archive")
        missing_counts = Counter(t for times in observed.values() for t in set(range(start,end,HOUR))-times)
        results[prefix] = {"archive":archive,"start_utc":iso(start),"end_exclusive_utc":iso(end),
            "files_verified":len(found),"files":list(found.values()),
            "full_window_complete_files":sum(x["full_declared_window_complete"] for x in found.values()),
            "empty_files":sum(x["empty"] for x in found.values()),
            "final_300_complete_files":sum(x["final_300_hours_complete"] for x in found.values()),
            "all_24_missing_runs":runs(t for t,n in missing_counts.items() if n==24)}
    sources.update({str(p.relative_to(ROOT)):sha(p) for p in [Path(__file__),
        ARCHIVES/"SHA256SUMS_archives.txt",ARCHIVES/"SHA256SUMS_inputs.txt",
        ROOT/"config/candidate_universe.yaml"]})
    report = {"acceptance":"ACCEPTED","scope":"read-only archive integrity/schema/timestamp audit",
        "experiment_readiness":"INCOMPLETE","configured_assets":assets,
        "not_audited_no_indexed_archive":[a for a in assets if a not in candidates],
        "selected_candle_files":48,"compressed_archive_hashes_verified":2,
        "selected_payload_bytes":transfer,"elapsed_seconds":round(time.monotonic()-started,6),
        "timestamp_unit":"seconds; bar-open UTC; hourly","self_check_cases":3,
        "windows":results,"sources_sha256":sources,"network_requests":0,
        "strategies_imported_or_run":False,"price_or_volume_fields_analyzed":False,
        "extraction_to_disk":False,"returns_calculated":False,
        "limits":["leading/trailing absence is not attributed to listing/delisting without dated evidence",
                  "no price/OHLC/volume validity or executable liquidity assertion",
                  "six-column rows do not supply observation availability timestamps",
                  "previously used history is not a holdout or future warm-up guarantee"]}
    with output.open("x") as target:
        json.dump(report,target,indent=2,allow_nan=False)
        target.write("\n")
    signal.alarm(0)
    print(json.dumps({"output":str(output.relative_to(ROOT)),"elapsed_seconds":report["elapsed_seconds"],
        "hashes_verified":50,"windows":{k:{f:v[f] for f in ["files_verified","full_window_complete_files",
            "empty_files","final_300_complete_files","all_24_missing_runs"]} for k,v in results.items()}}))


if __name__ == "__main__":
    main()
