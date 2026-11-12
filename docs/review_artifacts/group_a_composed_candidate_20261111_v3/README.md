# Composed Group A source candidate, revision 3

Bot relation: BOT_RULES; runtime trading configuration not checked.

**Source composition and local regression proof only. No deployment/startup authority.**
Author evidence checked2026-11-11T13:36:10Z. Separate final GATE checked
13:34:48Z:ACCEPTED_WITH_RISK for the exact source composition/fixture fix.
See INDEPENDENT_REVIEW.md. This is not full R3/operational acceptance.

## Delivered candidate

source-test-overlay.tar.gz contains126 unique regular0644 source/test/fixture
members, bound to protected Git base580ca31ea983af6452a1e02ab8d4b51645e9b43c.
Archive SHA256:
724b4785dd627f9ff35bc91b939788d6ac90850458ba4f4333f7c7231f3dac1d.

MANIFEST.json binds each delta path/hash/mode/provenance and the builder,
reconciliation inputs, test selection, excluded paging work and observed test
dependencies. TREE_MANIFEST.json binds the1960-file composed scratch tree:
1868 selected public base files plus the delta. This is not a standalone
runtime image, Linux dependency lock, unit installer or operating configuration.
The exact selection/reconstruction algorithm is compose_candidate_20261111.py
in the earlier r3_native_probe_20261105 folder, with explicit
--fixture-lifetime-correction. Do not extract over a working/deployed checkout.

Host #600 archive eligibility and #601 SMA flat-exit work are preserved on
the protected base. Current selected R3/R5 increments are included; base
exchange_factory.py remains intact and optional live-account paging modules
are excluded, not removed from the repository. PUBLIC_FACTORY_PROBE.json
checks the actual composed base factory with a fake client constructor and
empty credentials; it is not a public-price, account or execution test.

## Verification lanes, including failures

| Artifact/run | Result and interpretation |
| --- | --- |
| Original v1, retained |1582 passed,33 failed,1 Linux skip. Baseline core, before-version fixtures and static legacy systemd test assets were omitted from composition. No source mutation. |
| Corrected v2 focused slice |All33 previously failing cases passed after adding only those dependencies/assets. |
| v2 full selection, retained |1614 passed,1 failed,1 Linux skip. Remaining physical-byte assertion was affected by the test fixture's unclosed WAL writer. No source mutation; not green. |
| Deterministic causal probe |Forced GC changed queue bytes BEFORE the production reader; the same original assertions passed when the fixture writer was explicitly closed. Neither probe branch changed queue bytes during the production reader. Synthetic databases only; probe source/results retained under v2. |
| Permanent fixture regression |Failed before the fix; the corrected snapshot module passed63 tests. Existing assertions are unchanged. |
| Final v3, same59-file selection |1616 passed,0 failed/errors,1 Linux-only skip in148.58s; wrapper elapsed148.929s, exit0, no source mutations. One stricter fixture test added; no tests dropped. |

The skip is test_native_linux_cycle_launch_gate_result_and_reap: Linux
parent-death/WNOWAIT behavior is not Mac proof. Earlier seven-fixture Linux
evidence remains narrow and retains its separately recorded assertion limits;
it is not replaced by this skipped test or expanded into production proof.
This is a targeted selection, NOT the repository full suite or CI result.

pytest.xml, pytest_output.txt and TEST_RESULT.json preserve the final raw
test result. TEST_RESULT stays INCOMPLETE for broader operational readiness,
even though the test process exited0. Builder/manifest statuses describe
creation-time review state; later independent disposition is separate.

All runs use fresh scratch HOME/state/temp roots, cleared environment, bytecode
and plugin/cache disabling, no dependency installs and a parent-interpreter
socket refusal guard. That guard is not kernel-wide network isolation.
Static legacy unit tests invoke the existing helper only in dry-run or with
--apply into pytest's own temporary directory, never systemd installation or
daemon actions. Public base cbp.env.example is static test data, not a loaded
operating environment or private .env file. No actual collector/strategy
service, alert, account, server, Docker or trading operation occurred.

## Fixture-only correction

The v2/v3 tree comparison has exactly one changed path:
tests/test_paper_account_snapshot.py. Production source is byte-identical.
queue_db now uses contextlib.closing plus the original transaction context.
Its writer checkpoint/close finishes BEFORE a file-byte baseline is captured.
All24 existing other function ASTs, including their assertions, are identical;
one writer-close regression was added. See FIXTURE_DIFF_PROOF.json and
fixture_lifetime_correction.diff. The snapshot pin was not broadly disabled:
the builder requires the exact old1da551... and newe8d2a9... test hashes under
an explicit flag. Original archives, results and failing evidence remain.

## Environment and remaining boundaries

Observed test environment:macOS, Python3.12, pytest9.1.1, PyYAML6.0.3,
ccxt4.5.48, numpy2.4.4. Versions are observations, not installation instructions
or a Linux production lock. No real market data, strategy search, fee/capital
change or economic claim follows from synthetic tests.

Still required before operations:compatible Linux/venv dependencies, current
safe-value host inventory, complete runnable unit composition, protected
physical paths/credentials/read-only namespaces, restart/stop proof, actual
quote coverage, bounded host logging/capacity, external delivery/owner receipt,
R10 backup/heartbeat/restore and authorized72-hour commissioning. Existing
account/quote/alert fragments are non-startable. No legacy services or ledgers
may be repurposed. No upload, new connection, staging, activation or official
start is authorized by this candidate or prior spent access approvals.

What could overturn the source conclusion: changed manifests/bytes, failed
preserved-host regression, independent reconstruction mismatch, unclosed
dependencies, or a causal counterexample to the fixture correction. Operational
failure or a missing platform gate blocks the corresponding runtime claim,
not the ability to continue safe paper/source research.

What do I know that could change the owner's decision that I have not yet said?
There is now an exact locally tested source composition, not just a proposal.
It still cannot be called a deployed, startable or profitable trading system;
one Linux-only case and the operational configuration/delivery gates remain.
