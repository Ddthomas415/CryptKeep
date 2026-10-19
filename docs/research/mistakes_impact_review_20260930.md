# Mistakes impact review - 2026-09-30

Role: AUDITOR. Scope: current consequences of recorded errors, not new features.

## Current update - 2026-10-01

Read-only GitHub verification: #603 MERGED at 2026-10-01T15:24:57Z as
97c24c8e4884629347a5492ae848133becd9027b. The net-win reporting correction is
published. Deployment remains UNVERIFIED. The earlier publication-gap finding
below is historical, not an open implementation task.

#602 remains OPEN at 5f9129a61aa2e74c222821e50cc1ecf057556e1a. The previous head
below is historical. Diagnostic CI established signal_input_code_mismatch;
cause is not yet established. Do not equate local suite success with CI success.

## Historical publication snapshot - 2026-09-30

GitHub API master: 580ca31ea983af6452a1e02ab8d4b51645e9b43c.
Local HEAD: 620bc8dbe; dirty local fixes must not be confused with publication.

1. **Open publication gap: gross/net summary mismatch.** Ran the published
   strategy_feedback.py function from git against a two-fill fixture: buy 100,
   sell 101, quantity one, fee one per side. Output: net PnL -1, expectancy -1,
   but 100% win rate. Local corrected function reports 0% net-of-fees win rate.
   This reproduces the reporting defect, not a fresh trading loss. Numeric net
   results are separate from the incorrect summary text. Do not declare the
   correction generally delivered while it remains an uncommitted local diff.
   Execution used current local imported analytics dependencies, not an isolated
   full published checkout. Next action: isolate the existing fix/test for review
   and publication, rather than rewrite it or reopen underlying accounting.
2. **Published correction: SMA flat exit.** Master commit 580ca31ea is PR #601,
   preserving SMA exits across temporary blockers. Do not classify it as an
   unimplemented fix. Current host uptake and actual exit execution were not
   checked in this pass. No live/campaign correctness claim follows from merge.
3. **Unmerged correction: completed crossover entry.** PR #602 remains OPEN,
   head fc1f6dfd554fa75ecd64b22d9b92585c133a4ed1, no merge commit. CI sanity and
   CI validate failed; six other reported checks succeeded. It is not current
   master behavior. No CI bypass, activation, or campaign history reset.

## Local verification

`.venv/bin/python -m pytest -q tests/test_strategy_feedback.py tests/test_daily_trend_exit_translation.py tests/test_strategy_runtime_runner.py`

64 passed in 1.58s. This is dirty-working-tree targeted proof, not full-suite,
published-head, or deployed proof. The reporting reproduction used synthetic
fills; no campaign records were modified.

## Conclusions affected

### Follow-up: historical signal-quality defects

Verified on isolated master-based worktree: services/analytics/signal_quality.py
and tests/test_signal_quality.py have no changes relative to 580ca31ea.
Seven tests passed in 0.80s using the local venv Python, pytest -q -p
no:cacheprovider tests/test_signal_quality.py.

SHOWN: default require_matching_provenance=True excludes missing source,
unknown_ohlcv source and mismatched symbol in the regression fixture; only the
matching public-OHLCV record is scored. The previously recorded duplicate
subtraction in short MAE is absent; the test pins the existing reciprocal-price
metric. This does NOT independently validate that metric as entry-notional
short-position PnL, nor validate historical records or every report consumer.

Disposition: the specific historical provenance/default and double-subtraction
defects are corrected in published source. Do not reopen them as new work.
Old affected artifacts and decisions remain unverified; do not reclassify
historical unqualified samples as trustworthy because current code is corrected.

- At the September 30 snapshot, publication was not established; this is
  superseded by the verified October 1 merge above.
- Keep historical campaign and archive entry/exit contracts separate; the
  unmerged crossover must not be retroactively assumed in prior evidence.
- No new profitability verdict follows from these checks. Whether any human
  decision depended on misleading summary text remains UNVERIFIED.

Overall review INCOMPLETE. Earlier currency, provenance, scope-drift and other
documented findings still require affected-artifact tracing. No new runtime
changes, deployment, credential changes or trades in this pass.
