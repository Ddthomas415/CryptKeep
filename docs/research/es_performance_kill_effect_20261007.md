# What the performance kill does to the corrected ES strategy - 2026-10-07

Reviewer: Claude (AUDITOR). Research only, on the frozen archive. Not promotion evidence, not
edge validation. No campaign, state, config or code change.

## Question

The laptop es campaign was locked out by the kill cooldown after three losing exits
(`es_daily_trend_lockout_review_20261007.md`). Is that a one-off, or what the corrected
strategy (SMA200, declared exits) should expect from the same mechanism?

## Method

Same archive, costs and replay as `es_exit_policy_matrix_20261007.md` (3,077 daily rows,
SHA256 `c0d64661...28eb`, 7.5 bps fee, 5 bps slippage, 210-bar warm-up, runner entry rule).
At every exit the replay calls the repo's `evaluate_exit_outcome`, `update_drawdown_state`
and `evaluate_performance_kill` with the default limits the campaign runs with: 3
consecutive losing exits, 10 points on the policy's own measure (a running sum of per-trade
percentage results, not the drawdown of equity), 50-loop cooldown.
Without any kill the replay gives 9,543.47, the matrix's SMA200 cell.

Three treatments of a triggered kill:

- **Master**: the cooldown is an absolute loop number and the loop counter restarts in every
  process. For a campaign that starts a process each day and reads a daily signal, the first
  loops of every later session stay blocked and the signal change is consumed in loop 1.
  Modelled as: after the first trigger no entry is taken again. This is what the laptop shows.
- **Series patch 0001**: the cooldown is a persisted count of blocked loops. Modelled as
  entries blocked on the exit bar and the next N bars, with a blocked change consumed.
  N = 0 when a session has 50 or more loops (the laptop has run 62 since mid-September).

## Results

| Treatment | Closed trades | Net return | Max drawdown | Entries blocked |
|---|---:|---:|---:|---:|
| No kill | 31 | +854.4% | 64.3% | 0 |
| Master (lockout after first trigger) | 3 | +44.3% | 45.2% | 30 |
| Patch 0001, cooldown ends inside the exit session (N = 0) | 31 | +854.4% | 64.3% | 0 |
| Patch 0001, N = 1 | 27 | +1,098.9% | 55.8% | 4 |
| Patch 0001, N = 3 | 26 | +1,046.0% | 58.7% | 5 |
| Patch 0001, N = 5 | 24 | +1,299.7% | 54.6% | 7 |

- The kill would trigger at 17 of the 31 exits. The strategy wins 22.6% of its trades, so
  three losses in a row, or 10 points on the policy's running sum of trade results, is its normal condition.
- The first trigger is the third trade: exit 2020-02-26, on the drawdown rule, after two
  losses. On master the strategy stops there at +44.3%. The next trade it would have taken,
  2020-04-29 to 2021-05-19, is +317.7%.
- With patch 0001 and a short cooldown the blocked entries in this sample happened to be
  whipsaw losers, which is why those rows are higher. That is one path, not a reason to
  want the cooldown: a blocked entry is not offered again until the next cross, and one
  blocked winner of the size above would dominate the result.

## What this means

- The laptop lockout is not an accident of that campaign. On master, any run of the
  corrected strategy is expected to lock itself out at its first kill trigger, early, and
  to stay out. That includes a trial that is working as designed.
- The Hetzner corrected trial has no trades, so it has not reached this yet. Which runner
  code is deployed there is not established here.
- The default kill limits were not written for a low-win-rate trend strategy. Whether they
  should apply to it at all is an operator decision; nothing here changes them.

## Limits

- In-sample, one asset, daily closes, all-cash compounding. Returns are cumulative and come
  from a few long trends.
- "Master" is modelled as a permanent stop. An intraday change of the daily signal late in a
  session could in principle slip through; the laptop record shows none in 90 days.
- The cooldown length in bars depends on loops per session, which is a campaign setting.
- The window ends 2026-06-04.

## Decisions for the operator

1. Review of the cooldown patches (0001, 0002 and the other session's quantity treatment):
   this is the measured cost of leaving master as it is for this strategy.
2. Whether the performance-kill limits (3 losses, 10 points) apply to es_daily_trend.

## Files

`docs/research/es_exit_policy_matrix_20261007/es_performance_kill_effect_20261007.py` and
`.json` (per-trade streak, drawdown and trigger are in the JSON).

## Note added 2026-10-08

Per `shared_rev88_review_20261007.md`: the master row is a modelled scenario (a permanent
lock imposed in the replay), not a measured run of the current runner. The "Max drawdown"
column is the drawdown of equity; the kill's 10-point limit is a different measure.
