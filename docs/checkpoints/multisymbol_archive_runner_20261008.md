# Frozen strategy snapshots and read-only archive phases

Implementation role: ENGINEER. Risk: HIGH. Separate GATE: ACCEPTED_WITH_RISK.

Operator decision: **Carry cash and positions forward** across discovery,
validation and final historical segments. Registered plan amended explicitly
before data evaluation; no prior economic results were produced or retuned.

Frozen file: `research/multisymbol_baseline_v1/strategies.snapshot.json` stores
three exact preset signal blocks, plan hash, selected source hashes, commit
context and dirty-checkout disclosure. Source/config identity is based on file
content, not an assumption that HEAD describes this dirty checkout. Selected
hashes are not complete transitive implementation attestation.

`scripts/research/run_multisymbol_baseline.py` defaults to coverage-only. It
checks the frozen plan/source contract and reads exact OKX spot hourly rows
using SQLite read-only URI mode. It refuses wrong-market, incomplete, malformed
or misaligned data without normalization, substitution, fetching or repair.
Output is exclusively created; prior output cannot be overwritten.

Explicit `--simulate` replays the continuous account prefix through the selected
phase endpoint using fixed frozen settings. Every phase starts simulation at
the original evaluation start, not a fresh phase account. Intermediate splits
do not liquidate; only the final end liquidates. Phase return is ending equity
minus equity at the preceding bar close. Cumulative equity, fees, exposure,
trade count and drawdown are visibly labeled prefix metrics, not falsely
reported as phase-only metrics. Open-position equity includes unrealized PnL.
Calendar summaries, phase-specific cycle statistics and candidate ranking are
not implemented in this slice. Each arm is independent, not an aggregate
portfolio. Historical final segment remains exploratory, not assured untouched.

SHOWN: 38 isolated tests passed in 0.37 seconds, including real synthetic SQLite
reads, file preservation, exact dates/market selection, missing-symbol reporting,
source/plan drift refusal, no-signal preflight and carried cash/positions:

```sh
CBP_STATE_DIR=/private/tmp/multisymbol-runner-tests-20261008 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_multisymbol_archive_runner.py tests/test_next_open_research.py tests/test_frozen_strategy_comparison.py
```

SHOWN laptop discovery preflight: exit 2 (expected incomplete archive), all five
symbols INCOMPLETE. Artifact:
`research/multisymbol_baseline_v1/archive_preflight_20261008.json`.
No strategy simulation was requested. Existing local data includes other
venue/timeframe combinations; none were silently borrowed.

No campaign/config/account/service/credential change or historical evidence
rewrite. No economic result or promotion claim. UNVERIFIED: full market study,
complete dependency hashing, full suite/CI/deployment, public-data availability
and cost realism. Next after independent acceptance: bounded public archive
ingestion for the exact registered markets/date grid, then discovery execution
and report completion. No new background collector is required.

Separate GATE independently reproduced 38 passed in 0.33 seconds with no blocker.
Accepted limits: separate phase runs assume historical prefixes stay unchanged;
cross-run prefix consistency is not yet enforced. Freeze/check those prefixes
before relying on cross-phase economic comparisons. Exclusive output creation
is not atomic crash-safe publication. The reviewer did not rerun laptop preflight
and treats that operator-surface result as CLAIMED from this thread's command.
Acceptance covers code/tests only, not a full study or deployment.
