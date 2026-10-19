# Multi-symbol next-open simulator core

Role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.

Implements the pure simulation core for the registered multi-symbol baseline,
not the full archive-backed experiment. No archive is fetched or written and no
campaign, account, runtime strategy or canonical parity engine is changed.

Completed candle signals are executed at the next candle open. One fixed quote
notional entry is allowed while flat; insufficient cash refuses instead of
silently resizing. Both legs pay fees and adverse slippage. A remaining long
position is liquidated at the last close, with its cycle contribution and the
terminal event separately identified. Equity is bar-close sampled, not an
intrabar drawdown guarantee. Signal-only exits do not replicate campaign stops.

Inputs reject malformed, nonfinite, negative, duplicate, unaligned, unordered or
gapped candles. Signal evaluation gets detached completed-bar history only,
up to 300 bars, and evidence emission is disabled. Configuration/data hashes
identify supplied inputs, not complete transitive implementation authenticity.

SHOWN: 24 tests passed in 0.27 seconds:

```sh
CBP_STATE_DIR=/private/tmp/next-open-research-20261008 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_next_open_research.py tests/test_frozen_strategy_comparison.py
```

Synthetic tests cover next-open fill versus prior close, two-leg fees, terminal
liquidation, flat cash, fixed-size refusal, malformed archive rows, detached
signal inputs, invalid costs and config/data hash changes. Existing frozen
comparison tests also passed. No historical profitability result was produced.

UNVERIFIED: real preset signal integration in this core, archived input adapter,
explicit chronological split orchestration, immutable resolved preset/code
snapshot, control-arm orchestration, daily/calendar reports, CI/full suite and
independent review. No training/tuning, candidate selection, ranking or promotion
exists in the core. Historical quarantine is not an untouched holdout claim.

Next dependency after acceptance: freeze exact preset configs and wire one
archive-backed segment with strict planned dates, source and hashes. Then run
the bounded basket and report all arms/failures, not just winners.

## Subsequent acceptance and numerical correction

The operator supplied `INDEPENDENTLY_REVIEWED AND ACCEPTED` for the earlier
core. Subsequently received separate GATE review returned INCOMPLETE with a P2:
finite extreme prices could overflow executed price and deduct cash for zero
quantity. The acceptance does not waive that reproduced defect.

Correction rejects nonfinite computed execution/accounting values and zero
executed quantity before accepting a result. Regression tests cover price,
quantity and equity overflow, quantity/gross underflow, plus real-registry smoke
execution for the three registered presets on synthetic flat candles. These
smoke tests show invocation compatibility, not real-market strategy performance.
SHOWN: same two-file isolated selection, 32 passed in 0.25 seconds with
CBP_STATE_DIR=/private/tmp/next-open-correction-20261008. No archive fetch/run.
The numerical correction is READY_FOR_INDEPENDENT_REVIEW; archive orchestration
and economic results remain INCOMPLETE.

Separate GATE subsequently accepted the corrected production core WITH_RISK,
reproducing 32 passed in 0.23 seconds. It found the terminal-underflow test had
a bad timestamp/action count, so it rejected the grid rather than the intended
arithmetic. The test now uses a contiguous four-row grid, four actions, and
requires `invalid_numeric_range`; local rerun: 32 passed in 0.26 seconds.
Production code was unchanged by this test repair; reviewer confirmation of the
repaired test was requested. Core acceptance remains bounded, not study approval.

Separate GATE confirmed the repaired test reaches terminal gross-underflow
arithmetic (one test independently passed); its bounded core acceptance stands.
The subsequent optional nonliquidating phase extension is separately reviewed
with the archive runner and is not implied by that prior acceptance.
