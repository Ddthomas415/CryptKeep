# Offline E1 observation-window diagnosis

Bot relation: STANDALONE diagnostic; runtime trading configuration not checked.

**2026-11-13. Active role AUDITOR. Status: ACCEPTED_WITH_RISK for offline diagnosis/reporting only.**
Owner scope: one offline diagnosis of the existing ETH capture, its minimum justified correction, and one independent review. No new public requests, source changes or experimental outcomes.

## Answer

**SHOWN:** ETH failed the declared local-window filter because every returned trade timestamp precedes that window. Replaying the original validator reproduces exactly `no_reported_trades_in_local_window`; BTC reproduces its conditional COMPLETE result with 83 selected prints. The conservative exclusion is working as written. No demonstrated parser/filter defect justifies changing production or diagnostic source.

**UNVERIFIED:** why those observations diverge. Delayed/cached trade responses, differences between book/trade publication timing, source-clock offsets and a real pause cannot be distinguished with these receipts. Diagnosis is complete at the evidence-limit boundary; the upstream causal mechanism and E1 qualification remain INCOMPLETE.

The practical decision is **not to patch the filter or rerun until green**. A future measurement correction must establish freshness/clock and interval coverage before cost interpretation. None of this supplies a strategy-return or live-fill result.

## Evidence and exact reproduction

Inspected the complete existing capture source, its saved protocol/result and prior receipt review, all ten raw/receipt bindings, both trade pages and six books. Reused the October28 E1 readiness reconciliation and arrival-observer boundary rather than proposing another framework. No runtime trading configuration, current process, host clock synchronization, live endpoint, account or actual order was inspected.

| Saved product | Prints in declared local window | Newest print before trade request | Reported book-source time behind local receipt, T0 / arrival / final |
| --- | --- | --- | --- |
| BTC-USD | 83 of 100 | 0.465213 seconds | 1.173725 / 0.761721 / 0.463041 seconds |
| ETH-USD | 0 of 100 | 4.648994 seconds | 2.565511 / 2.198216 / 2.195120 seconds |

These signed timestamp differences are arithmetic, **not measured network latency or calibrated source age**. Book source timestamps have nanosecond strings; the stdlib diagnostic truncates to microseconds, with less than one-microsecond effect on these numbers. HTTP request durations are independent monotonic observations.

ETH's local window is 17:31:33.213300Z through17:31:37.433671Z. Its newest returned trade is17:31:32.804163Z, **0.409137 seconds before the start**, not merely before the final request. Its oldest is17:31:17.408233Z; page span15.395930seconds, largest internal interprint gap1.616944seconds. BTC span6.919360seconds/largest gap0.769810seconds. Both contain100 distinct IDs; neither page proves complete market coverage.

**SHOWN diagnostic distinction:** using the saved books' own source timestamps only to inspect overlap gives ETH7prints and BTC86prints. ETH's last book reports17:31:35.238551604Z, after its newest returned trade by about2.434389seconds. The book sequences increase across all three observations. This shows that price/book observation and the returned trade page are not demonstrated to describe the same event interval. It does **not** establish their relative clock calibration, prove trading continued, or authorize using this alternate interval to rescue the result. Local-window qualification stays unchanged.

The stored HTTP Date values track the request's displayed UTC second. Only `date`, `content-type`, `cb-before`, and `cb-after` are retained by the source allowlist. Therefore the saved receipts cannot tell whether upstream Age/Cache-Control/Via/cache-status headers existed or what they said. HTTP Date is second-resolution response metadata, not an exchange clock calibration or proof of uncached trade data. Pagination cursors are present; no additional page was fetched.

[Machine-readable arithmetic, raw bindings and validation replay](ETH_OFFLINE_DIAGNOSIS_20261113.json) records the exact results. The replay calls the unchanged pure `metadata/book/analyse` functions; `analyse` also recomputes the existing conditional shadow arithmetic internally, but no new strategy/backtest, fee comparison conclusion, parameter search or account result is scored. Socket connection creation and the urllib opener are patched to raise if invoked. Zero network calls and no capture output are produced.

## Cause classification and minimum justified correction

