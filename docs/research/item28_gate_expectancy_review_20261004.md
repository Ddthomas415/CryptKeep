# Backlog item 28 (paper fee/PnL semantics): review of the gate path

2026-10-04. AUDITOR then ENGINEER (Claude). Reviewed on master 97c24c8e.
State: READY_FOR_INDEPENDENT_REVIEW. Nothing merged, pushed or deployed; no
config or account change. Patch 0035 (commit 088b2805, cloud clone only) is in
`docs/review_artifacts/20261004_rev32_bundle/cryptkeep_review_bundle_2026-10-02_rev46.zip`,
folder 43. Zip SHA-256:
74092817c4ea7902a31d891960468437057220d265e64e8aba395500abdcbaad

Scope: recorded fees were audited in E01
(`e01_paper_evidence_audit_20261002.md`) and are not repeated. This is what
the paper promotion gate computes.

## What holds

Paper promotion expectancy comes from the trade journal through FIFO lots, net
of both legs' fees, limited to provenance-qualified completed round trips. The
per-fill JSONL fallback is not used for paper promotion.

## Findings (both latent)

1. P2. The round-trip gate counted `closed_trades`, a FIFO lot-closing count.
   One round trip exited in two sells, or entered in two buys, counted 2.
2. P2. Qualification returns `ok: True` while listing
   `missing_journal_order_ids`, and the gate scored what was left:
   - five winning trips plus a sixth whose losing sell is absent from the
     journal: `expectancy_ok=True`, 9.78 per trade;
   - the losing sell present but sorted before its buy (journal timestamp in
     another format): `expectancy_ok=True`, 9.77, a 50.00 loss ignored.

## Current data

This checkout's canonical journal, read-only: 176 rows, one timestamp format,
every fee labelled USDT, the candidate's 10 buys and 10 sells all 0.001.
Neither finding is occurring; the 3/5 round-trip count is unaffected.

## Correction in 0035 (gate script only)

- Round trips = the smaller of journal closings and evidence round trips.
- Expectancy is unknown, with the reason, if a qualified order is missing from
  the journal, the journal fill count differs from the qualified evidence fill
  count, or the journal pairs fewer closings than the evidence has round trips.
- A computed expectancy keeps the accepted unit (per closed trade, net).

6 new cases, 5 fail on the previous code (one only for the new report field).
Full suite: 4445 passed, 33 skipped, 19 failed (the same 19 as master).

## Not changed

- The retirement trigger reads `expectancy_per_closed_trade` without this
  check: a dropped loss can also keep it from firing.
- `fifo_pnl_from_fills` ignores `fee_currency` and still charges the fee of a
  sell it ignores. The journal labels fees USDT on USD and EUR pairs.
- `_check_expectancy` (capped-live stage) averages per fill and counts buy
  fills as 0, so 5 round trips satisfy its "10 fills" minimum.
- With split entries or exits, "per closed trade" is not "per round trip".
  That unit is an accepted decision
  (`docs/decisions/canonical_expectancy_decision.md`).

## Addendum, same day: retirement check (patch 0036)

Commit 1b9f2dd2 (cloud clone only), bundle rev47, folder 44. Zip SHA-256:
693814f275aba1396eb53e04b2eaeb0a6313eb2eef0e82f2ef8c0c409554d4fc

- The journal/evidence comparison is one helper used by the paper gate and the
  retirement check. Report-only: the retirement result gains
  `journal_evidence_mismatch` and `expectancy_trigger_established`. No trigger
  is suppressed; `retirement_required` is computed as before.
- Three cases added (9 in the file); all three fail on 0035. Full suite: 4448
  passed, 33 skipped, 19 failed (the same 19 as master).

Observation on current data, not changed: `services/control/kernel.py`
auto-demotes a strategy when two retirement triggers are active, using the
average of `pnl_usd` over every fill record that has the key, buy fills
included at 0, minimum 10 records. This checkout's canonical fill evidence,
same formula computed read-only (the kernel was not run): 16 records (8 buys
at 0, 8 sells; 7 sells of unknown PnL semantics, 1 net of fees), sum -4.163,
average -0.2602. By that rule the negative-expectancy trigger is active now.
Without the buy records there are 8 values, below the minimum of 10. One
trigger is a review flag; a second (drawdown above 12%) would auto-demote.
