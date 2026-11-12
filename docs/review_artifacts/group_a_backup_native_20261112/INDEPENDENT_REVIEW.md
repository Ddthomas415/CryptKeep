# Independent source review

Bot relation: BOT_RULES; runtime trading configuration not checked.

Checked2026-11-12T04:42:28Z; HEAD82b5f216e, existing dirty work preserved.
Reviewer:Rawls01a1c9d6-7c8d-7c12-86ce-08152156ac6d, separate from author.
This report records actual reviewer tool responses, not self-certification.

## Disposition

SHOWN download/executor/CLI source ACCEPTED_WITH_RISK04:26:39UTC.
SHOWN native-controller source ACCEPTED_WITH_RISK04:40:50UTC.
UNVERIFIED native sandbox/runtime, local encrypted recovery and MEGA operation.
No client execution or operational authorization is implied by either GATE.

## Findings and corrections

- Initial download CLI REJECTED:reused helper could leak a child on spawn-time
  cancellation and reap the group leader before signalling. Independent real
  synthetic cancellation reproduced the leak; reviewer cleaned/reaped it.
  Dedicated gated backup executor now masks SIGINT/SIGTERM through ownership
  registration, retains a live unreaped leader, signals only while fenced,
  and reaps afterward. Original companion helper is unchanged, older callers
  not re-audited; their accepted-state impact remains UNVERIFIED/parked.
- An EPERM test failure was prematurely attributed to app sandboxing. The same
  escalated test failed, contradicting that explanation. A live-leader hold
  resolves the observed test; exact kernel causation is not independently
  established. Failed XML is retained.
- Corrected executor initially omitted SIGCHLD-context refusal. Independent
  SIG_IGN probe failed after fork. Default-SIGCHLD precondition now rejects
  ignored/custom handlers before fork. Reviewer independently reproduced both
  guard regressions failing before and12process tests passing after, and
  verified the51case source XML. No PID reuse/misdirected signal observed.
- Native controller initially put tool verification outside a fresh300second
  allowance. Independent review demonstrated synthetic9+300seconds. Corrected
  absolute attempt deadline includes preparation and verification;301second
  simulated preparation starts no worker. Reviewer independently reproduced
  both clock regressions failing before and21policy tests passing0.22s after.
  No remaining material blocker in this diff.

## Accepted identities

- Download library:d1d7782b788206ced089cc3977cd56bd964e4e94e5666bf122baf57e5ec3ccbd.
- Download CLI:43e165181458849fdec56d56b109abce552b8b7e99bfd564fad20686011e5595.
- Owned executor:c2abbacf7031b82ab30257f8a3d291f55ef14a67421c5a5bb9f80c30eb99cf73.
- Native controller:28530fa0b6cce29de866b7409f5d1d62d2148f8bca7c4716051a02bef34834db.
- Native policy tests:0ce419abf03c769e56e94d8ccde8b85e52365f66a559fbd703b7c4c7ad2f54bc.
- Tool pins:a048a74db7342f18c3a16d591f951e0564f57d9d8b45e687ef1513b3b3ca8041.
- Actual staged TOOLCHAIN receipt:866a8650d1a3570d0fe3e02d7e9022db5c10023ed022aeddbc68bc7cc5108c4e.

Reviewer independently checked staged receipt/archive/binary hashes and mode0600.
Actual archives were downloaded once by the approved author action, not by the
reviewer. Binaries have never been executed. Publisher-signature verification
was not performed; HTTPS/checksum agreement is weaker evidence.

## Limits and proof still required

Source/synthetic acceptance is not native process isolation or interoperability
proof. The300second controller reserve does not guarantee recovery after parent
SIGKILL or uninterruptible kernel I/O. The128MiB work-state monitor is a refusal
threshold, not a filesystem quota; copied tool bytes are separately bounded.
Private owned paths assume no hostile concurrent same-UID mutation. No private
configuration/credentials, existing accounts/databases, MEGA, host, service or
trading path inspected. No full suite, CI or native encryption test performed.
Current task stops at completed download/preparation. A separately authorized
local synthetic native test is the next evidence, not automatic cloud setup.

What do I know that could change the owner's decision that I have not yet said?
Even a successful local encrypted restore will not prove unattended MEGA login,
remote durability, key recovery, retention or complete operating backup coverage.
