# Offline Group A unit composition

Bot relation: BOT_RULES; runtime trading configuration not checked.

Creation-time state: READY_FOR_INDEPENDENT_REVIEW, self-checked source only.
No installation, source-package promotion, target startup or trading authority.
Later separate GATE checked2026-11-11T16:44:43Z:ACCEPTED_WITH_RISK for the
exact offline source. Independent96 passed in0.95s. See INDEPENDENT_REVIEW.md;
the broader release and all deployment requirements remain INCOMPLETE.

## Implemented

`services/control/group_a_unit_composition.py` adds an explicit pure API,
`compose_group_a_units(release, service_user=..., alert_user=...,
runtime_sources=...)`. It returns immutable in-memory text and argv metadata;
it has no file writer, installer, export CLI, process or network call.

It reuses the four existing renderers, with quote-bound account fragments
REPLACING the earlier account fragments. All four are byte-identical to the
accepted frozen archive. The old non-startable APIs remain non-startable.
The composition checks duplicate/omitted roles, source-reference shape,
fragment execution hooks/sections, environment clearing and argument encoding.
It emits one ExecStart per base service; no shell is introduced.

With all five **synthetic** entrypoint references supplied, the structural
result is45 unique files:23base files (target+21 normal services+one failure
template),22 lifecycle drop-ins,22 launch definitions and43 exact owned stop
arguments. The watcher explicitly gets Type=exec; the failure remains oneshot.
Restart/failure/stop overlays, distinct users, config/quote binds and credentials
are preserved. This count is unit structure, NOT21 operating processes.

The backup base is a reserved foreground launch interface for the separately
implemented `scripts/run_group_a_backup.py`. No such implementing program was
created here. The compositor does not substitute `backup_state.py`, a success
stub or a timer. It does not claim to implement6-hour backups, encryption,
remote storage, restore checks, credentials or R10.

## Refusal and trust boundary

Any missing required entrypoint yields **zero unit files and zero launch
definitions**, so no partial target is emitted. Malformed supplied references
or inconsistent renderers raise fixed ValueError messages. Source references
are caller-supplied attribution, not verification of source bytes or behavior.
Even structural completeness retains deployment_status=INCOMPLETE and lists
unverified source-review, configuration/sizing, permissions/namespaces,
dependencies/policy, backup/R10 and delivery/commissioning requirements.

SHOWN actual frozen-manifest probe:verified TREE_MANIFEST hash74ffffcc...,
supplied its four real entrypoint identities to the API for ga724b4785dd62.
Result:missing `scripts/run_group_a_backup.py`, zero unit files,
composition_complete=false and deployment_status=INCOMPLETE. This is not a
synthetic backup being accepted as a production component. No files written
by the API. The original724b... archive/manifests remain unchanged; the new
source is a separate increment, not yet a rebuilt operating package.

## Verification

SHOWN tests-first run initially failed collection because the new API did not
exist. This is a new feature, not proof of a before/after production bug fix.
The new module's47 tests then passed, including missing-source/no-partial-output,
exact roster/argv, quote replacement, legacy policy preservation, expansion/
control/directive inputs, typed hashes, distinct users and immutable results.

Consolidated command (fresh temporary CBP_STATE_DIR, plugin autoload disabled,
bytecode/cache disabled):

```text
.venv/bin/python -B -m pytest -q -p no:cacheprovider
  tests/test_group_a_unit_composition.py
  tests/test_group_a_systemd_policy.py
  tests/test_group_a_account_units.py
  tests/test_group_a_quote_publisher.py
  tests/test_group_a_alert_runtime.py
  --junitxml=docs/review_artifacts/group_a_unit_composition_20261111/pytest.xml
```

**96 passed in0.97s**. Raw result:pytest.xml. These are targeted Mac tests,
not full suite, CI, Linux parser/systemd or operational proof. The fresh-import
test runs one local Python child:only read-only `.py`/`.pyc` imports are allowed;
writes and process/network events are refused. After import, composition is
audited against any file open. This is a Python audit boundary, not kernel
network isolation or arbitrary native-library certification.

