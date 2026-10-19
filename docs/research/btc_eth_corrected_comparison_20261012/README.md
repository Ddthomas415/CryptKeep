# Corrected BTC/ETH trend comparison, 2026-10-12 (status: CANDIDATE, not established)

**Simulator:** the already reviewed corrected harness (`scripts/research/rerun_frozen_stress.py`, hash-checked).
- Decide at the Sunday close, trade at the next day's open.
- Refuses non-contiguous data. BTC/ETH have zero missing days.
- Reproduces the stored `stress_corrected_v1.json` results exactly.

**Rule:** frozen, with no parameter changes. Every strategy and benchmark pays the same fee + 0.05% slippage per side, including entry.

**Files:** script `compare.py` (sha256 6cb61b52...); result `comparison_result.json`.

## $1,000, 0.50% fee (observed taker tier). Sharpe and max drawdown in brackets

| Period | Trend rule | Matched mix: BTC and ETH split evenly at the rule's own average exposure, rest cash (hindsight) | 25% BTC / 25% ETH / 50% cash | Hold BTC | Cash |
|---|---|---|---|---|---|
| A 2016-08..2019 | $5,555 (1.49, 52%) | $4,014 (1.43, 50%) | $5,894 (1.42, 61%) | $11,782 (1.30, 84%) | $1,000 |
| B 2020..2023 | $9,920 (1.70, 33%) | $3,832 (1.17, 45%) | $4,268 (1.17, 49%) | $5,862 (1.00, 77%) | $1,000 |
| C 2024..2026-10 | $1,780 (0.82, 32%) | $1,309 (0.50, 34%) | $1,320 (0.50, 36%) | $1,837 (0.70, 53%) | $1,000 |
| 2018-01..2026-10 | $13,434 (1.01, 52%) | $3,487 (0.63, 55%) | $4,023 (0.63, 61%) | $6,027 (0.64, 81%) | $1,000 |

**At 1.2% (the registered stress fee):** the rule falls below both fixed mixes on Sharpe in A, and below BTC on Sharpe in C. The registered REJECT verdict at 1.2% stands.

**Benchmark labels:** neither mix is fully invested.
- "Matched mix" holds BTC and ETH in equal halves of the rule's own average invested share (about 37-48% depending on period). The rest is cash. It is rebalanced weekly.
- "25/25/50" is 25% BTC, 25% ETH and 50% cash, rebalanced weekly. It is not a fully invested BTC/ETH portfolio.

**Initialization exception (not identical to the live tracker):**
- The harness makes its FIRST decision at the close of each period's starting day, whatever the weekday. All later decisions are on Sunday closes.
- The tested periods start on: A Mon 2016-08-01; B Wed 2020-01-01; C Mon 2024-01-01; FULL Mon 2016-08-01; 2018 Mon 2018-01-01. Each therefore has one non-Sunday initial decision.
- Tracker v2 initializes differently: it holds cash until the first Sunday close on or after its start date, then follows Sundays only.
- The v2 parity test therefore compares the two only on windows that start on a Sunday close, where the rules coincide.

## Reading
- **At 0.5%:** the rule has a higher Sharpe than BTC and both fixed mixes in every period, and a smaller worst drop than BTC in every period.
  - It beats BTC's ending value in B and from 2018, but not in A or C.
- **Status:** a CANDIDATE.
  - These are in-sample periods for a rule chosen after a search.
  - The robustness pass at 0.5% is exploratory.
  - The result depends on costs.
  - The DSR shows no return edge over BTC since 2016.
- **Corrects `xs_momentum_20261012`:** the $10,323 (2018 start) figure there came from a different simulator that filled missing candles with the last close.
  - This harness gives $13,434 at 0.5% + 0.05% slippage, and $7,090 at 1.2%.
  - The difference also reflects a different start day and slippage assumption.
- **Economics:** this table is not an income forecast.
  - A 23%/yr rate (period C) on $1,000 is about $230/yr before tax; a 34%/yr rate is about $340/yr.
  - The ~$240/yr server cost comparison depends on which period is assumed and on the actual bill. It must be stated with both, not as a one-line verdict.
