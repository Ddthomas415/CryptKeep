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
