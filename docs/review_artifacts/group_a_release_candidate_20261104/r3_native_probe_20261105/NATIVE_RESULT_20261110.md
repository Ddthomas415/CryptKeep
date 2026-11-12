# R3 disposable Linux result, November 10, 2026 New York

Bot relation: BOT_RULES; runtime trading configuration not checked.

Role: ENGINEER. Observed run: 2026-11-11T02:11:24Z (November 10, 21:11 New York).
State: ACCEPTED_WITH_RISK for this native evidence increment after separate GATE
review; R3 remains INCOMPLETE. Review checked through 2026-11-11T02:13:56Z:
[independent evidence review](INDEPENDENT_REVIEW_20261110.md).

## Result

SHOWN: the unchanged reviewed packet ran **7 tests, 0 failures, 0 errors, 0 skips**
in the isolated Linux arm64 container. Harness time was 0.722 seconds; the recorded
pull/test/cleanup operation took 3.885 seconds. There was one image pull and one
container, with seven total Docker commands. This is not a full application suite.

The container exited 0. Its immutable ID and unique ownership label matched the
post-run inspection, which reported `running=false`, `status=exited`, `exit=0`.
Removal then returned exit 0 and that exact ID. No broad cleanup or stop command
was used; no pre-existing container was selected or changed by this operation.
The pulled image remains cached as approved.

| Evidence | Observed value |
|---|---|
| Packet SHA256 | `9027d7ddcdca0b45c639c64156af15c32418cf221fdde890049a34434d84f95c` |
| CLI SHA256 | `e6bb967adc3e97c9a9027aa7a1b83691789630cb26a4bbcddd2e8353a8a89ea4` |
| Pinned official Python image | `docker.io/library/python@sha256:c61cffc3bacb94ed026ff8b45d5114b7693dd0420baca0a1ace0e3d0ce9035fd` |
| Image platform | `linux/arm64`, inspected after pull |
| Owned container ID | `ab224ad205eabd65081973a4ab80e01ae5e0200e0ac9fb83ac251a3cf53e898d` |
| Owned label value | `78787c94151d4cada86dc1ebfd8a0489` |
| Raw JSONL receipt SHA256 | `4af24bf6054dcb465d3cc62fd3482ab4c5ff20f2bc60d664adead0ae34b9e60b` |
| Archived invocation SHA256 | `7faae311d956babdb884eddc71eaa764772d96c16d79363a0a3d156ef233d2bd` |

## What was run

The public Docker Hub `library/python` tag metadata identified the single Linux
arm64/v8 manifest for `3.12-slim`; the response and its checksum are in the receipt.
The image was pulled by that digest, then its platform, immutable ID and repository
digest were checked. This is public-registry provenance, not a separate supply-chain
signature attestation. [Official Python image](https://hub.docker.com/_/python),
[Docker digest-pinned pull documentation](https://docs.docker.com/reference/cli/docker/image/pull/).

The create command used the immutable image ID, `--pull=never`, no network or published
ports, read-only root, UID/GID 65534, no capabilities, no new privileges, 32-PID/256-MiB/
one-CPU limits and init. Its only source bind was the reviewed extracted packet,
read-only at `/probe`; `/tmp` was a 64-MiB noexec/nosuid/nodev tmpfs. No repository,
home, daemon socket, named volume, credentials, state database or market data was mounted.

Entrypoint: `/usr/local/bin/python3 -I -S -B
/probe/scripts/research/verify_group_a_linux_processes.py --run-linux-fixtures`.
The seven source fixtures cover normal cycle, timeout, cancellation, parent death
before/after the launch gate, inherited lifetime lock and supervisor SIGTERM.

Raw evidence: `pull_test_20261111T021124Z_78787c94.jsonl`. Exact operation source is
archived as `invocation_used_20261110.py`, identical to the scratch source used.
It is evidence, not standing permission to repeat its `--run` operation.

## Boundaries and open questions

- Packet, harness and production source were not revised to obtain the pass.
- The current operation followed the owner's continuation after Docker processes
  and the original socket became available externally. Codex did not start/restart
  Docker. The earlier failed preflight receipt remains unchanged.
- Claude's packet review R-1/R-2 still apply: timeout/cancellation assertions do not
  prove a callback-start receipt, and a tracked-fork assertion can be vacuous. This
  pass is not evidence that those recommended test-strength changes were made.
- No host/systemd unit, production namespace/WAL mount, installed application,
  sustained capacity, real source/cursor volume, Slack compatibility or owner alert
  receipt was tested. These remain separate R3/provisioning/commissioning proof.
- No research strategy, campaign, account, collector, schedule, server, risk setting,
  credential or trading action changed. There is no financial or profitability result.
- Separate GATE independently checked underlying receipts, invocation, archive,
  manifest and current source matches; it accepted this evidence WITH_RISK, with
  R-1/R-2 unresolved. It did not rerun fixtures or inspect the daemon. This author
  does not accept its own high-risk source or infer full R3 acceptance.

Acceptance checklist: official pinned acquisition DONE; seven native fixtures DONE;
owned removal DONE; source/packet preservation DONE; independent receipt review DONE;
full R3/deployment/alert commissioning NOT DONE. A successful Docker command is not a
claim about every process on the laptop, which was not inventoried by this test.

What could overturn this result: an input/receipt mismatch, misattributed container,
unsupported interpretation of the assertions, or independent review contradicting
the evidence. A different target kernel/architecture or production unit configuration
requires its own evidence rather than transferring this pass without qualification.

What do I know that could change the owner's decision that I have not yet said?
The narrow Linux test is no longer the immediate blocker. The pass does not authorize
deployment or close the remaining real host, capacity and external-delivery gaps.