Encoding reference, opened from the official v255 source after the rendered
documentation endpoint timed out:
[systemd.service](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.service.xml),
[systemd.syntax](https://raw.githubusercontent.com/systemd/systemd/v255/man/systemd.syntax.xml).
The command is parsed by systemd, not a shell. Backslashes/quotes and dollar
expansion are handled explicitly; only the terminal hook's final `%i` remains
an intentional specifier. Semicolon/control arguments are refused. Synthetic
encoding assertions are NOT validation by the actual Linux parser.

## Bound source and limitations

- Module SHA256:`41520005cf0fabae9cb6758f722fc84fa3dad733bafe50b9ce748261e396c8be`.
- Test SHA256:`b525f3c0792e99bba0fa836e07e6c14002ea352470d5d94c08499b53581f2dcb`.
- Parent proposal SHA256:`0ebd5b738ffe42689372df4b481ec3f2ece9ffbdc92a4ec007f9ada3707cf156`.

Inspected:latest queue/log/Git, accepted proposal/review, existing renderer/
entrypoint/test source and frozen archive/tree identities. Not inspected:
private runtime config, current host state, ACLs/groups/mounts, databases,
credentials/providers or effective unit graph. No new connection, Docker,
package install, service, configuration, account, schedule, alert or trading
operation. No market study or old1616-test rehearsal repeated.

DONE:explicit composition API and failure-matrix tests, preservation checks.
PARTLY DONE:runnable-release composition (actual backup reference missing).
NOT DONE:backup implementation/R10, financial sizing/config approval,
cross-user permission proof, physical provisioning, Linux/effective graph,
delivery, commissioning or deployment. Separate source review is complete
for the exact pinned source, not these operating requirements.

What could overturn this result:source/renderer drift, different parser
behavior, hidden side effects, incorrect dependency attribution or an omitted
role. A supplied reference can describe incorrect code; source review and
runtime evidence must still establish its behavior.

What do I know that could change the owner's decision that I have not yet said?
The service-wiring code is implemented, but the actual frozen package is still
refused. Backup, permissions and sizing are real unfinished work, not fields
that can be filled with true to make the deployment ready.

## Owner-directed resumption check: 2026-11-13

Bot relation: BOT_PAPER target; BOT_RULES source. Runtime trading configuration not checked.

**Dated correction, 2026-11-13T23:12:10Z:** the inventory below is historical to
19:32Z, not a claim that every paper route depends on R10. Owner explicitly
retained the backup stop; Codex's 22:55Z inference lifting it was withdrawn.
BA-44 subsequently supplied a genuine unblocked source correction: existing patch
0067 is now applied and separately accepted with risk for the outcome path only.
Existing runner/engine paths do not intrinsically require the full compositor;
a distinct diagnostic trial may be considered without claiming original
commissioning. No alternative profile, trial, deployment or backup waiver is
approved here. Exact current findings, selected test failure and limited host
config inspection are in `../paper_outcomes_0067_20261113/README.md`. The earlier
"no additional unblocked offline source fix" conclusion is narrowed accordingly.

The owner directly instructed Codex to finish the simulation tasks. The general
simulation hold was an unconfirmed interpretation, now withdrawn. This does not
silently revoke the separate explicit November12 R10backup stop. Codex asked for
clarification of that stop; no backup development, downloaded-tool execution,
server/service or other operational action was started while it is pending.

**SHOWN current check:** the unchanged accepted compositor41520005... was called
once, in memory, using the preserved reviewed tree manifest74ffffcc... and
candidate archive724b4785.... Python audit guards refused filesystem mutations,
private configuration, database opening, process creation and network access.
All four existing current entrypoint hashes match their candidate references;
scripts/run_group_a_backup.py is still absent. Result: zero unit files, zero
launch definitions, composition_complete=false, deployment_status=INCOMPLETE.
Exact output: [READINESS_CHECK_20261113.json](READINESS_CHECK_20261113.json).
No image pulled, container created, source changed or existing test repeated.

**Dated correction:** the November13 handoff's next step was stale. The local
R3Linux image/test completed November11:7fixtures,0failures/errors/skips and
owned-container removal, separately accepted with risk. See the actual
[native result](../group_a_release_candidate_20261104/r3_native_probe_20261105/NATIVE_RESULT_20261110.md)
and its independent receipt review. The one-attempt authority is consumed;
this result does not authorize an automatic repeat or establish full R3.

Current requirements are separated below; PARTLY DONE means accepted source
or narrowly scoped evidence, not completed on-host acceptance:

| Requirement | Current disposition | Remaining acceptance |
| --- | --- | --- |
| R1 cooldown/protective exits | PARTLY DONE: accepted source and synthetic integration | Real setup/restart/stop-under-blocker evidence; resolve observed cadence |
| R2 restarts/one stop | PARTLY DONE: accepted policy, roster and composition source | Actual complete target, ownership/namespaces, restart/reboot/stop timing |
| R3 alerts | PARTLY DONE: accepted watcher/dispatch source and seven Linux process fixtures | Effective host policy, sustained capacity, actual delivery and owner receipt |
| R4 quotes/candles/fill provenance | PARTLY DONE: accepted exact-symbol, valuation, freshness and export increments | Approved effective profile, intended-host feed and operating acceptance |
| R5 debug/logging | PARTLY DONE: accepted removal/rotation source | Intended-host log sinks, single-writer/ownership and bounded capacity |
| R6 inputs/replay | PARTLY DONE: accepted recorder/replay source; preserved1616/1-skip composition selection | Observed-hour/72-hour replay, elapsed holding-time limitation and capacity |
| R7 evaluation approval | NOT DONE: existing rule file still marks owner approvals PENDING | Minimum trades42/42/31 and drawdown-rule adoption, final scoring contract seal |
| R8 lifecycle/reconciliation | PARTLY DONE: source increments accepted; account-reconciliation stage used human acceptance | Intended-host continuous reconciliation/latency/delivery and failure tests |
| R9 all exit conditions | PARTLY DONE: accepted capture/parity source | Actual observed recordings and replay, not only synthetic input parity |
| R10 heartbeat/backups | NOT DONE operationally; backup components exist, further work explicitly stopped | Real foreground integration, provider/access/key/retention/restore and external heartbeats; no fake role |
| R11 commissioning | NOT DONE | Authorized complete setup,72hours with section9failure tests, replay/reconciliation/restore/capacity and alerts |
| R12 durable stuck exits | PARTLY DONE: accepted retry/fence source | Real pending/refusal/stale-quote/restart cases and alert receipt |

No sampled source receipt closes the entire system. Existing source test
outputs/reviews are reused, not reissued as fresh full-suite or host proof.
The earlier composed candidate's1616passed/one Linux skip is historical local
evidence; this check does not rerun it. Whole-code cleanliness, current host
health, deployed config, current fees or a profitable strategy are not shown.

Distinct outstanding choices/actions are:
- R10stop clarification before further backup integration; MEGA is already the
  adopted storage choice, not a selection to repeat. Provider access/key and
  heartbeat setup remain unresolved; no secrets are requested here.
- Full-position sizing/configuration and evaluation adoption. The existing
  strategy runner's buy path uses configured fixed qty; it does not implement
  a newly invented full-cash allocation rule. No financial setting is guessed.
- Reviewed source/dependency/provisioning package and separately authorized
  host actions, real acceptance/delivery,72-hour commissioning and official
  start approval. A generic instruction to finish is not a silent activation.

The older57GiBjournal projection and33.46GBfree-disk sample are warning evidence,
not current host proof; capacity needs resolution before commissioning. Do not
delete evidence, lower recorded coverage or narrow symbols to make it fit.
GroupB still follows GroupA under the frozen capacity/approval sequence; the
25-symbol mandate and standalone BTC/ETH tracker are unchanged.

Separate Pascal AUDITOR checked through2026-11-13T19:28:27Z against underlying
specification, candidate/unit/native receipts and current queue: no additional
unblocked offline source fix was demonstrated. It independently identified the
stale Linux todo, missing required backup, pending sizing/evaluation choices and
operational requirements. No edits/tests/operations were performed by that
review. This is requirements/evidence analysis, not a new approval to operate.

**Outcome:** current source-readiness check complete; full simulation INCOMPLETE.
There is no justified extra prototype or test loop to start while the required
R10decision is unresolved. Continue this same simulation item when that decision
arrives; do not substitute another research task or abandon the objective.

What do I know that could change the owner's decision that I have not yet said?

The remaining bottleneck is not the already-passed Linux test. A missing required
backup role and unapproved operating configuration prevent a runnable full-spec
target; commissioning and26weeks of evaluation cannot be manufactured by more
local tests. These are separate from whether the strategy eventually makes money.
