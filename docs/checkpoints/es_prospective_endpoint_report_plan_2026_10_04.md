# Corrected ES prospective trial: endpoint report plan

## October 7 host-verification addendum

The prepared report is `es_prospective_endpoint_report_2026_10_13.md`.
Actual-host checks now establish capture activation at September 21 01:27:11 UTC;
15 earlier signals that day have no capture metadata. The verifier example below
starting at midnight is historical and must not be used as a post-activation
failure test. Use `--since 2026-09-21T01:27:11Z`, disclose earlier non-replayable
records, and retain the full trial/session window. This does not alter the trial.
See `es_preendpoint_host_status_2026_10_07.md` for current bounded proof.

2026-10-04. AUDITOR (Claude). PROPOSED, for review. Written nine days BEFORE
the fixed endpoint so that what is reported, and how it is read, is fixed in
advance. It adds no rule to the trial, changes no host state and extends
nothing. It implements the "At the fixed endpoint, report ..." paragraph of
`docs/checkpoints/es_prospective_evaluation_contract_2026_09_09.md`.

## Fixed facts (work log, "2026-09-12T19:53:01Z - Human-Approved Isolated ES Trial Launch")

| | |
|---|---|
| State directory (host) | `/srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1` |
| Launch | 2026-09-12T19:53:01.418557Z |
| Evaluation window | 2026-09-13 00:00 UTC to 2026-10-13 00:00 UTC (30 UTC days), half-open |
| Seed SHA256 | 81accfe4d0acf86d7bcc11c771899c977c3c04893f9093500b073a535e92a1f8 |
| Effective config | SMA200 / ATR20, qty 0.001 BTC, cash 10,000 USDT, paper fee 7.5 bps, slippage 5 bps, four exit controls at zero |
| Signal-input capture | activated 2026-09-21 (work log); earlier days are not replayable |
| Deadline | systemd timer, next elapse 2026-10-13 00:00:00 UTC |

## State on record before the endpoint (not a result)

Through the last host inspections (2026-09-19 and 2026-09-28): daily
sessions completing; signal BUY unchanged; zero intents, fills and closes.
The 2026-09-28 diagnosis: the runner enters only on a signal CHANGE; the
signal has been BUY since before launch, so no entry transition has occurred.

Expected outcome, stated now: **zero trades**, unless the signal goes flat
and then long again before 2026-10-13. Under the contract, "Zero or few
trades is an inconclusive trading-efficacy result, not a failure to be
hidden." That is the reading this plan commits to. Zero trades will NOT be
reported as evidence for or against the strategy, and will NOT be a reason
to extend the trial ("No automatic extension").

## What the report must contain (each item from the contract)

| # | Item | Source on the host (read-only) | If unavailable |
|---|---|---|---|
| 1 | Completed trades | the trial state's paper fills and trade journal | report "none recorded" with the query used |
| 2 | Open position, marked to market at 2026-10-13 00:00 UTC | paper position row + the daily close used by the runtime | report position and state the mark source |
| 3 | Fees | paper fills | 0 if no fills |
| 4 | Drawdown | paper equity series | "not meaningful: no exposure" if no position was ever open |
| 5 | Data gaps | expected 30 daily sessions vs sessions recorded, each missing day listed | every missing scheduled observation reported explicitly |
| 6 | Strategy decisions including holds | signal evidence per day (direction, regime, entry permission, action) | list per day; do not summarise away holds |
| 7 | Cash comparison | 10,000 USDT, 0 return | n/a |
| 8 | Buy-and-hold comparison | same capital basis and source window, explicit costs, labelled MODELLED | see "Comparators" |
| 9 | Config identity | seed hash and effective config at the endpoint vs launch | any drift marks the evaluation invalid/incomplete |
| 10 | Signal-record verification | `scripts/research/verify_es_signal_capture.py` over 2026-09-21 to 2026-10-13 | exit 2 (no records) is NOT success |

## Validity checks before any number is read

The contract makes the evaluation invalid or incomplete, not repairable by
older fills, on any of: configuration identity drift; substituted source or
provenance; duplicate execution accounting; an unreported missing scheduled
observation. The report states each of the four as PASS / FAIL / NOT
CHECKED with the evidence, before the results section.

## Comparators (fixed now)

- Window: the evaluation window above. Source: the same Coinbase BTC/USDT
  daily data the runtime observed, not a later finalised series where they
  differ.
- Buy-and-hold: 0.001 BTC bought at the first evaluated daily bar and marked
  at the endpoint, same 10,000 USDT account. Reported twice, both labelled
  MODELLED: at the paper engine's 7.5 bps + 5 bps, and at the account's
  recorded taker rate of 50 bps per side (work log 2026-09-26; not
  re-verified).
- Cash: 0.
- No volatility or risk matching is claimed. No winner is selected.

## Read-only commands (host; none changes state)

```sh
# 10. signal-record verification, capture period only
./.venv/bin/python scripts/research/verify_es_signal_capture.py \
  --state-dir /srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1 \
  --since 2026-09-21T00:00:00Z --until 2026-10-13T00:00:00Z

# service and deadline state
systemctl --user --no-pager status cbp-es-corrected-prospective.service
systemctl --user --no-pager list-timers | grep -i es-corrected
```

Items 1-6 and 9 need read-only SQLite queries (`mode=ro`) and file hashes in
the trial state directory. I have not seen that directory, so I do not write
the queries here; they should be written and reviewed against it.

## What the report must NOT do

- Extend, restart or re-seed the trial, or reset the entry latch.
- Count fills from the laptop cohort or any other state directory.
- Present zero trades as success, or as failure.
- Recommend live promotion or a size increase "from this 30-day observation
  alone" (contract).
- Use a later finalised candle in place of the partial candle the runtime saw.

## After the report

The endpoint report is one input to E03 (continue / revise / retire), with
`docs/research/e03_decision_brief_20261004.md` and its three addenda. It does
not make that decision.

## Limits of this plan

Written from the repository only. I cannot reach the host; state after
2026-09-28 is unknown to me. Whether the deadline timer stops the service
cleanly at the endpoint, and what the stop preserves, is recorded in the
launch entry as intended behaviour, not verified by me.
