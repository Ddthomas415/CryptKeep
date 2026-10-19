# Why es_daily_trend_v1 has no winning trade and has not traded since 9 July - 2026-10-07

Reviewer: Claude. Read-only on the laptop (checkout `620bc8dbe`): evidence files, the runner's
state store, the paper intent queue and the runner source. Nothing changed. No new patch:
the fix is patch 0001 of the review series, which is not merged.

## Finding 1: the strategy has been locked out since 9 July by the kill cooldown

On 2026-07-09 the third consecutive losing exit triggered the performance kill. The runner
stored `kill_until = 51`, an absolute loop number. The loop counter restarts at 0 in every
process, and this campaign starts a new process every day. So the first 50 loops of every
daily session have been blocked ever since.

That alone would leave about ten unblocked loops at the end of each session (a session
runs about 61 loops). But the runner only enters when the signal *changes*, and it records
the change before the kill check. Each time the signal turned long, the change was consumed
in loop 1, inside the blocked part, and never offered again.

| Evidence | Value |
|---|---|
| `loss_streak:coinbase:BTC/USDT:sma_200_trend` | `3`, written 2026-07-09T00:03:59 |
| `kill_until:coinbase:BTC/USDT:sma_200_trend` | `51`, written 2026-07-09T00:03:59, never updated |
| `last_action` / `last_emitted_action` on 2026-10-07 | `buy` / `hold` |
| Runner source on the laptop | `should_block_symbol(loops=loops, kill_until_loop=kill_until_loop)` |
| Signal records per day in September | median 61 |
| Paper intents since 9 July | none |
| Signals since 9 July | 2,219; `entry_allowed` true on all; direction long on 1,995 |

The signal turned long on 2026-07-26, 08-06, 08-08 and 08-18. No entry followed any of them.

| Date | Signal | Price | SMA-200 |
|---|---|---|---|
| 2026-08-18 (last turn to long) | long | 64,542 | 63,902 |
| 2026-10-07 | long | 85,581 | 71,692 |

The signal has been long without interruption since 18 August, a 32.6% move in price, with
no position. On the campaign's 0.001 BTC that is about 21 USD before fees. This is the size
of the move the signal called, not a guaranteed result: the strategy's own stop or trailing
exit could have closed a position on the way.

## The fix already exists and is not merged

Patch 0001 of the series, `0ef8b34a` "fix: expire kill cooldown across runner sessions",
replaces the absolute loop number with a count of blocked loops that persists across
processes, and converts a leftover `kill_until` once. With it this cooldown would have ended
during the session of 10 July and the turn to long on 26 July would have been taken.
REVIEW_HANDOFF.md lists 0001 under "earlier bounded reviews; not a fresh deployment
approval". Master (`97c24c8e`) still has the old form.

Still true with 0001: an entry refused for any reason is not offered again until the signal
changes (listed in REVIEW_HANDOFF.md as a known open point).

## Finding 2: the eight "closed trades" are mostly not strategy trades

| Trades | What they are |
|---|---|
| 3 on 2026-04-20, 1 on 2026-05-15 | Held 1 to 4 minutes on a daily strategy: development runs. PnL recorded as 0.0 on three of them although price moved against. |
| Buy 2026-05-18 at 39,864.7, sell 2026-05-26 at 77,281.2 | The buy price is about half the market (BTC was near 80,000). A mispriced paper fill of the kind fixed later (exact-symbol quotes). PnL recorded as 0.0. |
| 2026-06-16, 06-21, 07-04 | Three genuine trades on daily bars: -2.75%, -2.42%, -1.03%. |

So "8 trades, 0 wins, -4.16 USD" is three real losing trades plus five records that should
not count. Three trades say nothing about the strategy either way.

## Decisions for the operator

1. Review and merge patch 0001, or keep the campaign locked out. Until one of those, every
   daily session records "ran, no trade" while the signal is long.
2. Whether the five non-strategy records count toward the paper gate. I would exclude them.

## Not established

- Whether Hetzner campaigns carry the same stale `kill_until`. Any campaign that had three
  losing exits in a row on the old code would.
- What the strategy's exits would have done between 18 August and today.


## Correction, 2026-10-07

I wrote "review and merge patch 0001". That was incomplete. 0001 alone still blocks a
protective exit during the cooldown; in the series that is treated by the next patch, 0002
(`49226798`, "let closing sells through the kill cooldown"). 0001 must not be deployed alone.
See `cooldown_patch_current_base_review_20261007.md` and
`cooldown_protective_combined_review_20261007.md`.

Checked in the series code (`services/execution/strategy_runner.py`): the cooldown exception
for a sell does not look at the sell's size. With `strategy_runner.sell_full_position` off,
the sell uses the configured order quantity, which can exceed the held position. In paper the
engine and ledger reject such a sell as `insufficient_position`, so the result is a refused
exit, not an oversell. `sell_full_position` defaults to on.

The crossover rule stands: nothing here calls for resetting state or forcing an entry.


## Correction, 2026-10-07 (later the same day)

The turns to long listed above (07-26, 08-06, 08-08, 08-18) and the "+21 USD since 18
August" come from the signal as recorded, which before 2026-09-09 was a roughly 20-day SMA.
On a true 200-day SMA of the same daily series the only turn to long was 2026-08-20 at
69,360; a position from there would be +16.22 USD unrealized on 10-07. The three trades in
Finding 2 called "genuine" are old-policy trades, not the corrected strategy. The lockout
finding itself (stale `kill_until`, per-process loop counter) stands.
See `es_laptop_records_identity_correction_20261007.md`.
