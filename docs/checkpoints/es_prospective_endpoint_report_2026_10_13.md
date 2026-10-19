# Corrected ES trial endpoint report

Status: PREPARED, NOT AN ENDPOINT RESULT. Prepared October 7, 2026.
Role: AUDITOR. Evaluation acceptance: INCOMPLETE.

## Fixed contract

- Actual host state: /srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1
- Evaluation: [2026-09-13T00:00:00Z, 2026-10-13T00:00:00Z), 30 UTC days.
- Preserve SMA200/ATR20, crossover-only entry, 0.001 BTC quantity, 10000 USDT
  initial cash, declared disabled exit controls, trial dates and state.
- Launch seed SHA256: 81accfe4d0acf86d7bcc11c771899c977c3c04893f9093500b073a535e92a1f8.
- No reset, restart, forced entry, automatic extension or live promotion.

## Validity before results

| Check | Endpoint status | Required evidence |
| --- | --- | --- |
| Effective configuration identity | NOT CHECKED | Compare launch seed and resolved child settings; seed hash alone is insufficient |
| Source/provenance preserved | NOT CHECKED | Captured inputs and per-day signal provenance, including pre-capture limits |
| Duplicate execution accounting | NOT CHECKED | Read-only intent/order/fill/journal identity checks, not counts alone if nonzero |
| Every expected observation reported | NOT CHECKED | All 30 UTC days, missing/failed/incomplete sessions listed explicitly |
| Deadline actually stopped service | NOT CHECKED | Post-endpoint service/process status, not timer schedule alone |

Do not convert unknown checks to PASS. A failed material identity/provenance or
accounting check makes the evaluation invalid/incomplete, not retrospectively
repairable using another cohort.

## Endpoint results to populate

| Metric | Result | Evidence requirements |
| --- | --- | --- |
| Completed trades | NOT COLLECTED | Match entries/exits from fills and journal; do not equate fills with trades |
| Open positions | NOT COLLECTED | Exact quantities and endpoint marks with source/timestamp |
| Fees | NOT COLLECTED | Sum by fee currency before any explicit conversion |
| Net PnL | NOT COLLECTED | Fill-derived cash flows and both entry/exit costs; state currency |
| Drawdown | NOT COLLECTED | Equity observations and gap limits; no exposure means not meaningful |
| Missing/failed daily sessions | NOT COLLECTED | September 13 through October 12 inclusive |
| Daily signals and holds | NOT COLLECTED | Direction, regime, entry permission, action and reason for every day |
| Cash comparator | 0 USDT under contract | 10000 USDT starting cash; no assumed yield |
| Buy-and-hold comparator | NOT COLLECTED, MODELLED | 0.001 BTC sleeve and remaining cash in the same 10000 USDT account |
| Monthly infrastructure cost | Approximately 20 USD/month | Operator estimate supplied October 8; not invoice-verified |

Buy-and-hold uses original runtime-observed source/window, paper 7.5 bps fee
and 5 bps slippage scenario, plus separately labelled 50 bps taker-fee scenario.
State fee-rate observation date; do not imply historical rate constancy.
Separate open-position marked value from hypothetical liquidation costs. If the
required original first/endpoint price is missing, report comparator unavailable;
do not quietly substitute finalized candles. No risk matching or winner selection.

Report trading PnL before infrastructure and estimated operating net separately.
Allocating the full estimated monthly cost to this 30-day trial would subtract
approximately 20 USD under an explicit 30-day-month convention. State whether
costs are shared with other research; do not deduct them twice or silently equate
USDT with USD. Break-even arithmetic at 1000 USD capital is 2% monthly, or 0.2%
at 10000 USD, merely to cover infrastructure. These are not expected returns or
authorization to increase capital. Capital contributions are not profit.

## Capture boundary

Authorized capture restart: September 21 01:27:11 UTC. Fifteen records on that
day at 00:02:29-00:02:46 precede activation. They remain non-replayable and must
be disclosed, but are not post-activation capture failures.

Use this read-only verifier window on the matching host runtime:

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python scripts/research/verify_es_signal_capture.py \
  --state-dir /srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1 \
  --since 2026-09-21T01:27:11Z --until 2026-10-13T00:00:00Z
```

Record command/result and selected/verified counts. Exit 2 is no evidence,
not success. Replay verifies recorded signals, not session completeness or orders.

## Read-only accounting extraction

Open the trial databases with SQLite URI mode=ro; never initialize missing files.
Filter timestamps to the half-open trial window and report unexpected records
outside it separately. Read paper_fills joined to paper_orders by order_id;
match journal_fills by fill_id/order_id and intents by linked identity. Read
paper_positions and paper_equity without writing marks or forcing liquidation.
If trades exist, inspect partial fills, fees and journal consistency before PnL.
Use a coherent read transaction per database; cross-database consistency still
needs explicit checking. Report schema changes or missing tables as incomplete.

## Prior checkpoint, not endpoint evidence

October 7 host check: 25 completed daily sessions, zero intents/orders/fills/
positions, cash 10000.0. September 22-October 7 captured signals: 251 selected,
251 successfully replayed. Seed matches launch. These figures must be refreshed
after the endpoint; they are not prefilled final results.

## Interpretation and decision

Zero or few trades: INCONCLUSIVE trading efficacy. Operational evidence and
economic evidence are separate. No automatic continuation, capital increase or
entry-contract change. Report supports the existing E03 continue/revise/retire
decision, which remains the operator's choice.
