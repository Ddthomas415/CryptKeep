# E6 corrected-simulation rule (pre-stated 2026-10-15, BEFORE any corrected run)

Purpose: replace the defective missing-candle handling in E6 (execution at a stale last close). This file was written before any corrected simulation was run or seen.

- **Executable prices only:** a product can be bought or sold only on a day it has a candle, at that day's open, with the registered costs.
- **Held product with no candle on an execution day:** it is not traded. It stays held and is marked at its last close for NAV. The new target weights are applied to the tradable NAV only (NAV minus frozen value). It is sold at the open of the first later execution day on which it has a candle.
- **Never trades again (delisted):** PRIMARY: the frozen position stays valued at its last close to the end of the period; the capital is locked and never redeployed. SENSITIVITY (reported only): value written down to 50%, and to 0, from the first missing day after its last candle.
- **Buy of a product with no candle that day:** skipped; that weight stays in cash.
- **Everything else unchanged:** universe, ranking, lookback, top-5, costs, periods, benchmarks and PASS criteria from PREREGISTRATION.md.
- **Status:** the original E6 verdict (FAIL) is NOT changed by this rerun. The corrected result is reported separately. A PASS here would not count as a pass: the periods were already seen, so it would need a new pre-registration on new data.
- **Implementations:** (1) an independent blind implementation written by an audit subagent from the PREREGISTRATION text + this file; (2) optional cross-check by a minimal patch of a scratch copy of xs_momentum.py. The repo copy of xs_momentum.py is not modified.
