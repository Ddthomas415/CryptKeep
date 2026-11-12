# Final Independent Written-Exit Accounting Correction Review

Date: 2026-11-03. Active role: GATE. Risk: HIGH.

Bot relation: BOT_RULES; runtime configuration not checked.

**Disposition: ACCEPTED_WITH_RISK for the corrected written-exit accounting
source prerequisite, not full R8 or operational readiness.** The original P1
ambiguity finding is SHOWN corrected. No remaining finding was identified within
the bounded decoder/empty-document correction scope. The original rejection and
unchanged probes remain preserved alongside this report.

## Corrected Boundary

- `IntentQueueSQLite.strategy_sell_intents_after` reuses the existing journal's
  strict finite-object decoder. Repeated keys at any nesting level, nonfinite
  JSON and invalid/non-object JSON are not silently normalized into usable
  accounting evidence. The original `meta_raw` value is retained.
- `PaperExitAccounting._recover` distinguishes absent SQL NULL metadata from an
  invalid empty document using `meta_raw is not None`. Invalid raw evidence is
  retained and quarantined; it leaves accounting unsettled, counters unchanged
  and new entries blocked. Protective sells remain available under the existing
  runner/queue constraints.
- SQL NULL and valid legacy objects without `exit_event` remain skipped rather
  than being automatically recounted. No other generic queue decoding API,
  trading policy, stop-reset basis or execution rule was redesigned.

Inspected: final decoder/controller source delta, eight added flat/held
regressions, unchanged original probe code, relevant strict decoder contract,
final hash manifest and existing receipts. This was a correction-only recheck;
no broad audit or full recording matrix was repeated.

## Independently Executed Evidence

All commands ran from `/Users/baitus/Downloads/crypto-bot-pro` using the repository
venv and fresh temporary state. Temporary directory names were produced by
`mktemp`; their expansions were not returned and are not invented here.

### Narrow Affected Selection

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r8-correction-gate.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_exit_event_journal.py tests/test_paper_exit_accounting.py tests/test_kill_cooldown_sessions.py tests/test_runner_decision_capture.py::test_storage_accounting_method_is_part_of_loaded_decision_identity --tb=short
```

SHOWN independent result (completion chunk `8610d4`, exit 0):

```text
167 passed in 16.32s
```

This includes 93 journal, 52 accounting, 21 cooldown and one storage-fingerprint
case. The eight new regressions cover top-level duplicate `exit_event`, nested
duplicate PnL, unrelated nested duplicates and empty documents, each while flat
and while held. They verify exact raw quarantine, no provisional counter change,
blocked buys and continued protective sell emission.

### Original Three Probes, Unchanged

The exact original probe files were executed without edits:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r8-correction-originals.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c 'from pathlib import Path; p=Path("docs/review_artifacts/paper_exit_accounting_r8_20261103/independent_review/probe_recovery.py"); exec(compile(p.read_bytes(),"<string>","exec"))'
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r8-correction-runner.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c 'from pathlib import Path; p=Path("docs/review_artifacts/paper_exit_accounting_r8_20261103/independent_review/probe_runner.py"); exec(compile(p.read_bytes(),"<string>","exec"))'
```

SHOWN independent results (`b767fb` and `5032d6`, both exit 0):

```text
2 passed in 0.40s
1 passed in 0.61s
```

The duplicate-key recovery and real-runner admission counterexamples now pass;
acknowledgement-loss recovery continues to pass. These are three probes of the
original single finding, not three newly discovered defects.

### Before-Correction Failure Proof

The reviewer independently overrode only the saved old queue iterator and old
controller recovery method in memory after temporary fixtures were installed.
No production files were swapped. The command captured the repository root
before pytest changed the working directory:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r8-correction-before-absolute.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c '
from pathlib import Path
import pytest
ROOT=Path.cwd()
class Before:
 def pytest_runtest_call(self,item):
  h=item.funcargs.get("flow")
  if h is None:return
  queue_ns=dict(h.queue_store.__dict__)
  p=ROOT/"docs/review_artifacts/paper_exit_accounting_r8_20261103/storage__intent_queue_sqlite.py.submitted"
  exec(compile(p.read_bytes(),str(p),"exec"),queue_ns)
  h.mp.setattr(h.queue_store.IntentQueueSQLite,"strategy_sell_intents_after",queue_ns["IntentQueueSQLite"].strategy_sell_intents_after)
  accounting_ns=dict(h.accounting_lib.__dict__)
  p=ROOT/"docs/review_artifacts/paper_exit_accounting_r8_20261103/paper_exit_accounting.py.initial"
  exec(compile(p.read_bytes(),str(p),"exec"),accounting_ns)
  h.mp.setattr(h.accounting_lib.PaperExitAccounting,"_recover",accounting_ns["PaperExitAccounting"]._recover)
