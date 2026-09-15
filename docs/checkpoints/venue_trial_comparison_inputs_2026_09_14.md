# Venue Trial Comparison Inputs

Active role: AUDITOR. Read-only preparation; outcomes pending.

## Explicit Sources

Host root: /srv/cryptkeep/app/.cbp_state_challengers.
For each venue gateio/binance, read two separate roots:
- ema_cross_<venue>_btcusdt_daily (existing daily control).
- ema_cross_<venue>_btcusdt_24h_trial (new trial).

Use runtime/health/paper_strategy_evidence.json for status and bounded-session
results; session JSONL under data/evidence/<session-id>/ for historical start/end
records. Daily session IDs end in _paper_candidate, trial IDs in _24h_trial.
Fill/order evidence may instead use preset label ema_cross_default, so never
select a source merely by strategy label. Root, venue, symbol and timestamp
are all required. Persisted stores: data/intent_queue.sqlite,
data/paper_trading.sqlite, data/trade_journal.sqlite.

## Baseline Observed September 14

| Daily control | Session start UTC | Session end UTC | Fills delta | Closed delta | Historical fills/closes |
| --- | --- | --- | ---: | ---: | --- |
| Gate.io | 00:03:41.049825 | 00:18:47.018618 | 0 | 0 | 0 / 0 |
| Binance | 00:03:46.370833 | 00:18:49.039518 | 0 | 0 | 2 / 1 |

Binance historical latest fill is September 11; historical net PnL
-2.1213665852374706 is NOT a trial-window outcome. Both daily status files
were idle; both trial files running. Trial last_results were empty because
their windows had not completed. Empty results do not imply zero outcomes.

## Time Alignment

Both units entered active September 14 at 04:13:34 UTC. Use actual strategy
start/end timestamps at completion, not unit activation alone. September 14
daily sessions precede the trials and cannot be called overlapping controls.
September 15 daily sessions are expected to overlap but must be observed,
not assumed successful. For each venue, compute intersection of actual daily
and trial strategy intervals; report missing/no overlap explicitly.

Report two distinct views:
1. Whole trial: operational coverage, signals/actions, fills, costs, residual
   positions and pending intents across its observed interval.
2. Matched overlap: compare both modes on the intersection only, and separately
   identify trial actions outside the daily observation interval.

Do not divide a historical aggregate by runtime and call it a fair comparison.
Carry-in position/signal state differs between daily and fresh trial processes;
matching timestamps/configuration does not remove that confounder. Do not infer
causal profitability improvements from one day or rank venues on unequal paths.

## Cost and Integrity Rules

Prior deployed resolver checks show both modes use EMA12/26, same filters,
.001 BTC, 10000 quote starting cash and fee/slippage 7.5/5 bps. These are modeled
costs, not actual exchange fee quotes. Record effective runtime/config version
and any deviations; exclude unrelated historic fills. Gross and net win/loss
labels must remain distinct. Mark open positions separately from realized PnL.

Use existing terminal checklist in extended_venue_observation_trial_2026_09_05.md.
After all trial writers stop, use SQLite mode=ro and record integrity checks,
status counts, pending intents, fills, positions and selected-record hashes.
Daily controls remain active: use coherent read transactions or SQLite backup
snapshots, never assume a copied live database file is consistent.

Session/status files and latest OHLCV snapshots do not establish continuous
per-bar coverage. Inventory retained timestamped observations first; label
unrecorded intervals unknown and do not reconstruct them as observed using a
later fetch. Existing loss replay with explicit journal path is descriptive;
its whole-history output is not an interval-filtered trial result.

No new tool, scheduler, runtime change or campaign reset introduced.
Acceptance state: ACCEPTED for source/time alignment plan; results INCOMPLETE.
