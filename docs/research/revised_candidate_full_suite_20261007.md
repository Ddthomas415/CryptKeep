# Revised candidate verification

Active role AUDITOR. Release acceptance INCOMPLETE.

The three bounded review corrections are assembled in an unpublished candidate:
explicit quantity evidence, per-intent fill-write failure isolation, and approved
durable-recording order for canonical symbol-loss effects. Prior independently
accepted scopes remain bounded; no assembled series/release approval inferred.

## Frozen identity

Base: 620bc8dbeee71cca327042902759e219e18f30b6.
Candidate: /private/tmp/cryptkeep-revised-suite-mzseu2l_/source.
Artifact directory: docs/review_artifacts/treatment_candidate_revised_20261007.
Manifest records ten source/test hashes and patch SHA256. Those ten files match
the independently reviewed candidate and current source at freeze. Candidate
contains the base plus exactly those ten modified/added files, not unrelated
working changes. Patch applicability against disposable base index and diff
whitespace checks passed. Original Git index remains untouched.

## Verification boundary

Full-suite runner: docs/review_artifacts/verify_revised_treatment.py.
Runs tests/ with a 900-second timeout, no runner slow skips, clean environment,
null keyring, disposable state/SQLite, macOS network and operator-home data/write
denials except dependency reads. No credentials or account copies supplied.
Only this runner's subprocess group is terminated on timeout.

Full result: 3,812 passed, 33 explicitly skipped, zero failures/errors,
35 warnings, 289.77 seconds. Runner exit0, elapsed290.50s, no timeout.
run_summary.json/JUnit/log preserve the exact result. Earlier mixed-working-source
3,889-pass result is not attributed to this revised candidate: unrelated tests
were excluded. Optional companion skips do not prove companion integration.
Candidate CI/host/live/economics remain UNVERIFIED.
Patch SHA256: 1299a32e2fd07be52cf1075898a675d8f7c2b3aedbacae80af16e2a3d7420c47.

## Required release limits

No push, merge, deployment, migration, collector restart, config/account/order
or credential change. Old-writer shutdown and approved no-history-replay cutover
remain release preconditions. Orphan earlier journal rows may hold subsequent
loss accounting; direct low-level callers and separate position/daily effects
are outside the ordered symbol-loss contract. Full-suite success cannot resolve
these disclosed design boundaries or authorize live execution.
