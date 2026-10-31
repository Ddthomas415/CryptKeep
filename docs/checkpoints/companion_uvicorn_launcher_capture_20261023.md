# Uvicorn Module Launcher Capture

Active role: AUDITOR. Objective: supply R1's missing fixed-file source evidence
for the four accepted stopped v6b replacements. Operator explicitly approved
four-file read-only capture; no startup, execution or credential access.
Evidence state: READY_FOR_INDEPENDENT_REVIEW. Runtime remains INCOMPLETE.

## Shown

The one approved capture completed: six native read commands (one sanitized
four-ID inspect, four fixed-path docker-cp reads, one identical inspect).
Elapsed 0.303 seconds; 120-second overall and 15-second per-command limits.
Pinned CLI hash verified before each command with the existing verification
helper and an empty temporary Docker configuration, fixed local socket and
empty child environment except PATH. No retry or container exec.

All four IDs/images match the accepted packet. All four remain created,
zero-restart and never-started. Recorded name, command, entrypoint, workdir,
state and identity fields equal their prior selected values before and after.
This is not a full configuration, volume or original-container audit.

Fixed path on each subject:
`/usr/local/lib/python3.11/site-packages/uvicorn/__main__.py`.
Each readable payload is 62 bytes and has SHA256:
`0d08b3cba9ca3f4cb084fa6708782644360831f72a64a544ccd2164198eab554`.

```python
import uvicorn

if __name__ == "__main__":
    uvicorn.main()
```

The source was read, never imported or executed. Four separate regular-file
tar members were checked in memory (fixed basename, <=64KiB, no extra members
or links) and saved separately. No tar was extracted onto the filesystem.

## Reproducible Evidence

Folder: `docs/review_artifacts/companion_worker_preparation_20261023/launcher_capture/`.
Each subject has a `phase1-<name>.__main__.py.source.txt` record; report.json
binds path, exact container/image IDs, byte sizes, hashes and both inventories.

- report.json SHA256: `5e1f397376c0e2f4ff1617b5881accb70baf5202ef35bfe2b7bfdf2e58d36d32`
- Driver: `docs/review_artifacts/companion_worker_preparation_20261023/capture_uvicorn_launcher.py`
- Driver SHA256: `b059e2b263b105b65fb3ca6bee9c682f26b4975d865c96384923dd649b336f7c`

VERIFIED_ENV actual command (one approved invocation, exit0):

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B \
  -m docs.review_artifacts.companion_worker_preparation_20261023.capture_uvicorn_launcher
```

Driver exclusively creates its output directory; do not rerun it. Source bytes
and recorded hashes were rechecked offline, all four payloads byte-identical.
Three synthetic tar-parser assertions passed before capture. No full suite or
runtime tests repeated. Do not confuse those parser checks with startup proof.

## Limits And Next Proof

These are parent-performed native observations, not independent re-observation.
No originals, storage or older stages were queried or changed. No build,
create, start, stop, signal, service query, token access, scheduler, account,
strategy or trading operation. The existing runtime transport allowlist was
not broadened to perform this separate expressly authorized fixed-path read.
The direct bounded read helper handled only the six stated read commands.

Independent static review must assess the launcher bridge against the accepted
startup/client policy evidence. Captured source is not startup, SDK, shutdown,
acknowledgement, cancellation, recovery, cited-explanation or profitability proof.
The old packet/source records and previous review findings remain unchanged.
Any required exact-path runtime pin support is a separate offline code change;
no operational authorization follows from this capture or its review.
