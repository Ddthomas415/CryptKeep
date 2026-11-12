# Correction to the SSH approval handoff

Bot relation: BOT_RULES; runtime trading configuration not checked.

Role: AUDITOR. Checked 2026-11-11T03:40:05Z (November 10 New York).
Intended-host proof remains INCOMPLETE; no new connection was made to investigate.

## What happened

SHOWN: after the owner confirmed the first SSH check, the single authorized retry
again printed an additional-check URL and ended with exit 255/timeout. No remote
JSON or inventory returned. Receipt: `owner_confirmed_host_preflight_20261111T033529Z.json`.
The owner confirmation is preserved; it is not treated as a failure to approve.

SHOWN workflow defect: the earlier URL was presented to the owner only after the
associated SSH process had exited. That is not a reliable interactive approval
handoff. The five-second connect deadline and then a fresh connection do not
provide a deliberate live window for the human check. The exact effective check
period, whether that old URL remained usable, and why approval did not carry over
are UNVERIFIED. We did not inspect or alter the tailnet access policy.

## Primary-source checks and their limits

Tailscale documents additional verification during SSH initialization and permits
`checkPeriod=always`, so some policies require a check on each new connection.
That is a supported possibility, not proof this tailnet uses that setting.
[Tailscale check mode](https://tailscale.com/docs/features/tailscale-ssh#configure-tailscale-ssh-with-check-mode)

OpenSSH documents that ConnectTimeout applies to connection establishment and
initial protocol handshake/key exchange. It is not a separately designed human
approval budget. We have not independently localized this server's check to a
specific handshake phase. [OpenSSH ConnectTimeout](https://man.openbsd.org/ssh_config#ConnectTimeout)

Tailscale's issue tracker reports that LogLevel ERROR hides the INFO-level check
banner. Our initial silent attempt used ERROR and the later visible attempts used
VERBOSE. This is consistent evidence, not a controlled reproduction proving the
first failure's exact cause. [Tailscale issue 7589](https://github.com/tailscale/tailscale/issues/7589)

Current upstream Tailscale source describes holding authorization on the connection
and canceling the delegated wait when that connection closes; deployed version is
unknown. [Upstream connection handling](https://github.com/tailscale/tailscale/blob/main/ssh/tailssh/tailssh.go)

## Smallest proposed correction, not yet executed

Use one new explicitly authorized live connection with a five-minute overall
ceiling: at most 210 seconds for connection/approval, the unchanged remote command
at most 70 seconds, and remaining margin inside a 300-second client alarm.
Keep strict existing host-key checks, one connection, no forwarding, no policy
or authentication-setting changes, and the same read-only inventory command.

Surface the new approval URL immediately while the tool still reports the SSH
process running. The owner completes the browser check; the SAME connection then
continues into the inventory. A chat confirmation must not launch another SSH
process. Preserve the running tool session ID in the local receipt for continuity.
If that process exits or the budget expires, stop. Do not send its URL as if it
were a live request, retry automatically, or claim that the owner's check failed.

No further SSH attempt is authorized by this proposal. O-111/O-112 record the
diagnostic/handoff omissions. The proposed live-handoff control is not integration
tested yet. No server facts, deployed-source comparisons or profitability claims
follow from the still-failed preflight.

What do I know that could change the owner's decision that I have not yet said?
Part of this blockage was our handoff design, not demonstrated failure of the
owner's sign-in or the host. Keep the approval connection alive rather than
asking the owner to approve a finished connection or weaken access controls.

## Dated correction, 2026-11-11T04:19:41Z

The proposed ConnectTimeout-only revision was incomplete: the actual live attempt
retained ServerAliveInterval=5/ServerAliveCountMax=1 and ended before the promised
window. It did use the same session, so replacing the connection is no longer the
observed fault. The packet-timeout correction and seven offline regression checks
are documented in `SSH_PACKET_TIMEOUT_CORRECTION_20261110.md`. No further live test
is authorized by either document; tailnet policy and server health remain unverified.

What do I know that could change the owner's decision that I have not yet said?
All client deadlines must be reconciled, not just ConnectTimeout. The short alive
deadline was missed in the first correction and is now explicitly tested.