- **SHOWN cause class: data/measurement limits.** The fixed single-page REST design supplies no verified complete interval or local/source clock alignment. HTTP success did not supply the required trade observations. This narrows “collection succeeded” to transport success only.
- **UNVERIFIED causal alternatives:** cache/publication lag, clock disagreement, or real no-trade interval. One short observation gives no defensible likelihood ranking or normal-trading baseline. The gap being larger than the maximum gap inside one selected page is not a statistical test of a trading pause.
- **No demonstrated engineering defect in the conservative exclusion.** Preserve the failed capture, the source, and all frozen criteria. No patch or new regression test is appropriate merely to force a formerly excluded event into COMPLETE.
- **Smallest future proposal, not implementation:** reuse the existing observe-only transport/arrival components; retain bounded allowlisted non-secret freshness metadata if supplied, plus independently documented clock uncertainty; adopt an E1-specific freshness/alignment and interval-coverage rule before applying it. Under a separately approved collection budget, require evidence covering the declared interval or explicitly mark it uncovered. Increasing page size or fetching older pages cannot manufacture trades newer than the returned newest print. Do not invent a numeric freshness threshold from this one sample, shift clocks to maximize overlap, or assert that cache-busting will repair an unproved cache fault.
- **What proves a correction:** deterministic cases for delayed newest prints, a page whose oldest print fails to reach the start, duplicates/conflicts across bounded pages, absent/inconsistent source times, and exhausted collection bounds must remain unqualified. Adequate complete evidence may qualify only under the separately adopted clock/coverage contract. Source-change regression proof is required only if that future implementation exposes an actual bug.

This proposal is inside existing E1 readiness gaps, not permission for a new controller/daemon, extra market request, budget extension, schedule, bot change, whole-project hold, scope narrowing or automatic code implementation.

## Preservation, limitations and acceptance

Original capture remains INCOMPLETE. Original source SHA256 `4ac85819a81ee00d10307550dfc2bd532c2d1b2e676d57080e848c6c788dff88`.
Original report.json SHA256 `ea5f99ce687b8bb96464d57eb9446c77cfe30c29f19f997e6057a7e89ea98252`.
Frozen v3.3 SHA256 `8414bbcf00883f74e1cfa49c4c3161e4a742e19282b28235dc48a4a2ac1aaad6`.
All ten raw payload hashes/byte counts match their saved receipts; receipt hashes are in the JSON. Primary tracker and all ledgers remain untouched.

**DONE, self-checked:** offline evidence trace, exact validator reproduction, measurement/cause separation, minimum proposal and preserved-original checks.
**DONE:** one independent review of underlying files, not merely this summary; see receipt below.
**INCOMPLETE:** upstream cause, clock/coverage qualification, eligible Monday evidence and actual-fill/E1 conclusions.

No broad suite was run: no code changed. A full suite or another market replay would not identify an unsaved cache header, clock state or missing trade. The final verification will check new report links and unchanged original hashes. This evidence lane is not a report of live services, account fees, economic return or trading readiness.

## Reproduction command (offline; no files written)

Run from the repository root. This is the exact calculation performed for the saved JSON; it emits JSON to stdout only and does not invoke the live capture CLI.

