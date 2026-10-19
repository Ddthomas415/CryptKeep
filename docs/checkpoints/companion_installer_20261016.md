# Executable companion installer: offline handoff

Active role ENGINEER. Risk HIGH. READY_FOR_INDEPENDENT_REVIEW.
Runtime restoration INCOMPLETE. No installation or query executed/authorized.

## Delivered implementation

- `scripts/research/companion_installer.py`: reviewed-manifest loader, one-shot
  installation/recovery controller, inert-by-default command-line entry point.
- `scripts/research/companion_install_docker.py`: concrete Docker backend for
  source-only local image construction, preserved originals, stopped replacement
  creation, source verification and identity-scoped rollback. It does not extend
  the existing query transport's allowlist.
- `scripts/research/companion_install_env.py`: pure bounded environment encoder;
  preserves existing credentials and applies declared nonsecret probe overrides.
- Two matching test modules; existing reviewed controller/profile unchanged.

The CLI takes an externally trusted SHA256 of an independently reviewed public
manifest. It does not discover or generate acceptance from installed inventory.
Policy claims bind to that manifest; neither the hash nor a reviewer-name string
authenticates the reviewer. Test manifests are SYNTHETIC ONLY and must never be
used as operational pins. No real manifest is supplied by this stage.

Default entry point validates manifest shape/hash only, without Docker or secret
access. An explicit apply flag also requires a new exclusive receipt path and
host installation lock. That flag is not human authorization. No executable
command with live operands is given here because the independently reviewed real
manifest and installed-compatibility evidence do not yet exist.

## Important behavior and boundaries

Seven original target identities/state/configuration fingerprints must agree
before work. Four application images are built from their respective existing
images using explicit reviewed source files in an in-memory tar context, no RUN,
ADD, remote source, dependency upgrade or broad repo COPY. Parent ONBUILD is
refused. The backend selects legacy-builder mode, no-pull and network-none;
installed support and absence of registry metadata access still require external
proof before the manifest's builder policy can be accepted. Failure is not
permission to enable a networked builder.

Build output/new layer lineage is checked before container replacement. Public
parent tags and daemon/build artifacts can remain after failure; no prune or
image deletion is attempted. Original application containers are renamed and
detached, not deleted; replacement containers are created, never started.
Storage identities and mounts are preserved. Unsupported reconstruction options
are refused; completeness of the reviewed reconstruction remains an external
precondition rather than an automatic guarantee from an argv whitelist.

All credentials stay in the bounded create/preparation child's memory. Core
dumps are disabled before reading original Config.Env through private stdout;
validated records go directly to Docker stdin, not disk/env/argv/logs. Invalid
records are checked during preparation before any rename. No credential hashes
or values return to the parent. Docker still persists its own container env;
clearing Python references does not promise forensic memory erasure. Installed
Docker env-parser fidelity is not established by the pure encoder tests.

The controller reserves120s of300s for recovery and caps each operation. Intent
receipts precede mutation. After a timeout it reads actual identities before
cleanup, never retries the mutation. Only this attempt's identified, never-started
replacement may be removed, without force/volume flags. Original names/network
settings are restored and checked; running, changed or ambiguous targets are
not removed or stopped. Reconciliation is point-in-time evidence, not proof of
server-side cancellation. Process death can leave preserved rollback objects;
there is no claim of automatic recovery after restarting the whole installer.

Success leaves four created applications plus three exited original storage
targets and retained rollback objects; it requests independent installed review.
It does not start the explanation path or establish trading readiness. The
separately accepted created-state lifecycle repair is preserved, not bypassed.

## Proof

VERIFIED_ENV: Python3.12.10 with synthetic inputs and fake external state only.

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  --noconftest -c /dev/null -p no:cacheprovider \
  tests/test_companion_installer.py tests/test_companion_install_env.py
```

SHOWN:90 passed in0.50s. Covers default refusal/check-only CLI, manifest rejection,
ordinary stopped installation, before/after-effect failures, partial rollback,
foreign/running replacement preservation, final-state change, deadline reserve,
minimal source-only context, and synthetic stdin-only credential handling.
The sidecar encoder's separate56-test run is included in90, not additional proof.
No full suite, real Docker, network, credentials, build, replacement, startup,
accounts, schedules or trading operations. Fake inline execution is not actual
process isolation, installed parser or daemon failure proof.

Two assumptions for a future operation: the trusted manifest/policy review is
genuine and complete; exclusive operator control holds during the attempt.
No hidden success probability, operational readiness or profitability inferred.
Frozen hashes and review outcome are recorded in
`docs/review_artifacts/companion_installer_20261016.json`.

## Remaining real evidence

Installed CLI/builder/SDK/startup helpers and required binaries, complete public
reconstruction/import-path evidence, credential parser/descriptor fidelity,
approved namespace preparation and real reviewed pins remain UNVERIFIED.
These are actual installation preconditions, not completed by synthetic tests.
No further infrastructure layer is proposed. Independent source review is the
handoff boundary for this implementation; actual preparation/installation and
one explanation query require their separately scoped operational authorization.

## Independent review and bounded corrections, 21:45 UTC

Independent AUDITOR disposition INCOMPLETE on the initial frozen source. It
independently ran90 tests in0.37s and verified hashes/prior preserved source.
Two findings: receipt writes could prevent physical recovery, and success omitted
the public installation identities/fingerprints needed for independent review.
Neither the test count nor absence of observed secret leakage was acceptance.

Corrected those two findings in one bounded patch: recovery receipt writes are
best effort and cannot skip the recovery action; receipt_complete=false preserves
the evidence failure. Success now returns and attempts to persist exact original/
replacement IDs and image IDs, metadata fingerprints, storage identities and
source hashes labeled verified_at_creation. Failure/rollback does not emit stale
successful evidence. Four persistent-receipt-failure cases exercise restoration
after rename, detach, create and terminal-receipt failure. Existing success test
checks returned and persisted public evidence agrees.

The same targeted command now gives94 passed in0.42s. No broad rerun or second
review loop. These two corrections are NOT independently re-reviewed. Initial
and current hashes are preserved in the manifest. Handoff remains
READY_FOR_INDEPENDENT_REVIEW, not ACCEPTED; installed compatibility and actual
service restoration remain INCOMPLETE. No Docker/credential/operational action.

## Independent correction confirmation, 21:47 UTC

Separate AUDITOR returned ACCEPTED strictly for the two final corrections, no
blocker found, independently94 passed in0.39s using the specified isolated command
once. It confirmed physical recovery despite persistent receipt failure, false
receipt_complete, suppression of success evidence after rollback, and complete
returned/persisted public evidence on success. Source/test hashes were unchanged.
Review input artifact SHA256 is retained in the manifest before adding this
disposition. No source changes or operational actions followed the review.

The earlier two findings are closed for offline scope. This scoped acceptance
is not blanket whole-installer approval or installed compatibility proof. Parent
handoff remains READY_FOR_INDEPENDENT_REVIEW for any operational use; runtime
INCOMPLETE. Next substantive evidence is the installed compatibility review and
real reviewed manifest, not another implementation layer or repeated backtest.
