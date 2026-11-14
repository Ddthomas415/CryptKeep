# Exit-unblocked variants: measured result (Claude, 2026-11-14T18:41Z; self-checked, Codex to verify)

Bot relation: BOT_RULES for arm R (the bot's signal functions and exit stack, modelled with the runner's entry latch);
arm S is signal-only. Offline replay of saved data; no production code, preset or configuration changed; no network.
Owner direction: "provide support on the tasks that can help codex with the workload" (2026-11-14). This is the
measurement half of engineering item 4 (spec: `README.md` sections 3-4). Codex's remaining half is the production
parameter, presets and tests, if the owner still wants them after reading this.

## How the variant was produced without touching production code
Each default signal function reports its raw decision through the existing `observer` hook before its filter block
(`breakout_donchian.py` 45-49, `ema_cross.py` 94-98, `mean_reversion_rsi.py` 43-47). Variant action = `sell` when the
raw action is `sell`, otherwise the filtered action. That is exactly spec section 2 (sells bypass every post-decision
filter, buys unchanged). `exit_variants_replay.py` (sha256 ef7397c9e1a88b32…) copies the simulation, exit-stack walk
and metrics from `exit_parity_audit_20261031/exit_parity_replay.py`; its default arm S reproduces all 15 saved baseline
trade lists (coin x strategy) to 1e-9 in price and 1e-6 in per-trade net (`validation_default_S_vs_saved`, 15 of 15).

Data: `research/multisymbol_baseline_v1` (OKX 1h; BTC, ETH, SOL, ADA, XRP; 2026-01-01 to 09-30). $100 per entry,
5 bps slippage per side, fees 25 / 50 / 60 bps per side. Runner exit stack: stop 3%, trailing 2%, take-profit 6%,
60 bars (code defaults). Outputs: `exit_variants_result.json` (6ae2bd6f9b9972db…), `exit_variants_trades.csv`
(895874c61db0e29c…, 2,715 trades).

## Result (all five coins summed; $ before fees and net at 50 bps per side)

Bars on which the default produced a raw sell that a filter turned into hold: breakout 109, EMA cross 370, mean
reversion 1,705 (bar counts, not trades).

| Arm | Strategy | Default trades / before fee / net50 | Variant trades / before fee / net50 | Variant minus default (before fee / net50) |
|---|---|---|---|---|
| S signal only | breakout | 310 / +139.08 / -171.61 | 318 / +127.83 / -190.81 | -11.25 / -19.20 |
| S signal only | EMA cross | 129 / +45.13 / -84.09 | 206 / +63.90 / -142.42 | +18.77 / -58.33 |
| S signal only | mean reversion | 29 / -147.71 / -175.97 | 53 / -142.88 / -195.16 | +4.83 / -19.19 |
| R runner rules | breakout | 543 / +140.32 / -403.38 | 543 / +141.39 / -402.32 | +1.07 / +1.06 |
| R runner rules | EMA cross | 204 / +38.04 / -166.15 | 206 / +42.81 / -163.40 | +4.77 / +2.75 |
| R runner rules | mean reversion | 87 / -35.79 / -122.61 | 87 / -33.81 / -120.64 | +1.98 / +1.97 |

Net at 25 bps (maker) and 60 bps are in the JSON; the sign of every difference is the same at all three fee levels.

## Reading
- **Under the bot's own rules (arm R) the variant changes almost nothing:** +$1 to +$3 per strategy over nine months
  and five coins, with the same or nearly the same trade count. The runner's exit stack (trailing 2% above all: 465 of
  543 breakout exits, 163 of 206 EMA, 78 of 87 mean reversion) closes positions long before a filtered signal sell
  would have mattered. Signal sells are 15, 20 and 7 of the exits.
- **Signal-only (arm S) the variant trades more and loses more after fees** in all three strategies. Before fees, EMA
  cross (+$18.77) and mean reversion (+$4.83) improve as the 2026-10-30 diagnosis predicted in direction (its $28 and
  $65 were first-blocked-signal estimates later marked not established); breakout worsens (-$11.25), as predicted. The
  extra round trips cost more in fees than the earlier exits save, at every fee level tested.
- **Pre-registered expectation (spec section 3, "net results at least as good"): not met** in arm S for any strategy;
  met trivially in arm R (differences of $1-3 on losses of $120-400).
- All six configurations lose after fees in both arms, as the failure diagnosis and exit-parity audit found.

## What this does and does not establish
- It measures the one variant the owner approved on 2026-10-30 (sells bypass the entry filters, nothing else changed),
  on the same data and cost model as the diagnosis, including the bot's exit stack. It does not test other exits, other
  parameters or other data.
- It is in-sample descriptive history, not a forward test. Dollar amounts are per $100 trade; signs and ratios are the
  point.
- Self-checked. Codex can verify by re-running the script (about 90 s with numpy) and by checking the observer logic
  against the three signal functions.

## Implication for engineering item 4 (owner decides; nothing deprioritised by this note)
The production change (parameter, three presets, tests) would make the bot able to run a configuration whose measured
effect under the bot's rules is about +$1 to +$3 per $100-per-trade strategy over nine months, on strategies that lose
$120-400 after fees. The question the item was approved to answer is answered by this replay; building the presets adds
the ability to run the variant on paper, not new information. Options: (a) Codex builds it anyway as approved; (b) the
owner closes item 4 with this result recorded; (c) the owner redirects the item to the exit stack itself (the trailing 2%
that ends 79-90% of trades (465 of 543, 163 of 206, 78 of 87)), which the exit-parity audit flagged and which this replay did not test.
