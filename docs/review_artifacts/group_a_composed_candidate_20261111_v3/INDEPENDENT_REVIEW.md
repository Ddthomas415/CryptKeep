# Independent gate: exact composed paper-source candidate

Bot relation: BOT_RULES; runtime trading configuration not checked.

Reviewer Rawls01a1c9d6-7c8d-7c12-86ce-08152156ac6d, checked
2026-11-11T13:34:48Z. Recorded by author from the separate response.

**ACCEPTED_WITH_RISK for exact v3 paper-source composition and fixture
correction only. No blocking findings.** No deployment/activation/trading
authorization or full R3 closure follows.

SHOWN: reviewer verified archive724b4785... and126 unique regular manifest
members, source hashes/modes, preserved base factory and paging exclusions.
Runtime bytes are unchanged from v2. Only the explicitly pinned snapshot test
changes:writer lifetime plus a stricter regression, with existing assertions
intact and no test case removed. Prior failure lanes remain preserved.

Reviewer independently reproduced the GC causal control and ran13 focused
cases:all passed in0.71s. Four selectors expand to1+1+7+4:

```text
tests/test_paper_account_snapshot.py::test_queue_fixture_closes_writer_before_byte_preservation_check
tests/test_paper_account_snapshot.py::test_snapshot_readonly_quoted_queue_opens_after_ledger_lock_and_closes_connections
tests/test_daily_trend_exit_translation.py
tests/test_strategy_runtime_runner.py::test_daily_flat_exit_retries_without_duplicate_enqueue
```

Invocation used the existing venv Python-B, a parent socket-refusal pytest
wrapper, -q -p no:cacheprovider, fresh temporary HOME/state/tmp, candidate
PYTHONPATH and disabled plugin autoload/bytecode. No host namespace or operating
state reused. GC control used v2/probe_queue_fixture_gc.py against v2's unchanged
tree under the same socket refusal; parsed output exactly matched the retained
QUEUE_FIXTURE_GC_PROBE.json. Those controls were not merely inferred from the
author's summary.

Reviewer inspected actual v3 pytest.xml/output/TEST_RESULT:1616 passed,
1 Linux-only skip, zero failures/errors, exit0, elapsed148.929s, no recorded
source mutations. It did NOT independently rerun the consolidated selection.
The v2 remaining failure is supported as a fixture-writer lifetime defect,
not an observed production-reader write.

Full archive SHA256:
724b4785dd627f9ff35bc91b939788d6ac90850458ba4f4333f7c7231f3dac1d.
Manifest SHA256:
928b12da4275a76c44728cdd141b76d7c0899c99fa3d28204a86bb03ec26ea03.
Tree manifest SHA256:
74ffffcc5f131d7766350731337825e9c628ce1184b5d3d240d476d8c027f885.
Corrected test SHA256:
e8d2a9ad1b69ecae1427af6861abc1be84dc07808ac77dfbbddb8a0fd5842f90.

Residual limits:Linux execution/dependency lock, actual runtime configuration,
effective systemd/namespaces/capacity and operational readiness are not
established. Parent socket guards are not kernel isolation. Unit fragments
remain non-startable. No reviewer edits, network, server, installation or
service action was performed.

What do I know that could change the owner's decision that I have not yet said?
This is independent acceptance of exact source composition and its fixture
correction, not an independently rerun1616-case suite or permission to deploy.
