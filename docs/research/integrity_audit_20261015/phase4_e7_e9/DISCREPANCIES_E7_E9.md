recorded 2026-10-15T19:34:18Z (before reading original band/brake code for investigation)
# E7-E9 blind reimplementation: discrepancies recorded BEFORE investigation

Saved = repo result JSON (unchanged). Blind = audit subagent code written from PREREGISTRATION.md + auditor-supplied shared conventions.

## E7 crash brake
- End values, Sharpe, brake weeks (D 11, H 2), PASS checks, DSR (0.835 / 0.561): identical to saved at every reported digit.
- D1: sensitivity pct95 H Sharpe blind 0.870 vs saved 0.869 (rounding-level).
- D2 (spec, not code): prereg says D starts 2020-12-01 "when the BTC brake becomes available"; under its own 365-day rule BTC is available ~2020-09-09; 2020-12-01 fits ETH. Documentation inconsistency in the frozen prereg.
- D3 (spec): prereg H is "2024-01-01 to 2026-10-08" without "first Sunday"; both implementations start H at Sunday 2024-01-07.
- D4: D max drawdown ties exactly (32.77%) for braked and unbraked; the "lower" test fails on a tie. Blind used a 1e-9 tolerance; without it rounding noise could flip check 1. Verdict FAIL either way.

## E8 composite
- Incumbent, hold BTC, 25/25/50: identical. Composite Sharpe/turnover/rebalances/DSR identical at reported precision.
- D5: composite D end blind $38,034 vs saved $38,009.97 (+0.06%) at 0.50%; $33,458 vs $33,422.76 (+0.11%) at 0.90%. Blind scaled traded targets so cash >= 0 on 2 dates (2020-10-26, 2024-02-12). Hypothesis: band/sizing convention. Not yet investigated.
- D6 (spec): prereg does not define how the band interacts with the shared rebalance() sizing, nor turnover.

## E9 band
- D7: blind PRIMARY (cash allowed negative, min -$2,414) D end $54,794 vs saved $53,367.38 (+2.7%); 0.90% D $43,397 vs $42,232.31 (+2.8%); H $1,874 vs $1,867.16.
- D8: blind no-leverage variant: D $53,413.89 (+0.09%), Sharpe 1.6201 vs 1.620, turnover 8.366 vs 8.36; H $1,868.87 (+0.09%).
- Verdict FAIL in all variants (turnover ratio ~0.90-0.91 > 0.75).
- D9 (spec): prereg does not say whether a banded portfolio may go below zero cash. The two blind agents chose differently (E8 capped, E9 primary did not), so the spec admits both.
