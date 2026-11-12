# Independent R4 Hourly-Candle GATE

Disposition: **REJECTED** for the frozen nine-file candidate: one demonstrated within-scope P1 blocker.
Active role: GATE, separate from implementation author. Risk: HIGH. Review stopped at the blocker.
Bot relation: BOT_RULES; actual runtime configuration, profile activation and host state NOT checked.
Latest task-card/work-log and scoped git status checked: **2026-11-04T02:15:20Z**.

## Blocking Finding

**[P1] New diagnostic persistence can carry a buy across its deadline without another TTL verdict.**
SHOWN at `storage/paper_trading_sqlite.py:818`, specifically the new `_set_state_conn` call at line 823.
The canonical age check samples `now_ts` at line 809, after cache assessment but before diagnostic
serialization/persistence. Successful diagnostic persistence is followed by fill accounting without
another age check. The fill timestamp also retains the earlier `now_ts` at line 833.

Concrete independent regression:
`independent_review/test_probes.py::test_new_diagnostic_write_crossing_ttl_must_not_fill`.
It uses the existing isolated real-cache/engine/SQLite fixture, a valid sixty-hour public cache, the
enabled profile and a real submitted buy. At age 119 seconds the pre-fill and post-cache age checks
pass. The wrapper around only the newly added diagnostic write advances the injected clock to age
121 seconds and performs the original SQLite write successfully. Evaluation then reports **filled=1**,
with a real fill and filled order, instead of expiry/no accounting. Its fill evidence timestamp is
`2026-11-04T12:11:59+00:00` while the injected current time is `2026-11-04T12:12:01+00:00`.
The required 120-second deadline has been crossed. The probe fails on `assert evaluated['filled'] == 0`.

This is a deterministic synthetic I/O-delay model, not a claim that a real host was observed stalling
or trading. No production function or cache verdict was replaced: only the new diagnostic writer
boundary was wrapped to advance the supported test clock. Actual ledger fill/accounting code ran.
The failing probe is preserved as a regression requirement, not altered to accept the late fill.

Cause: **engineering defect / entry implementation**, with a verification gap around delay in the
new post-verdict write. Moving expiry before diagnostics fixes O-56's already-expired/write-failure
case, but does not prove the new write cannot make the accepted age verdict stale. This finding
narrows the candidate README's statement that no late fill is authorized by the new data check.
The existing O-56/O-57 entries remain recorded pre-acceptance corrections; the worker's four initial
TTL-diagnostic failures remain CLAIMED because their original artifact was not preserved.

Smallest correction proposed within the authorized one-blocker-correction budget: retain the
pre-diagnostic expiry/fence precedence, and resample/revalidate canonical buy age after successful
diagnostic work and before proceeding to fill accounting; use the updated time for fill evidence.
Do not simply move the only check below a diagnostic operation that may fail. Preserve unresolved
safe failure, sell bypass, terminal precedence and the existing four O-56 cases. No implementation
was performed here. A correction must be resealed and independently reviewed, not self-approved.

## Evidence And Completed Checks

SHOWN: all nine current and nine before manifest hashes matched. The five existing production
baselines came from `before/`, the provenance test baseline from `git show HEAD:...`, and the three
new files from empty content, exactly as declared by `seal.py`. The independent reconstruction of
the complete incremental diff matched `stage.diff` byte-for-byte. Final hashes still matched after
the tests; no reviewed source or original artifact changed.

```text
stage.diff  f6069d5edcdb67c37e9eabe16f2e6ef0b3d7bfb4503ec86704d67b6c4eecf07c
hashes.json 82270272b22a9f7b66ee6d19d527fbf8046b894ae4ba58e6ec5b5f0a9fab8a83
```

VERIFIED_ENV: local Python 3.12, scrubbed environment, temporary state/SQLite, plugin autoload off,
no bytecode or pytest-cache writes. Commands ran from the repository root with this prefix and a
distinct STATE under `/private/tmp/cbp-candle-independent-*` per invocation:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp PYTHONDONTWRITEBYTECODE=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_STATE_DIR=STATE \
  CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider
```

- SHOWN: `tests/test_hourly_candle_quality.py tests/test_paper_candle_fill_boundary.py tests/test_ohlcv_snapshot_provenance.py tests/test_runner_decision_capture.py tests/test_runner_decision_kernel.py --tb=short`
  -> **199 passed in 9.42s**, no failures/errors/skips.
- SHOWN: `docs/review_artifacts/paper_candle_freshness_r4_20261103/independent_review/test_probes.py --tb=short`
  -> **1 failed, 4 passed in 1.00s**. The failure is the P1 above. Passing probes verify the nine-file
  seal, active assessor alias and module constant in loaded identity, and rejection of a colliding
  cache filename whose envelope identifies another symbol. No further probes were added after failure.
- SHOWN: prefix with `CBP_CANDLE_BEFORE_ROOT=docs/review_artifacts/paper_candle_freshness_r4_20261103/before`,
  `tests/test_hourly_candle_quality.py -k 'enabled_profile_refuses or fresh_at_submit' --tb=line`
  -> **4 failed, 40 deselected in 0.42s**, as expected: three old submissions accept bad candles,
  and one old fill accepts a newly gapped cache. The AST fixture loads the original methods and its
  shim drops only the new keyword; these are behavior failures, not import/API mismatch failures.
- SHOWN receipt inspection only: author's `consolidated.txt` records **839 passed in 29.96s** across
  seventeen files. That selection and a broad suite were not rerun; this review does not certify them.

Favourable bounded evidence is retained despite rejection. The focused tests exercise exact
300-second grace and sixty-hour windows; forming-versus-complete diagnostics; invalid/missing/gapped
rows and malformed clocks; cache identity/source/size and unsafe venue rejection; actual submission
and serialized fill; canonical account/market under lock; invalid policy; disabled-default and sell
isolation, including the pending protective R12 sell; terminal/fence precedence; evidence-write rollback;
ordinary queued refusal/alert handling; safe diagnostic projection and existing decision replay.
The new diagnostic is observational rather than a changed strategy signal rule in the inspected diff.
These passing checks do not erase the independently demonstrated deadline gap.

## Status And Limits

DONE: independent seal/source inspection, focused current/before checks, a concrete failing regression,
and bounded source GATE disposition. Cache assessment, source identity, sell/default isolation and
capture paths have the focused evidence described above, not blanket system acceptance.

PARTLY DONE: the serialized buy boundary. It checks candle data under the canonical writer lock and
checks TTL after cache reading, but does not retain deadline correctness across its newly introduced
successful diagnostic write. This candidate does not satisfy the preserved buy-age requirement.

NOT DONE: source acceptance of this candidate, blocker correction, runtime activation/configuration,
full R4 quote age/completeness/fill provenance, actual coverage, host capacity/cadence/delivery,
commissioning, aggregate operational safety or economics. No profile activation or trading permission
is inferred. The earlier account-stage human acceptance was not reopened or upgraded.

Evidence needed for acceptance: intact corrected seal and current focused tests, this failing probe
passing without late accounting, preserved pre-diagnostic expiry/evidence-failure behavior and separate
review of the bounded correction. No broader architecture or new strategy is proposed.

Inspected: applicable AGENTS rules already read in this review chat; current PROJECT_STATE item 2 and
O-56/O-57; latest hourly-candle task card; artifact README/diff/manifest/seal and receipts; affected
source portions of all six production files; cache path/writer/provenance reader, pure assessor, actual
serialized fill/TTL/accounting path, runner diagnostic binding/capture projection and code fingerprint;
and the focused tests and their synthetic fixtures. Before bytes were checked mechanically against
the manifest/diff, not treated as a complete historical tree. Existing dirty work was not reverted.

Not inspected: private/runtime configuration, credentials/accounts, actual cache/status files or
exchange responses, running processes, services, schedules, host state, delivery, backtests or market
economic results. No network or operational action occurred. Source plus synthetic integration evidence
does not establish current bot behavior; **current/host/economic readiness remains UNVERIFIED / INCOMPLETE**.
Full runner trading rules and broader R4 were not audited. Investigation stopped at the concrete blocker.

Assumption for the counterexample: the new synchronous diagnostic write may consume time across
the existing buy deadline; a two-second delay is injected, not measured. No assumption about actual
deployment/profile activation or account state is needed. Cache labels remain producer assertions,
and a file read is not a cross-filesystem transaction or interruptible I/O deadline.

What could overturn rejection: a corrected sealed candidate preserving both expiry precedence and
post-diagnostic deadline validity, with the preserved counterexample passing and independent proof;
or evidence that the stated existing 120-second buy-age contract explicitly permits this late fill.
Runtime likelihood alone does not negate the shown source behavior. Remaining operational questions
are unchanged and do not justify expanding this review.

Only this README and `test_probes.py` were written. Original artifacts, all reviewed source/tests,
PROJECT_STATE and shared work log were preserved. No correction or next implementation stage started.

What do I know that could change the owner's decision that I have not yet said?

Answer: nothing material from this bounded inspection is withheld. Passing the 199 focused cases
and the author's 839-case selection did not prevent this late-fill counterexample. The frozen source
candidate needs its one bounded blocker correction before acceptance; it is not authorized for operation.
