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

## Separate invocation-path correction GATE,2026-11-12T17:15:37Z

Bot relation:STANDALONE; runtime trading configuration not checked.

Reviewer:Darwin,01a1d038-a33c-7da1-926e-c4fe2e2c3e1e,separate from author.
Disposition:ACCEPTED_WITH_RISK for offline invocation-path source repair only,
no blocking findings. This is a normalized receipt of the returned separate
review,not a new native run or a replacement for earlier review history.

SHOWN relativepins anchored lexically to invocationcwd,absolute inputs unchanged;
no symlink/'..' resolution before existing strict validation. Sharedload_pins,
toolverification and executor source unchanged. Worker/shareddeadline/noexecute
earlyreturn unchanged; existing tests retained verbatim. Existing concurrent
same-UID path-mutation assumptions remain outside this narrow correction.

Independent command:

```sh
env CBP_STATE_DIR="/private/tmp/cryptkeep-r10-gate-synthetic-state-$$" \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_group_a_backup_native_policy.py \
  -k 'pins_cli or no_execute_flag or parent_preparation'
```

VERIFIED_ENV:9passed,18deselected1.69s; six newpathcases,noexecutecontrol,
twodeadlinecases. Read-only baseline comparison and scopedgitdiffcheck passed.
Author's before1failed/5passed and final55passed are CLAIMED to reviewer by
work-log/test-output records, not independently rerun. Prior242notrefreshed.

Reviewed hashes:
- scripts/research/probe_group_a_backup_native.py:52f54b469b48151c41b4470f663d15c3d45738041552623f902486f9aa1624ce.
- tests/test_group_a_backup_native_policy.py:f8de09d743186528c85245b610d28f6ab98f181c7c01683379821631098eae98.

No reviewer edits, actual staged-tool reads, native/controller execution,
network/account/server/service operations, installation, commit or push.
Native isolation/interoperability/encryption/recovery/cloud durability remain
UNVERIFIED; operational R10 held. Current17:16:11UTC authorreadback matched
bothreviewhashes; source frozen after review.

What do I know that could change the owner's decision that I have not yet said?
The repair makes a relativepins invocation consistent with the existing strict
verifier, not a working encrypted backup. Only separately authorized native
execution can establish the next evidence; this review grants none.

## Separate bounded-diagnostics GATE,2026-11-12T17:36:56Z

Bot relation:STANDALONE; runtime trading configuration not checked.

ReviewerDarwin01a1d038-a33c-7da1-926e-c4fe2e2c3e1e,not author,returned
ACCEPTED_WITH_RISK for O135offline diagnostic-source repair only,no blockers.
This is a normalized receipt of the returned review,not new runtime evidence.

SHOWN fields limitedtotypecheckedstatus/errno,bytecounts,booleans,fixedlabels;
no rawoutput/exceptionmessage/environment/key/path copied. Marker scanfirst
4096stderrbytes only,notcausality. Per-canaryresets avoidstalereceipts and fields
attach onlyto3sandboxfailurephases. Reviewercomparisonagainstexactaccepted
52f54b46...source confirms_command/profile/executor/timing/CLIpathrepair/
nativegates unchanged; failures stillstop. No weaker isolation/native preflight.

Independent command:

```sh
env CBP_STATE_DIR="/private/tmp/cryptkeep-o135-gate-synthetic-state-$$" \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  ./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_group_a_backup_native_diagnostics.py \
  tests/test_group_a_backup_native_policy.py
```

VERIFIED_ENV:41passed0.46s. Scoped diffcheckpassed. Author14beforefailures/
final69passconsolidatedresult are CLAIMED to reviewer,not independentlyrerun.

Exactreviewhashes:
- scripts/research/probe_group_a_backup_native.py:51161a9d3899fa9d4247cc31a32c31f8e26db9a9b8ef3da0b4af67b524960745.
- tests/test_group_a_backup_native_policy.py:965a3e71b3bb7199d3a5161bfb6e4ded372de0c6be03ff1ed41189a77001c1ac.
- tests/test_group_a_backup_native_diagnostics.py:25aa744faf33c5870c9e99718eff0d0ad74851ffda3fda9de555fda8bdb1967a.

No revieweredit/stagedclientread/nativeprobe/sandbox/network/operationalaction,
install/commit/push. Earliercause UNVERIFIED,discardeddetailsirrecoverable;
realdiagnosticusefulness/sandbox/encryption/recovery stillunproved. Acceptance
doesnotauthorizearetry. Authorpost-review17:37:46UTChashesmatch; sourcefrozen.

What do I know that could change the owner's decision that I have not yet said?
Better diagnostic reporting is not a sandbox fix, and synthetic rejection
tests do not establish why the previous actual command failed. A new real
observation would require separate approval and could still be inconclusive.
