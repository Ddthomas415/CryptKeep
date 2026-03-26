# Mean Reversion RSI Research Note (2026-03-26)

## Scope

Question:

- what should happen next for `mean_reversion_rsi` given the current repo evidence?

This note records the current evidence position without changing presets.

## Current Evaluation Position

Current decision source:

- [decision_record_2026-03-26.md](/Users/baitus/Downloads/crypto-bot-pro/docs/strategies/decision_record_2026-03-26.md)

Current status in that record:

- decision: `freeze`
- evidence status: `insufficient`
- aggregate deterministic result: `2 / 8` active windows, `0` closed trades
- persisted paper history: `46` closed trades, `-2.55` net realized PnL, `2.2%` win rate across `92` fills

## Deterministic Window Read

The built-in synthetic evidence windows now produce limited participation for `mean_reversion_rsi`, but they still do not produce realized closed-trade evidence.

Observed from the persisted evidence artifact:

- active windows: `2 / 8`
- closed trades: `0`
- positive windows: `1 / 8`
- aggregate net return after costs: `+0.00%`
- best window: `low_vol_fee_bleed`
- worst window: `false_breakout_whipsaw`

Interpretation:

- the current deterministic window set is not proving this strategy viable
- the added `low_vol_fee_bleed` window is a better structural match for the observed low-vol paper losses
- but the deterministic pack still is not producing realized closed trades that would justify tuning from synthetic evidence alone

## Persisted Paper-History Read

Paper-history source:

- `/Users/baitus/Downloads/crypto-bot-pro/.cbp_state/data/trade_journal.sqlite`

Repo-native FIFO analytics summary:

- fills: `92`
- closed trades: `46`
- wins: `1`
- losses: `45`
- win rate: `2.17%`
- gross realized PnL: `-1.0139812774998709`
- total fees: `1.5389794117481255`
- net realized PnL: `-2.552960689247996`

Per-symbol breakdown:

- `BTC/USD`
  - closed trades: `14`
  - win rate: `0.0%`
  - net realized PnL: `-2.4390982508105`
- `ETH/USD`
  - closed trades: `21`
  - win rate: `4.76%`
  - net realized PnL: `-0.11148818220062084`
- `SOL/USD`
  - closed trades: `11`
  - win rate: `0.0%`
  - net realized PnL: `-0.0023742562368749285`

## Hypothesis Alignment

The current hypothesis in [hypotheses.py](/Users/baitus/Downloads/crypto-bot-pro/services/strategies/hypotheses.py) says this strategy is expected to fail in:

- `bear`
- `bull`
- `high_vol`
- `event_trend`

What can be said safely from current evidence:

- the live paper sample is strongly negative
- the deterministic pack now captures a small amount of low-vol participation, but still does not reproduce a convincing realized-loss analogue to the paper history
- the next step should be hypothesis and evaluation redesign, not threshold tuning

What should **not** be claimed from current evidence:

- that the strategy concept is permanently disproven
- that a specific parameter tweak will fix it
- that the observed paper losses have already been mapped conclusively to one named failure regime

## Decision

Do not tune `mean_reversion_rsi` presets yet.

Keep:

- current preset unchanged
- current decision at `freeze`

Reason:

- the paper sample is large enough to show the current implementation is performing poorly
- the deterministic window set is better than it was before the low-vol fee-bleed addition, but it is still not strong enough to justify preset tuning
- changing thresholds before fixing the evaluation mismatch would be guesswork

## Recommended Follow-up

If work resumes on this strategy, do one of these first:

- strengthen the deterministic pack so low-vol fee-bleed and adverse trend windows produce more diagnostic realized participation
- run a dedicated regime study that compares paper-loss periods against the hypothesis failure regimes

Not recommended now:

- shortening RSI thresholds or moving-average lengths on the current evidence alone
- spending more paper runtime on the unchanged preset without a clearer regime question
