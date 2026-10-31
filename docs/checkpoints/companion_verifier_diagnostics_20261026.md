# Offline verifier diagnostics repair, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, corrected offline scope only.
Runtime INCOMPLETE. No service changes, credential access or live query.

## Objective

The failed V6g query passed client normalization but its verifier returned an
undifferentiated all-false result. Add fixed diagnostic codes without changing
the evidence required for acceptance or assuming the historical cause.

Artifacts: docs/review_artifacts/companion_verifier_diagnostics_20261026/.
prechange.tar preserves this turn's exact baseline; repair.diff isolates this
change from older dirty-worktree edits. report.json records before/after hashes,
preserved guard/witness/archive hashes and parent-reported test results. Existing
V6g receipts, diagnosis and reviews are unchanged historical evidence.
The first independent review rejected two protocol gaps (VD-01/VD-02).
Its source/test/report/diff checkpoint is preserved in rejected_v1.tar and the
review in independent_review.json; the current revision corrects only those gaps.

## Contract and changes

- companion_evidence_checks.py adds a diagnostic evaluator/script whose wire
  result has exactly checks (the same five literal Booleans) and diagnostic
  (two fixed-enum strings: stage and code). No exception text/class, payload,
  body, URL, database rows or credentials are returned. Codes are ok, rejected,
  error and deadline. Stage identifies a failing verification group, not the
  exact predicate or value. Deadline identifies the interrupted stage; it is
  not a semantic verdict. Legacy evaluate()/EVIDENCE_SCRIPT retain five Booleans.
- companion_runtime_adapter.py adds verify_evidence_diagnostic. It strictly
  validates the envelope and retains the same private stdin, output bound and
  ten-second parent call. Existing verify_evidence returns only its checks,
  preserving the older controller's interface. It does not retry or use a second
  wire request when validation fails.
  Duplicate JSON members at every object depth are refused before validation,
  so later values cannot overwrite failed checks or diagnostic fields.
- companion_installer.py selects the diagnostic-capable method once when
  present, otherwise retains legacy-adapter compatibility. A diagnostic-call
  failure never falls back or retries through the old method. Returned JSON
  carries diagnostics across the bounded process channel; instance attributes
  would not survive that channel. The installer records only validated codes.
  Malformed envelopes are rejected and recorded with fixed parent_boundary/
  invalid labels. Transport/outer-timeout ambiguity is honestly unavailable;
  legacy adapters are labelled legacy_result/unavailable.
  A selected diagnostic method must return its envelope: bare checks cannot
  silently downgrade to the legacy interface. Explicit legacy-only callers
  still accept the original five-Boolean mapping.

Success still requires exactly five Boolean true values. Diagnostic ok cannot
override any false/invalid check. Current production adapter uses the diagnostic
wire; legacy compatibility is not acceptance of a bare remote wire result.
Existing predicates, registered question, SQL, read-only transaction/statement
timeout, archive and witnesses are unchanged.

The dedicated eight-second alarm still covers input and DB teardown and hard
exits; the diagnostic handler writes precomputed fixed bytes only. An occupied
timer is refused without modification. Ordinary evaluation failures retain the
first failed group if subsequent teardown fails. A deadline instead reports its
current interrupted stage, which can differ from an earlier semantic failure.

## Verification

VERIFIED_ENV local synthetic tests, not installed/runtime proof:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_companion_verifier_diagnostics.py tests/test_companion_evidence_checks.py tests/test_companion_runtime_adapter.py tests/test_companion_archive_probe_scope.py tests/test_companion_running_update.py tests/test_companion_existing_controller.py
```

SHOWN: revised six-file run 397 passed in 20.39 seconds, 12 existing FastAPI
deprecation warnings. 52 new cases cover first-group codes, import-independent input failures, archive/
query/lineage/teardown/timer failure, no private text, malformed/inconsistent
envelopes, all-true gate integrity, legacy controller compatibility and no retry.
The real bounded JSON executor preserves diagnostics. An isolated stdlib-only
synthetic child proves the diagnostic eight-second hard exit; it loads no app,
settings, SDK or DB. The previous legacy alarm test still passes. The existing
predicate ASTs and SQL compare equal to the preserved baseline.

The original 389-pass run did not cover the two independent findings. Eight
additional regression cases gave 7 failed / 1 passed against that rejected code,
then all passed with the correction: diagnostic bare-check refusal (true/false),
explicit legacy success, and duplicate checks/diagnostic/check/stage/code keys.
Each malformed wire makes one bounded command, with no retry or fallback.

Early new-test run found two failures (30 passed): cursor cleanup was labelled
db_query, and the teardown fixture failed before the intended later stage.
Added a cleanup stage marker and distinct late-teardown fixture; targeted rerun
passed. Caller search found the older controller's five-Boolean interface before
handoff; the separate diagnostic method preserves it. No rejected runtime input
or acceptance threshold was adjusted to make these tests pass.

Full suite not run. No Docker/native/service commands, token access, DB/query,
market-data, trading, scheduler, account or deployment actions occurred. Stdlib
test child processes are synthetic offline verification, not live runtime.

## Handoff and remaining limits

Independent review v2 accepted the two corrected boundaries with no blockers,
reproducing 397 tests / 12 existing warnings in 20.06 seconds and independent
malformed-wire/downgrade challenges. Parent read the complete review and checked
all 18 bound hashes before this documentation closeout. See
independent_review_v2.json in the artifact folder. The first review stays
REJECTED for its preserved version; report.json and repair.diff remain frozen
pre-review implementation records. The review-bound checkpoint hash refers to
its pre-closeout version. No reviewed source, test or evidence artifact changed.

This does not identify the prior V6g failure or prove the next query will pass.
Old source-bound runtime packets no longer bind the three changed production
files; do not reuse them or reset consumed attempts. Operational planning and
any new diagnostic/live run require separate authorization and current inputs.

Offline objective complete. Next operational prerequisite is a fresh source-bound
plan for the changed verifier/adapter/installer, not reuse of consumed V6g IDs
or authorization. This acceptance does not grant preparation/startup/cutover/query
authority or establish current service health.
