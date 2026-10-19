# FC-01-r1: session record and independent recomputation - 2026-10-04

AUDITOR (Claude), at the operator's request to document the session.
Read-only. This records what was decided and run in the Codex session on
2026-10-04 and adds an independent recomputation of its result. No collector,
config, campaign or account was touched; no file of Codex's was edited.
Not a profitability finding beyond the pilot it describes, and not financial
advice.

## 1. What happened, in order

Times are from the operator's session (New York) and the work log (UTC).

| # | Step | Who | Outcome |
|---|---|---|---|
| 1 | Laptop paper collector found dead (recorded PID 1506); operator approved a restart | Operator / Codex | Restarted with existing settings, PID 46484, 15:52 UTC |
| 2 | Context (crypto-edge) collector found silent since 00:06:13 UTC; restart authorized | Operator / Codex | Restarted with existing settings, PID 46947, 15:59:40 UTC |
| 3 | Workbook and count script reviewed and re-run | Codex | Every count and row-identity hash matched |
| 4 | Draft revised to FC-01-r1: 330-second freshness, explicit entry and exit quotes; threshold unchanged | Codex, "proceed" by operator | Frozen after availability counts, before any return |
| 5 | Design approved | Operator | "approved" |
| 6 | Inputs pinned: 138 windows, 101 complete paired, 17 entries, 84 cash, 37 unavailable | Codex | Input content SHA256 cd106bd5...9795f7a60f7 |
| 7 | Input pinning approved | Operator | "approved" |
| 8 | Exploratory outcome run, once, on the pinned inputs | Codex | Negative after fees (section 2) |
| 9 | Result accepted with risk; FC-01-r1 closed | Operator | STOP under tested costs; no 90-day confirmation; no same-data tuning |

Order matters and was kept: the freshness limit and entry price were fixed
after the eligibility counts and before any return was computed; the trial
registry was written before the outcome run.

## 2. The result (Codex's report)

Pinned archive 2026-08-30 to 2026-10-04, Coinbase BTC/USD, $100 purchase
notional per entry, entry at the ask, exit at the bid, 50 bps fee per side,
no extra slippage, no infrastructure cost. CF-MODELLED, not actual fills.

| | USD |
|---|---:|
| Rule (17 entries) | -15.99 |
| Enter every complete window (101) | -92.48 |
| Cash | 0.00 |
| Rule fees | 17.01 |

Disposition recorded: STOP this unchanged candidate under the tested cost
scenario. Scoped to this pilot; not a claim that imbalance can never work.

## 3. Independent recomputation (mine)

Method: my own code, written without reading `report_fc01_r1.py`, run
against the live database opened read-only with the same archive cut, NOT
against Codex's pinned JSON. Same rule text from the revised draft.

| Quantity | Codex | Mine | Match |
|---|---:|---:|---|
| Windows / complete / entries / cash / unavailable | 138 / 101 / 17 / 84 / 37 | 138 / 101 / 17 / 84 / 37 | yes |
| Rule gross before fees | about +1.01 | +1.01 | yes |
| Rule fees | 17.01 | 17.01 | yes |
| Rule net | -15.99 | -15.99 | yes |
| Enter every window, net | -92.48 | -92.48 | yes |
| Selected windows, mean midpoint move | +5.95 bps | +5.95 bps | yes |

Not recomputed: the bootstrap intervals. Not re-run: Codex's five tests.

## 4. Three things the recomputation adds

1. The rule did not pick better windows. Mean six-hour midpoint move:
   selected +5.95 bps, rejected +9.07 bps, all 101 windows +8.54 bps. The
   selected windows did slightly WORSE than the ones the rule turned down.
   The "+76.49 better than entering every window" is entirely from trading
   less often at a loss-making cost, as Codex's report also says; there is
   no sign of selection value in this sample.
2. The edge needed is far from the edge seen. The fee per side at which the
   rule would have netted zero in this sample is about 3 bps. The account's
   recorded taker fee is 50 bps and its recorded maker fee 25 bps. So neither
   recorded tier would have made it positive, even with every fill assumed.
3. One winner after fees. 7 of 17 entries were up before fees; 1 of 17 was
   up after fees.