raise SystemExit(pytest.main(["-q","-p","no:cacheprovider","tests/test_paper_exit_accounting.py","-k","ambiguous_duplicate_metadata","--tb=short"],plugins=[Before()]))
'
```

SHOWN independent result (`6c56a5`, exit 1):

```text
8 failed, 44 deselected in 0.62s
```

All eight failed at the expected assertion that accounting must remain unsettled
(old methods returned False). This is isolated component failure-before proof,
not a pristine whole-tree comparison.

An earlier reviewer override attempt incorrectly resolved artifact paths after
the fixture changed cwd. Its eight failures were not valid source evidence and
are excluded from the proof above. The corrected absolute-root run explicitly
showed the expected behavioral assertion failures. No production correction was
made in response to that reviewer command error.

## Final Hash Evidence

SHOWN: the reviewer recomputed all eleven values against
`../corrected_hashes.json`; every value matched (verification chunk `cfcabd`).
Changed-path `git diff --check` passed (`be1cb9`). Accepted candidate identities:

```text
services/execution/paper_exit_accounting.py
466b850fab391777671dd6782bf3737af8345e8e9d14f51432aca16c0e62edfc
storage/exit_event_journal.py
6c8ee1c44cd551a65139a16bfaa5fa18fbc29b4b5bee93c6e66835ae6e6f3ff8
services/execution/strategy_runner.py
347b8e7fcf2dfe2579b62c3d2b309d95ca5d0fa0d74f9ff6f65a0847e613269f
services/strategies/signal_input_capture.py
962ef51f959d256a30aa04fc0aa93b2e60898db778d5948a9bff5418adfe6abe
storage/intent_queue_sqlite.py
8b7aa575ebffee92db513925b1d81758591bad9e316a4b9378f10cabb4a5d1d3
tests/test_strategy_runtime_runner.py
46f31a04710a9296962632d4658fd27f723a02a3d3dbb8464faf6f5a3b2b9f0b
tests/test_runner_decision_capture.py
e87f6de7d1d3c387bae814c46ac4b1ac27a048f98b132e8a2219b1b1838a8048
tests/test_runner_recording_integration.py
0e01a642f81393ccaa429f9688fe245ad1dbc44937debbef254e3370f3b9b0bf
tests/test_exit_event_journal.py
e49b3adddd4934297b0bf229fd4b74a87e6254a87528a51c189969d6d219b7ce
tests/test_paper_exit_accounting.py
5ebbdbdd7f152270915007263319963c28e347461432439de0f89f4a2f4c572e
tests/test_kill_cooldown_sessions.py
33ac890ace911640dbf80509f297f27856e2821667f5914da53dc553f829e680
```

## Receipt Boundaries

The author retained the original 32-file consolidated result: 788 passed and one
FakeDB compatibility-fixture failure. The revised durable-queue cooldown fixture
then passed its 21-case file separately. Those results are not reclassified as
one uninterrupted green 789-case run. The reviewer inspected the original broad
receipt and the author's 21-case XML; the broad selection was not independently
rerun. The reviewer did independently execute the 21 cooldown cases inside the
167-case correction selection above.

The author's narrow correction receipt is separate from the reviewer's 16.32s
run. The owner's final message reports 167 passed in 15.32s; that timing is not
substituted for the independently observed result.

## Remaining Limits And Handoff

This is provisional written-strategy-sell reference-price accounting, not fills,
realized profit, a monetary portfolio return, or evidence that the system is
worth operating. The current stop-reset point/basis, consumed signal history,
legacy inventory limits and ordinary 200-row scan were not redesigned. SQL NULL
legacy rows are not automatically imported or recounted.

Full R8 expiry, lifecycle timestamps and watchdog/reconciliation; R4 quote/data
identity; R1 timing; actual runtime configuration, service commissioning and
economic validation remain unverified or incomplete. The inherited WAL/NORMAL
policy is not a new power-loss durability guarantee. Unknown accounting still
requires the existing runner-state and queue paths to work for protective orders
to progress. Legacy JSON plans are not automatically imported.

No implementation files were edited by the reviewer. Tests/probes were offline
and temporary; no services, accounts, private configuration, network calls,
deployment or trading operations were used. This report was persisted at the
owner's request without reopening any other accepted objective. New evidence of
ambiguous metadata acceptance, dropped/duplicated events, wrong provisional
counters, suppressed protective exits or actual host behavior could change the
bounded source disposition. Acceptance does not authorize operation of the
unfinished simulation.

What do I know that could change the owner's decision that I have not yet said?
