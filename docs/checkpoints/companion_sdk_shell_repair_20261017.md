# Qdrant constructor and explicit MinIO shell repair

Date2026-10-17 (client date). Active role ENGINEER. Risk HIGH.
Handoff READY_FOR_INDEPENDENT_REVIEW; scoped independent results below.
Installation/runtime INCOMPLETE. No new installed-state observation made today.

## Minimal source corrections

Removed the live HTTPTransport argument from the restricted Qdrant constructor.
It now supplies primitives only, retaining prefer_grpc=false, trust_env=false
and follow_redirects=false. The captured installed SDK copies these options
before forwarding. Captured HTTPX's default HTTPTransport sets retries=0;
there is no new wrapper, deepcopy override, dependency upgrade or global patch.
Ordinary/nonrestricted construction remains unchanged.

MinIO source coverage now requires /bin/bash rather than the observed /bin/sh
link. Its storage probe invokes exactly /bin/bash -p -c. The transport permits
the explicit regular /bin/bash archive path and still rejects all archive links.
PostgreSQL's existing shell command is unchanged. No storage image/config changed.

The -p flag closes a conditional startup regression found in independent review:
noninteractive bash can process inherited BASH_ENV before the probe script.
No evidence establishes that variable exists in the target. A synthetic host-only
test demonstrates control execution of a fixture startup file and suppression
with -p; it does not run the installed binary or actual MinIO script.

## Focused proof

Before source edits, the six selected regression cases failed. After initial
repairs, the following six-module command gave335 passed,128 existing FastAPI
startup deprecation warnings in3.83s:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_companion_probe_policy.py \
  tests/test_companion_runtime_adapter.py tests/test_companion_docker_transport.py \
  tests/test_companion_runtime_wiring.py tests/test_companion_installer.py \
  tests/test_companion_install_env.py
```

Separate AUDITOR independently repeated335 passed/128 warnings in3.84s. It
confirmed Qdrant primitives survive the captured constructor's deepcopy and
forwarding controls remain, but returned INCOMPLETE for bash startup processing.
Applied exactly its -p correction, exact-argv assertion and startup-file test.
Final narrow command:

```sh
env -i PATH=/usr/bin:/bin PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q \
  -p no:cacheprovider tests/test_companion_runtime_adapter.py \
  -k 'storage_checks_before_apps or pinned_bash_mode or minio_source_pins'
```

SHOWN:3 passed,62 deselected in0.16s; independent confirmation3 passed/62
deselected in0.19s, ACCEPTED for that correction. No remaining blocker reported
in the scoped confirmation. Do not add overlapping test counts or claim a new
full335-test run after the final argv correction. No full repository suite run.

The Qdrant regression executes only the captured constructor AST in a controlled
namespace, substitutes the remote wrapper and uses real host HTTPX with blocked
network. It verifies captured-source integrity, identical host/installed HTTPX
transport source hash, zero default retries, disabled proxy/redirect settings and
cached-client reuse. This is stronger than the old kwargs mock, not execution of
the installed module, complete SDK initialization or operational proof.

## Evidence and remaining boundary

VERIFIED_ENV: local Python3.12.10, captured public source, fake Docker state,
ASGI fixtures and synthetic host child processes. No Docker, network/service
request, real credential access, image build, replacement, startup, migration,
account, scheduler, strategy or trading operation. Reviewed source unchanged
after final confirmation; hashes in companion_sdk_shell_repair_20261017.json.
Earlier manifests/snapshots are historical and preserved, not current approvals.

The prior constructor/shell source gaps are addressed offline. Installed source
still was not updated; yesterday's inventory is not asserted as current today.
Offline-builder resolution, installed env-parser/descriptor fidelity, complete
reconstruction/import-path proof, namespace/citation evidence and a real accepted
installation manifest remain UNVERIFIED. No review of this patch certifies those.
No extra infrastructure is proposed or installed.
