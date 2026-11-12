# Correction: the live SSH window retained a short packet timeout

Bot relation: BOT_RULES; runtime trading configuration not checked.

Role: AUDITOR (diagnosis), followed by ENGINEER (offline invocation correction).
Status: ACCEPTED_WITH_RISK for the corrected invocation design only after separate
Harvey GATE review checked through 2026-11-11T04:20:59Z. See `SSH_TIMEOUT_REVIEW_20261110.md`.
Host preflight remains INCOMPLETE; no new connection has been made after the failure.

## Evidence

SHOWN: the approved live attempt used the same SSH session 87640 throughout.
The check URL was displayed while the tool reported the process running. The owner
confirmed that live check; polling the same session returned exit 255 and a connection
timeout, no inventory. No replacement connection was created.

The failed process had ended by the observation 42.317 seconds after launch. That
is an upper bound including user/tool delay, not its exact process exit duration.
Receipt: `live_host_preflight_20261111T041447Z.json`; temporary URL redacted.

SHOWN by local `/usr/bin/ssh -G` (no network connection): effective ConnectTimeout
was 210, but ServerAliveInterval remained 5 and ServerAliveCountMax remained 1.
The installed client reports OpenSSH_10.5p1, LibreSSL 3.3.6. Increasing only the
connect timeout did not remove the conflicting shorter setting.

Upstream OpenSSH calls `ssh_packet_set_timeout` with the alive interval/count
before login. Packet handling multiplies those values to obtain its read timeout;
the observed error text matches that packet-timeout path. This strongly supports
the explanation, but the installed Apple binary's internal exit was not instrumented
and its exact build/source equivalence is not proved.
[OpenSSH client setup](https://raw.githubusercontent.com/openssh/openssh-portable/master/ssh.c),
[OpenSSH packet timeout](https://raw.githubusercontent.com/openssh/openssh-portable/master/packet.c).

## Offline correction and proof

`live_ssh_contract_20261110.py` is a local argv builder and effective-option guard,
not a connection starter. It sets ServerAliveInterval to 0 for the approval-bearing
session, removing that short packet timeout, while retaining the explicit 300-second
outer alarm, 210-second connect window and unchanged 70-second remote cap. Strict
host-key checking, one connection, no forwarding and visible diagnostics remain.
It does not change a tailnet policy, authentication requirement or any configuration file.

Before any next authorized invocation, resolve local options with `ssh -G`, validate
them through `validate_effective`, then use `live_argv` from that same module.
Do not manually reconstruct options and reintroduce the old alive deadline.

Command (local only, no SSH connection):

```sh
PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider docs/review_artifacts/group_a_release_candidate_20261104/r3_native_probe_20261105/test_live_ssh_contract_20261110.py
```

SHOWN: **7 passed in 0.05s**. The actual installed client's old effective configuration
is rejected; the corrected configuration is accepted. Five synthetic scope/security
mutations are refused. These tests do not prove successful browser authorization,
deployed host identity, runtime/source alignment or a completed remote inventory.

The live handoff is conditional on the server/transport remaining available; a client
allowance is not a promise that a remote policy will keep the connection open.
The next attempt still needs fresh owner authorization. No more SSH is run under
the spent one-attempt approval. Do not weaken check mode, sign the owner out, retry
automatically, or claim the owner failed to approve.

What do I know that could change the owner's decision that I have not yet said?
The failed attempt kept an incompatible client timeout after I said I had allowed
a live approval window. That is my incomplete correction, not evidence that your
confirmation or the server was at fault. The fix is offline-tested, not live-proven.

## Dated live result, 2026-11-11T07:37:19Z

The owner approved one corrected attempt. Actual effective configuration was
validated against the reviewed contract before launch. Session70737 was saved
to the local receipt before its check URL was shown; the owner confirmed and
the SAME session was polled, not replaced. It remained running through the
long wait rather than reproducing the short cutoff, then returned142, consistent
with the configured overall alarm. No remote inventory returned. The observed
319.877 seconds since dispatch is an upper bound including tool/review delay,
not an exact native process duration.

Receipt: `corrected_live_preflight_20261111T072949Z.json` (URLs redacted).
The timing revision now has narrow live observations, not successful host
authorization/inventory proof. Effective tailnet policy and why the browser
confirmation did not produce completion remain unknown. The approval page's
actual status text is requested; no further connection is authorized here.

What do I know that could change the owner's decision that I have not yet said?
The early client cutoff did not recur, but a longer pending connection still
did not obtain inventory. More approvals without the page's actual status
would not resolve the unknown access-completion step.

## Dated live follow-up, 2026-11-11T11:28:06Z

SHOWN: a fresh owner-directed instrumented attempt on SAME native session31953
completed the live check, authentication and unchanged read-only metadata
command. Wrapper exit0,89.651s, owned leader reaped; receipt
instrumented_attempt_20261111T112512Z.json. Partial host identity/source evidence
is now available (see HOST_PREFLIGHT_RESULT_20261111.md). This supersedes the
current access-unverified status, not the historical failure records or their
unresolved exact causes. No policy, service or sign-in repair was made.

What do I know that could change the owner's decision that I have not yet said?
The longer instrumented handoff now has a successful observation, but the
checked server source differs from local files and full R3 is still incomplete.
