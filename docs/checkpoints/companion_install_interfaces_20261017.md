# Installed CLI interfaces and image provenance

Date2026-10-17, client timezone America/New_York. Active roles: AUDITOR for
read-only evidence, then ENGINEER for the demonstrated formatter/no-pull fixes.
Risk HIGH; implementation handoff READY_FOR_INDEPENDENT_REVIEW. No installation.

## New proof, not another proposed framework

The hash-pinned installed Docker CLI was pointed exclusively at disposable fake
Unix sockets, with an empty temporary config and replacement environment.
Synthetic create requests verified that /dev/stdin env-file parsing preserves
leading/trailing spaces, tabs, #, equals signs, quotes, Unicode, combining marks,
an embedded BOM, empty values and a50,000-character value. Each case generated
one fake create request and no start. No real daemon/container/registry or real
credential was used by these tests. API version1.47 was explicitly selected for
the fixture; real daemon negotiation and server-side environment merging were
not tested. This proves the covered installed-parser/descriptor behavior, not
every hypothetical environment string or effective credential validity.

Test module: `tests/test_companion_installed_cli_interfaces.py`. It is skipped
unless CRYPTKEEP_SYNTHETIC_CLI_CHECK=1; ordinary tests must not silently bind
listeners or invoke an installed CLI. First sandbox run had2 setup errors because
Unix socket binding was denied; approved fixture-socket access then passed.
This was a sandbox boundary, not authentication failure or service unavailability.

## Concrete source correction found by the interface check

Native CLI formatting failed when image Config omitted optional OnBuild:
1 failed/4 passed before correction. Installer IMAGE_FORMAT now uses an optional
map index, preserving nonempty instruction rejection in _image(). Three native
CLI fixtures cover omitted, null and populated values. The stopped-create recipe
also explicitly uses --pull=never, matching the no-pull contract and tested CLI
interface; a disappearing local image must fail, not trigger an implicit pull.
No transport allowlist, execution approval or startup behavior was broadened.

Final command:

```sh
env -i PATH=/usr/bin:/bin CRYPTKEEP_SYNTHETIC_CLI_CHECK=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 \
  ./.venv/bin/python -B -m pytest -q --noconftest -c /dev/null \
  -p no:cacheprovider tests/test_companion_installed_cli_interfaces.py \
  tests/test_companion_installer.py tests/test_companion_install_env.py
```

SHOWN:99 passed in0.79s, including5 native-CLI/fake-socket cases and94 existing
installer tests. Counts overlap previous runs and are not added to them. No full
repository suite. Real daemon inspection below is separate from fake tests.

## Read-only real daemon evidence

At20:45 New York (receipt UTC2026-10-18T00:45:57), all seven original IDs/images
were still exited, restart count0/policy no; initial/final selected metadata
matched. All four parent images are present, with no ONBUILD instructions. All
four application commands, null entrypoint, /app workdir and default user match
the inspected recipe; selected privilege/capability/DNS/resource exceptions were
absent. This is not a complete reconstruction certificate.

Container diff shows no writable-layer changes for audit, risk or memory.
Orchestrator's one change is addition of /repo, classified as its bind mountpoint;
its bind refers to this checkout and is read-only. Thus no application-code
writable-layer delta was observed in these four containers. Bind-mounted repo
contents are outside that conclusion and still require reviewed import/source
freezing. RootFS layer identities are recorded, not interpreted as proof of all
dependencies or namespace health. Engine reports29.8.2.

Receipts: `docs/review_artifacts/companion_install_interfaces_20261017/`:
provenance.json and mounts.json. Multiple initial metadata-template errors
(nil lengths, json.Number comparison and absent Parent field) were our diagnostic
defects; no service failure or authentication repair is claimed. Only selected
nonsecret comparisons and changed-path classifications were exported. No raw
environment, credentials or secret hashes requested.

## Independent review and remaining boundary

Separate AUDITOR ACCEPTED only the interface tests and two source changes,
finding no blocker. Independently5 native fixture tests passed in0.42s; the
--pull=never mocked regression separately1 passed in0.49s. It did not reproduce
the parent's entire99-test run or before-fix failure. It reviewed real receipts
as recorded contents, not independent collection or whole-install certification.
Source remains frozen after that review; hashes are in proof.json.

VERIFIED_ENV: native CLI/fake-socket interface and selected read-only Docker
metadata. UNKNOWN_ENV: actual local-only build behavior, complete reconstruction,
mounted import closure, eventual credential wiring, storage namespace integrity
and a real cited query. No image tag/build, container create/rename/disconnect/
start/stop, storage mutation, actual account/credential, scheduler or trading
operation occurred. Fixture HTTP create responses are simulated, not real objects.

No accepted operational manifest was manufactured. The next consequential proof
would be a separately authorized bounded source-only local build from an existing
image, creating image/cache artifacts only and no containers or startup. That
permission is not inferred here. Runtime remains INCOMPLETE.