These are descriptive of 17 entries in one 35-day period. They do not show
the feature is useless in general; they show this rule, at these costs, in
this sample, lost money for a reason that more data would not obviously fix.

## 5. Agreement with the earlier cost argument

`fc01_gate2_eligibility_count_20261004.md` (items 5-7) argued before any
outcome that a rule trading every day or two at 100 bps round trip needs
about 1% per trade on average and was unlikely to clear it. The pilot's
observed average, about 6 bps, is consistent with that. The pilot was still
worth running in the form it took: it cost no new data and no waiting, and
it replaced an a-priori argument with a measured one.

## 6. Correction to my own earlier statements

- My workbook and note said the laptop archive was "not growing". That was
  true when written (15:48 UTC) and is no longer: the context collector was
  restarted at 15:59:40 UTC and had written 4 cycles with 0 errors by
  16:15 UTC (its own status file; rows visible in the database).
- The outage left a hole of 15 h 53 min (2026-10-04 00:06:13 to 15:59:51
  UTC) in every context series. It cannot be backfilled.

## 7. State after this session

| Item | State |
|---|---|
| FC-01-r1 | Closed: STOP under tested costs. No confirmation collection. No same-data tuning. |
| SMA200 candidate, E02, E03 | Unchanged and undecided. Codex names E02/E03 as the next priority. |
| Laptop paper collector | Running (PID 46484 at restart); next session at the next UTC day. |
| Laptop context collector | Running (PID 46947 at restart). |
| Automatic recovery after a reboot or sleep | NOT configured for either collector. |
| Hetzner host | Not checked by anyone today. Trial fixed end 2026-10-13 00:00 UTC. |
| Patch series 0001-0030 | Reviewed patch by patch (latest: 0029/0030 ACCEPTED_WITH_RISK); overall INCOMPLETE; not pushed, merged or deployed. |

## 8. Artifact hashes at the time of this record (SHA256)

| File | SHA256 |
|---|---|
| docs/research/faster_context_hypothesis_draft_20261004.md | 6b69f66c8d1f487777ebd7b41eb41cd4add0d0feed85cc4248fbc4a31003ecaa |
| docs/research/fc01_r1_exploratory_result_20261004.md | c52c5d24fc9c89bb6a28b4dcd420bd39ec06d5ebeb91b62b3cddb8e74938ae2e |
| docs/review_artifacts/20261004_fc01/pilot_trial_registry.md | 71653e469292a9b2e34477b1c4ea54fa847026e8443e83ceb216bb2851bf6cc4 |
| docs/review_artifacts/20261004_fc01/pin_fc01_r1.py | 7139786c76d649bc81797d1361b6f6feb831d87c3a12712b417dc48e0ef28480 |
| docs/review_artifacts/20261004_fc01/report_fc01_r1.py | 4075d3993b51968377f86dcad39e32a2574a9b35ec2cbeeae6bbdef141034f2e |
| docs/review_artifacts/20261004_fc01/test_report_fc01_r1.py | 225eba0e88bd18d13f0c50c2e7c66e502e615d5006e44ee8e295bf62428536ee |
| docs/review_artifacts/20261004_fc01/fc01_r1_pinned_inputs.json | 19437756bf2ed9767e092572312002d37927a3764605914a41b3184a712f6d74 |
| docs/review_artifacts/20261004_fc01/fc01_r1_exploratory_results.json | 39192e790a360dfefa9282a222b337dc0b239f9fc1f4a25a7aa6a34bc31d367d |
| docs/review_artifacts/20261004_fc01/fc01_gate2_count.py | 8b020304556af82b0330b4dff33fe95c67e2d26a9605872e663832b677865244 |

## 9. Limits

- "Independent" here means separate code and a separate read of the
  database by a different agent. It is the same data, the same rule text
  and the same cost model, so it checks the arithmetic, not the design.
- `capture_ts` is storage time after the fetch, not exchange time (Codex's
  registry says so). Neither run tests whether the quotes were actionable.
- One 35-day period, 17 entries, one market regime.
- Step 1 of the table is from the operator's pasted session and the work
  log; I did not observe the processes.