```sh
./.venv/bin/python -B - <<'PY'
import datetime as dt
import hashlib
import json
from pathlib import Path
import runpy
from unittest.mock import patch

root = Path("docs/research/btc_eth_forward_experiment_20261112")
folder = root / "public_diagnostics/20261113T173128Z_b7514447"
source = Path("scripts/research/capture_candidate_execution_diagnostic.py")
stamp = lambda s: dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
module = runpy.run_path(str(source), run_name="offline_e1_diagnosis")
receipts = [json.loads(p.read_text()) for p in sorted(folder.glob("*_receipt.json"))]
evidence = {"source_sha256": digest(source),
            "frozen_criteria_sha256": digest(root / "CRITERIA_DRAFT_V3_3.md"),
            "original_report_sha256": digest(folder / "report.json"),
            "network_requests": 0, "timestamp_precision": "Python datetime microseconds; source book nanoseconds truncated",
            "products": {}, "raw_bindings": []}
for r in receipts:
    raw = folder / r["raw_file"]
    evidence["raw_bindings"].append({"raw_file": r["raw_file"], "sha256": digest(raw),
        "receipt_sha256": digest(folder / (r["raw_file"].split("_")[0] + "_receipt.json")),
        "bytes": raw.stat().st_size, "matches_receipt": digest(raw) == r["sha256"] and raw.stat().st_size == r["bytes"]})
for product in ("BTC-USD", "ETH-USD"):
    by_label = {r["label"]: r for r in receipts if r["product"] == product}
    body = lambda label: json.loads((folder / by_label[label]["raw_file"]).read_bytes())
    start = stamp(by_label["t0"]["receipt_utc"])
    end = stamp(by_label["final"]["receipt_utc"])
    trades = body("trades")
    times = sorted(stamp(t["time"]) for t in trades)
    source_start, source_end = [stamp(body(k)["time"]) for k in ("t0", "final")]
    book_rows = []
    for label in ("t0", "arrival", "final"):
        r = by_label[label]
        b = body(label)
        t = stamp(b["time"])
        book_rows.append({"label": label, "source_time": b["time"], "sequence": b["sequence"],
            "request_utc": r["request_utc"], "receipt_utc": r["receipt_utc"],
            "reported_source_behind_receipt_s": (stamp(r["receipt_utc"]) - t).total_seconds(),
            "monotonic_request_duration_s": r["duration_seconds"]})
    with patch("socket.create_connection", side_effect=AssertionError("network prohibited")), patch("urllib.request.OpenerDirector.open", side_effect=AssertionError("network prohibited")):
        try:
            result = module["analyse"](module["metadata"](body("metadata"), product),
                 [module["book"](body(k)) for k in ("t0", "arrival", "final")],
                 trades, (start.timestamp(), end.timestamp()))
            replay = {"status": result["status"], "window_prints": result["window_prints"],
                      "qualification": "CONDITIONAL_ONLY_NOT_E1_OR_FILL_PROOF"}
        except module["Invalid"] as exc:
            replay = {"status": "INCOMPLETE", "reason": str(exc)}
    evidence["products"][product] = {
        "local_window": [start.isoformat(), end.isoformat()],
        "source_book_window_diagnostic_only": [source_start.isoformat(), source_end.isoformat()],
        "trade_rows": len(times), "oldest": times[0].isoformat(), "newest": times[-1].isoformat(),
        "span_s": (times[-1] - times[0]).total_seconds(),
        "max_internal_interprint_gap_s": max((b-a).total_seconds() for a,b in zip(times, times[1:])),
        "newest_before_trade_request_s": (stamp(by_label["trades"]["request_utc"])-times[-1]).total_seconds(),
        "newest_before_initial_local_receipt_s": (start-times[-1]).total_seconds(),
        "source_book_end_after_newest_trade_s": (source_end-times[-1]).total_seconds(),
        "trades_inside_local_window": sum(start <= t <= end for t in times),
        "trades_inside_source_book_window_diagnostic_only": sum(source_start <= t <= source_end for t in times),
        "trade_ids_unique": len({t["trade_id"] for t in trades}) == len(trades),
        "book_observations": book_rows,
        "trade_receipt_headers": by_label["trades"]["headers"],
        "validation_replay": replay}
print(json.dumps(evidence, sort_keys=True, indent=2, allow_nan=False))
PY
```

What do I know that could change the owner's decision that I have not yet said?

The clock issue affects interpretation of the apparently successful BTC result too: its 83 matching prints show overlap, not complete coverage or actual maker fills. The correct next improvement is qualified measurement, not converting ETH to a pass by redefining its interval. Existing prospective Q1/Q2 criteria and the whole multi-symbol platform remain intact.

## Independent review receipt

Separate Nash GATE `01a1cee8-b4ec-7343-9992-b771df07aba1`, checked **2026-11-13T18:31:51Z**: **ACCEPTED_WITH_RISK for offline diagnosis/reporting only; no blocking finding**. Reviewer inspected the capture source, new report/JSON and underlying saved trade/book bodies and receipts; independently reproduced BTC83/ETH0 and original ETH error, all six source/local timestamp offsets, and diagnostic-only BTC86/ETH7 overlap. Source/original-report hashes match; prior ten-body integrity review was reused, not broadly restarted. The no-patch recommendation is supported. No network, live capture, edits or broad tests. This receipt changes report disposition only; it does not certify the upstream cause, clock/coverage alignment, E1, actual fills or economics.

What do I know that could change the owner's decision that I have not yet said?

Independent review confirms the conservative diagnosis, not a repaired collector. BTC overlap remains unqualified too. Further implementation must improve measurement provenance/coverage under an explicit bounded scope, without weakening the frozen criteria or replacing the failed evidence.

## Source provenance update: 2026-11-13T18:41:15Z

The owner subsequently authorized diagnostic-only instrumentation in the current source. The source hash quoted in this historical diagnosis remains valid for its exact [preserved pre-instrumentation source](diagnostic_proof_20261113/before_freshness_instrumentation.py). For the historical reproduction command above, substitute that preserved path for the current script path; the saved JSON/result is unchanged. See [instrumentation scope and source proof](FRESHNESS_INSTRUMENTATION_20261113.md). This is not a reclassification of the original capture or a new explanation of its upstream cause.

What do I know that could change the owner's decision that I have not yet said? Source provenance is now explicit across the revision; more diagnostics do not make this historical incomplete event qualified.
