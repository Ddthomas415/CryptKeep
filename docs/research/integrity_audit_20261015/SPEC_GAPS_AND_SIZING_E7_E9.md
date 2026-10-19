# E7-E9 independent implementations: sizing convention, shared assumptions, specification gaps (2026-10-15)

New file. Registered verdicts (E7 FAIL, E8 FAIL, E9 FAIL), frozen pre-registrations and registered results are unchanged.
Outputs: `phase4_e7_e9/` (from `phase4_e7_e9_20261015.tar.gz`; inner `SHA256SUMS`).

## Verified results (reported by audit-subagent code, rerun/compared by me)
- E7: blind code reproduces registered end values, brake weeks (D 11, H 2) and DSR (0.835 / 0.561) at every reported digit; one sensitivity Sharpe differs by 0.001 (rounding).
- E8: composite D end +0.06% (0.50%) / +0.11% (0.90%) vs registered; Sharpe, turnover, rebalance counts, DSR identical at reported precision.
- E9: blind primary (cash allowed negative, min -$2,414) D +2.7%; blind no-leverage variant D +0.09%.
- E9 diagnostic (`phase4_e7_e9/e9_diag_open_band.py`, a modified copy of the blind code): measuring band weights at the execution open instead of the decision close changes nothing; switching to the original's sizing rule reproduces registered E9 to the cent (D $53,367.38 at 0.50%, $42,232.31 at 0.90%; H $1,867.16; incumbent $42,583.31).

## E9/E8 trade-sizing rule used by the registered code (documented, not endorsed)
At an execution open: NAV = cash + held value at opens. Assets whose |target - current weight| >= band are "moved". Wanted value = target weight x pre-cost NAV. The sub-account = cash + value of moved assets; if the wanted total exceeds it, all wanted values are scaled down proportionally (no leverage, cash never negative). The shared `rebalance()` helper then solves post-cost equity within the sub-account and sets moved assets to their scaled weights of it. Unmoved assets keep their units.
- **Evidence status:** the cent-level match shows this convention explains the numerical gap (verified). It does NOT show the convention is the right one; the pre-registrations do not specify it, and other conventions are equally consistent with their text.

## Shared assumptions (supplied to the blind implementations; NOT tested by the reproduction)
Candidate formula and vol30 (population stdev x sqrt(365)); post-cost bisection sizing; NAV start point and daily marking; Sharpe and drawdown definitions; turnover = traded notional / NAV per year; benchmark timing; DSR formula and V = 0.0004636; band "current weight" definition.

## Specification gaps in the frozen pre-registrations (to be specified before any new confirmatory test; frozen texts NOT changed)
- E8/E9: sizing of banded trades and whether cash may go negative (allowed conventions move E9 D by up to 2.7%).
- E8/E9: turnover definition.
- E7: D start stated as "when the BTC brake becomes available" (2020-12-01) but its own 365-day rule makes BTC available ~2020-09-09; the date fits ETH.
- E7: H start lacks "first Sunday" wording (both implementations used 2024-01-07).
- E7: tie handling for "lower drawdown" (D drawdowns tie exactly at 32.77%; check fails on a tie).
None of these changes a verdict: E9 fails on turnover (0.90-0.91x vs 0.75x) under every convention, E8 on H Sharpe, E7 on D drawdown.

## Hypotheses (not verified)
- E8's 0.06-0.11% residual has the same cause as E9's (same simulator); not tested.

## Correction to a previously reported hash
The first `phase4/SHA256SUMS` (reported as e4c9fce0...) listed itself, so its own line could never verify. It was regenerated without the self-entry (5a5d6acb...) before archiving; all eight data/code entries verified unchanged. The invalid version is not archived.
