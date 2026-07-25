# Walk-Forward Validation

CryptKeep includes research-only archive-backed walk-forward and bounded
parameter-sweep tooling for strategy evaluation.

Code:

- `services/backtest/walk_forward.py`
- `services/backtest/parameter_sweep.py`
- `scripts/research/run_archive_walk_forward.py`
- `scripts/research/run_archive_parameter_sweep.py`
- `tests/test_backtest_walk_forward.py`
- `tests/test_archive_walk_forward_runner.py`
- `tests/test_archive_parameter_sweep.py`

## Current Scope

- anchored train/test windows over archived OHLCV rows
- complete-archive reads only; incomplete archives fail closed instead of
  falling back to live fetches
- deterministic reuse of the existing parity backtest
- dataset hash, strategy config hash, and source archive metadata on artifacts
- descriptive train/test summaries
- explicit, bounded parameter-grid expansion through the archive-backed
  walk-forward wrapper
- research-only metadata for persisted strategy evidence and strategy-lab
  reporting
- no promotion or live-execution authority

## Current Non-Goals

- no unbounded or background parameter search
- no automatic top-variant adoption
- no auto-promotion
- no use as a promotion gate or live-routing control
- no claim that walk-forward or sweep output proves profitability

## Intended Question

This tooling answers two narrow research questions:

- does the current strategy keep producing acceptable test-window behavior after
  the training window expands?
- do bounded parameter variants improve out-of-sample behavior enough to justify
  separate manual review?

The output is input to review. It is not itself strategy authority.

## Required Before Use In Strategy Decisions

- accepted archive source and dataset hashes
- explicit fee/slippage assumptions for the run
- minimum sample-size and closed-trade review
- comparison against baseline/unconditioned behavior
- review of overfitting risk before top variants influence configs
- separate reviewed config or campaign change before any runtime use

## Executable Guard

`tests/test_walk_forward_research_doc_guard.py` pins the archive-backed scope,
bounded sweep boundary, fail-closed archive requirement, non-goals, and
review-before-use requirements so walk-forward and sweep output cannot silently
become promotion, strategy-selection, or execution authority.
