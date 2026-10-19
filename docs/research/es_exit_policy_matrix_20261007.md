# ES exit-policy matrix on the frozen archive - 2026-10-07

Reviewer: Claude (AUDITOR). Research only. Not promotion evidence, not edge validation, no
campaign, state, config or code change. It completes the comparison that
`docs/checkpoints/es_corrected_policy_comparison_protocol_2026_09_08.md` left INCOMPLETE,
within the limits that protocol set.

## Method

- Input: the frozen Coinbase BTC/USD daily archive, 2018-01-01 to 2026-06-04, 3,077
  contiguous rows, SHA256 `c0d64661...28eb` (asserted by the script; same slice as
  `es_sma_archive_results_2026_09_08.md`). Read from `market_raw.sqlite` opened read-only.
- Fixed before running: 210-bar warm-up, 1,000 quote units, 7.5 bps fee and 5 bps slippage
  per side, all-cash sizing, fills at the bar close (the parity engine's conventions).
- The replay mirrors `run_parity_backtest` bar by bar and calls the runner's real exit stack,
  `evaluate_strategy_exit_stack`, once per daily close. Signals come from the strategy
  registry, as in the parity engine.
- Matrix: SMA20 and SMA200, each with the old runner defaults (3% stop, 6% take profit,
  2% trailing stop) and with the declared policy (all zero).
- Entry mode: "transition" is the runner's rule (act only when the decision changes, so
  after a stop or take-profit there is no re-entry until the signal goes flat and long
  again). "Level" is the parity engine's rule (buy whenever long and flat).
- Code: laptop checkout `620bc8dbe`; hashes of the five source files used are in the JSON.

## Validation

With the declared exits, the replay reproduces the parity engine exactly for both periods:
157 and 31 round trips, final equity 3,509.45 and 9,543.47, i.e. the +250.94% and +854.35%
already on record. The old-defaults cells have no independent reference.

## Results (runner entry rule)

| Signal | Exits | Closed trades | Win rate | Net return | Max drawdown | Profit factor | Bars in position |
|---|---|---:|---:|---:|---:|---:|---:|
| SMA200 | declared (none) | 31 | 22.6% | +854.4% | 64.3% | 2.80 | 55.3% |
| SMA200 | old defaults | 35 | 31.4% | +1.3% | 20.4% | 1.02 | 4.5% |
| SMA20 | declared (none) | 157 | 25.5% | +250.9% | 72.9% | 1.21 | 51.0% |
| SMA20 | old defaults | 161 | 37.9% | +54.4% | 32.1% | 1.13 | 18.8% |

Buy and hold from the first tradable bar, same costs: +674.6%.

Exit reasons with the old defaults: SMA200 - 18 trailing stop, 7 stop loss, 7 take profit,
3 SMA flat. SMA20 - 56 trailing stop, 42 stop loss, 41 take profit, 22 SMA flat.

With the parity engine's entry rule instead, the old-defaults cells are +248.0% (SMA200,
348 trades) and +61.5% (SMA20, 370 trades). With declared exits the two entry rules give
identical results.

## What this shows, and what it does not

- The old default exits are what removed the trend from the trend strategy. Under the
  runner's entry rule a 2% trailing stop or 6% take profit ends the position and nothing
  re-enters until the next cross, so SMA200 was in the market on 4.5% of days.
- The configuration the laptop campaign ran before 2026-09-09 (SMA20-like signal, old
  exits) is the +54.4% row. The corrected strategy is the +854.4% row. They are different
  strategies; evidence from one says nothing about the other.
- The crossover-only entry rule costs nothing while a run is continuous: with declared
  exits it gives the same trades as the level rule. It costs only when a run starts, or is
  locked out, while the signal is already long. SMA200 was long on 55% of days, so a start
  at an arbitrary date had about that chance of beginning inside a long phase.
- None of this is evidence of an edge. It is one asset, one in-sample path, cumulative
  returns dominated by a few long trends (7 winning trades of 31), with a 64% drawdown.

## Limits

- Exits are evaluated on daily closes only. Intraday crossings of a stop are not
  recoverable from daily bars and are not modelled.
- The old 60-count time stop is omitted: it counted runner loops, not bars.
- BTC/USD data stands in for BTC/USDT. Costs are assumptions, not measured.
- All-cash compounding is not the campaign's fixed 0.001 BTC size.
- The window ends 2026-06-04; the June-October period in the laptop notes is outside it.

## Files

`docs/research/es_exit_policy_matrix_20261007/`: the script and its JSON output. To rerun:
`python3 -B es_exit_policy_matrix_20261007.py /path/to/crypto-bot-pro` with `CBP_STATE_DIR`
pointing at an empty temporary directory. It asserts the archive hash and writes only to
standard output.
