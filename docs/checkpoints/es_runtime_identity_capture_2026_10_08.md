# ES runtime identity capture checkpoint

Role: ENGINEER. State: READY_FOR_INDEPENDENT_REVIEW.

This producer-side slice adds opt-in intent metadata, not cohort activation.
No campaign configuration, account, collector, historical evidence or gate
threshold is changed. Protective exits are not conditional on capture success.

Capture is disabled unless `CBP_CAPTURE_EXECUTION_IDENTITY=1`. An explicit
`CBP_EXECUTION_IDENTITY_COHORT_ID` is also required for successful capture.
Neither variable has been enabled by this change. Supported capture is the
resolved `sma_200_trend` daily public-OHLCV path. Unsupported or incomplete
inputs produce a failed-capture marker without suppressing an intent.

The payload records selected resolved signal parameters, entry/exit settings,
sizing, market provenance, provisional paper costs and selected loaded-code
fingerprints. Dynamic quotes and unrelated configuration are excluded.
Fingerprints include Python version and code-object details; they can differ
across runtime versions or paths. They do not cover all transitive dependencies,
global state or closures, and are not signatures or proof of actual execution.
Producer costs are a configuration snapshot, not verified fill-time costs.

SHOWN: 106 targeted tests passed using isolated temporary state:

```sh
CBP_STATE_DIR=/private/tmp/es-identity-tests-20261008 PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest --noconftest -q -p no:cacheprovider tests/test_execution_identity.py tests/test_runtime_execution_identity.py tests/test_strategy_runtime_runner.py tests/test_managed_exit_policy.py
```

The new storage test proves separate queue/order metadata round trips; it
manually transfers metadata and does not prove consumer integration.
UNVERIFIED: enabled runner end-to-end capture, actual fill-cost agreement,
journal persistence, identity-based gate exclusion, CI and deployed behavior.
The full suite was not run. Independent review is requested for this slice.

Next dependency: verify and propagate identity at actual paper-fill logging,
then persist it in the journal and require it in the forward-only analytical
cohort gate. Until those stages are verified, corrected cohort activation is
INCOMPLETE and no profitability or promotion claim follows.

## Acceptance and bounded correction

The operator supplied `INDEPENDENTLY_REVIEWED AND ACCEPTED` for the prior
producer slice. Subsequently received separate review found two P2 items:
unused configured regime controls were mislabeled as effective signal policy,
and enabled-hook behavior lacked targeted tests. That evidence is not waived
by the acceptance phrase.

Correction records only registry-converted SMA/ATR and the regime function's
effective defaults, excluding unused configured controls. New tests exercise
successful actual runner-hook capture and injected configuration failure;
runner-loop permutations retain buy/sell counts, quantities and exit reasons
with capture disabled or returning failure markers. The loop scenarios use
unsupported strategies, so they do not prove successful ES loop integration.
SHOWN: same isolated four-file test selection, 120 passed in 3.27 seconds.
This correction is READY_FOR_INDEPENDENT_REVIEW. No fill integration was added.
