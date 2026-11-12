# Native encryption and transport proposal

Bot relation: BOT_RULES; runtime trading configuration not checked.

Proposal disposition2026-11-12T03:29:32Z:ACCEPTED_WITH_RISK by separate Rawls
GATE, planning scope only. Execution INCOMPLETE, NOT execution-ready. Existing R3/R10 remains
INCOMPLETE. Owner local date2026-11-11; UTC checked2026-11-12T03:23:53Z.
Initial proposal state:no client selected by owner yet. This is superseded by
the owner continuation below; MEGA remains the already-adopted destination.
Current preparation outcome:official binaries downloaded/hash-verified and
non-executable; native workflow source prepared but execution remains held.

### Owner stop and actual attempt correction,2026-11-12T04:49:48Z

R10 STOPPED by explicit owner direction; no downloaded tools may run. Before
that direction reached this chat, one continuation-authorized invocation
exited1 with status INCOMPLETE/phase verify_inputs, offsite_verified false,
owned_directory /private/tmp/cryptkeep-backup-native-9brdbcqh. The directory
contains only empty work/. Neither client was copied/executed; sandbox and
encryption stages were not reached. No native retry or source repair occurred.
Read-only verify_tools call reproduced unsafe_tool_pin_path:CLI accepted a
relative pins path, while load_pins requires absolute canonical paths. Source
acceptance did not demonstrate the real invocation; its execution-readiness
implication is withdrawn. Existing hashes/source remain unchanged. O-130 records
the omission. A corrected invocation/code decision is deferred, not silently
performed. User reordered work to reviewed local commits, then tracker v2;
Claude reviews before any push. No actual encrypted/off-server backup exists.

### Owner continuation and preparation,2026-11-12

Owner "carry out the next steps" followed the explicit adoption/download
question. Recorded as adopting restic+rclone and authorizing bounded isolated
download/preparation, not native execution or MEGA/account operations. The
earlier undecided-client statement above is historical, superseded in this
scope only. Native execution remains held.

Public API metadata pinned restic0.19.1 and rclone1.76.0 Darwinarm64 plus
archive/checksum-manifest sizes/digests in TOOL_PINS.json. Official published
target checksum lines match the API digests. GPG/GPGV were not on PATH;
neither OpenPGP signature nor independent publisher identity is verified.
No trust-store/security settings were changed. Initial sandbox DNS and Python
CA errors were bypassed by using system curl with certificate checks intact,
not by disabling TLS. Future fetches disable curlrc and use a clean environment.
Metadata-only checks found no default user curlrc files or alternate CURL_HOME/
XDG_CONFIG_HOME setting in this process; no config contents were opened.

Download library/controller and an actual native-probe source candidate have
been written. No downloaded native program has run. Library extraction tests
use synthetic Mach-O-shaped data, not software. Native policy tests likewise
use mocks/synthetic tool bytes and prove no encryption/native runtime result.

Separate initial source GATE accepted the cooperative download library WITH_RISK
but REJECTED its CLI's reused executor:spawn cancellation could leave a child,
and group signalling followed leader reaping. A dedicated backup executor now
masks SIGINT/SIGTERM through fork registration, gates work on ownership, holds
a live leader through signalling and reaps only afterward. Original helper is
unchanged; other callers were not re-audited and are parked for scoped review.

An initial47pass/1fail corrected-run result showed group-signalling EPERM.
The same failure persisted outside the app sandbox, contradicting the initial
sandbox-only diagnosis. That explanation is withdrawn; exact kernel causation
is not independently established. Holding the leader alive resolved the
observed failure. Corrected source/policy/process slice49passed1.38s,
zero failures/errors/skips, one intentional duplicate-ZIP fixture warning.
Original failed pytest_preparation_corrected.xml is retained, not relabelled
as passing; pytest_preparation_final.xml is the49-test result. XML SHA256:
cf42f872b12f231d51385032e7c4ed687e52109ce574beb2cc6d65d9eb2aa891.
Separate corrected process/CLI review is pending here; actual transfer held.

### Corrected source GATE and real download,2026-11-12

Additional source GATE required rejection of ignored/custom SIGCHLD before
fork. Both regressions failed before the guard and passed after. Final
download library/executor/CLI ACCEPTED_WITH_RISK by separate Rawls GATE at
04:26:39UTC; independently12process tests passed,51-case XML verified, no
remaining blocker in that diff. Actual native-probe source was NOT covered.

The separately approved one-shot download then completed, exit0, using the
reviewed source hashes and external TOOL_PINS digest. Actual staging:
/private/tmp/cryptkeep-backup-tools-pdaujppb/tools-darwinarm64
TOOLCHAIN.json SHA256:
866a8650d1a3570d0fe3e02d7e9022db5c10023ed022aeddbc68bc7cc5108c4e
Sanitized derived receipt retained as DOWNLOAD_RECEIPT.json. Downloaded
archive/checksum payload42929778bytes; total retained161465927bytes.
Archive hashes match pinned API/published checksums; extracted thin Mach-O64
arm64 executable-file headers checked, binaries NOT run and mode0600:

- restic0.19.1:29756850bytes,
  SHA06582569ff2f10e1935a6f12187c76db02f0bae99e6e54098f2cdc374766d768.
- rclone1.76.0:88778466bytes,
  SHAda7c43d491e41966f4af7f5f4ac34f7dac2c8866e3675393ef0316ebc57ccd42.

Subsequent author read-only hash/mode/size check agrees with the receipt.
No global install, PATH/.venv change, login, native-client execution, key setup,
MEGA access, transfer, service/schedule/trading operation or file cleanup.
No OpenPGP/publisher signature verified; HTTPS/checksum provenance only.

Source bindings:download libraryd1d7782b...,CLI43e16518...,executorc2abbacf...,
TOOL_PINsa048a74d.... Original companion executor unchanged. Full author
nine-file source slice232passed13.85s, zero failures/errors/skips, one
intentional duplicate-ZIP warning; XMLpytest_all_preparation.xml SHA
899f04ae7cb13d5c226955e121ec6781f9b30c62d4b6460a403ebd3dd0083358.
This preceded the final native-policy negative-control clarification below;
it is NOT a single final240-case run or full-suite/native-encryption proof.

Native-policy source was then strengthened using restic0.19.1 scripting docs:
wrong-password evidence requires exit12, not generic failure; corruption
evidence requires exit1 and JSON summary naming the actually modified pack.
https://restic.readthedocs.io/en/stable/075_scripting.html#exit-codes
Final native-policy tests19passed0.26s, including8additional negative-control
checks. The worker now keeps CBP_STATE_DIR on synthetic state after fixture
patches unwind. Native source SHA
7cf300d1d03b2a8dcfd027ea4756a901546c4ec25c426538e6e6199ef885f754;
tests SHAaf3adab457a924ed53d2fe53bd184dbce5ddaa922baedec5a5b3952ab391bb2c.
Separate source-only readiness review pending; no native-client operation.

Earlier native candidate scripts/research/probe_group_a_backup_native.py was
a guarded workflow with11synthetic controller-policy tests at that stage. Its
SBPL/runtime enforcement, CLI behavior, wrong-key/corruption checks and actual
encrypted recovery are unverified. Work-state size checks are observed refusal
thresholds, not a hard filesystem quota. Tool copies are separately bounded
and not included in the128MiB work-state count. Source is not accepted for
native execution merely because the download library is accepted.

### Final source review and budget correction,2026-11-12

SHOWN separate Rawls native-source GATE initially rejected the parent budget:
tool verification preceded a fresh300second worker allowance. This contradicted
the proposed overall bound; it did not cause a native overrun because no client
ran. Both synthetic9second/301second parent-preparation tests fail before the
correction. One absolute deadline now includes parent preparation, tool/image
verification is the worker's first phase, and exhausted preparation starts no
worker. Corrected source SHA256:
28530fa0b6cce29de866b7409f5d1d62d2148f8bca7c4716051a02bef34834db
Policy tests SHA256:
0ce419abf03c769e56e94d8ccde8b85e52365f66a559fbd703b7c4c7ad2f54bc
Author21policy tests pass0.232s; final XML SHA256:
c2017e24575dd3040046a227ad9264af57e6fa80ffec7014dae4fae5c9f16845.
Separate diff-only Rawls GATE04:40:50UTC ACCEPTED_WITH_RISK, native-controller
SOURCE ONLY:independently reproduced both regressions failing before, then
21policy tests passing0.22s after. No remaining material blocker in that diff.
Native SBPL enforcement, executable interoperability, real wrong-key/corruption
behavior and encrypted recovery remain UNVERIFIED; source acceptance does not
authorize downloaded-client execution. See INDEPENDENT_REVIEW.md.

Requirements DONE:toolchain adoption, pinned isolated download and hash/mode
verification, process/controller/isolation source, focused synthetic tests and
independent source review. PARTLY DONE:provenance is HTTPS/checksums, not signing
verification. NOT DONE:native local test, MEGA account/quota/authentication,
off-server transfer/restore, dedicated key provisioning, retention or service
integration. No native execution, account/host/service/schedule/trading change,
commit or push. Failure fixtures/receipts are preserved; no cleanup is claimed.

Final consolidated author run2026-11-12T04:44:38Z:242passed14.68s,
zero failures/errors/skips, one intentional duplicate-ZIP warning. This is
the nine-file focused source/synthetic slice on the final controller, not the
full repository suite or native encryption. Command:CBP_STATE_DIR=<new owned
temporary path> PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest
-q -p no:cacheprovider tests/test_group_a_backup_process.py
tests/test_group_a_backup_tools.py tests/test_group_a_backup_native_policy.py
tests/test_group_a_backup_prefix.py tests/test_group_a_backup_acquisition.py
tests/test_group_a_backup_bundle.py tests/test_sqlite_backup.py
tests/test_state_backup_restore.py tests/test_group_a_unit_composition.py
--junitxml=docs/review_artifacts/group_a_backup_native_20261112/pytest_consolidated_final.xml.
XML SHAa3995bd0e8212669357bb1eb8a24c0bae46a377bac005d15b09cc656ce2edade.
This consolidated run is self-checked; separate reviewer ran the specific
before/after regressions and21final policy tests, not all242. Scoped tracked
documentation diff check passes. Whole-worktree diff check fails on pre-existing
CRLF/trailing whitespace in paper_ledger.csv; that artifact is left unchanged.

## Recommendation

Propose restic for a separately keyed encrypted backup repository and rclone
for MEGA transport. Reuse the accepted bundle/prefix acquisition and restore
checks. Do not implement new encryption, substitute MEGA-only account
encryption for the separate backup-key requirement, or change providers.

Before any account access, prove the actual client stack locally:an isolated
rclone local remote, real restic repository encryption, backup, full read-data
integrity check, fresh restore, existing manifest verification and recorded
decision replay. Also require wrong-key and modified-ciphertext failures.
This can establish native local encryption/recovery and client interoperability,
not MEGA login, cloud durability, quotas, a deletion-restricted credential or
off-server recovery. No offsite_verified=true may follow from local proof.

SHOWN local availability:uname -sm returned Darwin arm64. command -v found
no restic/rclone/MEGAcmd/age commands in the current PATH. This is not a full
disk/app inventory. No native tool executed or account/config inspected.

## Primary sources actually opened

- Restic preparation docs support rclone repositories, with restic starting
  and stopping its rclone child and configurable program/arguments. This is
  documented capability, not project compatibility or process-cleanup proof:
  https://restic.readthedocs.io/en/stable/030_preparing_a_new_repo.html#other-services-via-rclone
- Restic restore and repository-check docs describe recovery and read-data
  verification. Actual binaries/flags/version behavior remain untested:
  https://restic.readthedocs.io/en/stable/050_restore.html
  https://restic.readthedocs.io/en/stable/045_working_with_repos.html
- Rclone MEGA docs expose a 2FA input and warn about repeated-login blocking,
  duplicate names and absent backend hashes/modification times. Account state,
  unattended MFA/session behavior and actual failure frequency UNVERIFIED.
  Never weaken MFA/password policy to accommodate an example workaround:
  https://rclone.org/mega/
- Official MEGAcmd supports session/MFA login but uses a persistent background
  server and private local session cache. It remains an alternative, not an
  automatically started fallback/helper or new sync schedule:
  https://raw.githubusercontent.com/meganz/MEGAcmd/master/UserGuide.md
  https://raw.githubusercontent.com/meganz/MEGAcmd/master/contrib/docs/commands/login.md
- Opened public latest-release API endpoints. No exact binary version/digest
  is pinned by this document; no native archive was downloaded or executed:
  https://api.github.com/repos/restic/restic/releases/latest
  https://api.github.com/repos/rclone/rclone/releases/latest

## Proposed one-pass native proof, requiring owner authorization

1. Resolve and retain exact official Darwin-arm64 versions, URLs and published
   checksums before download. No moving-latest execution, package manager,
   sudo, global PATH edits, .venv changes or provider/account commands. Verify
   downloaded bytes before execution; disclose the actual authenticity evidence
   and stop if the reviewed provenance requirements cannot be met.
2. Download only the two standalone clients into an owned private test-tools
   directory, at most200MiB/180seconds, no automatic retry. Keep binaries out
   of Git. Downloads create retained local files/cache; no daemon or sync job.
3. Prepare the actual bounded controller and run synthetic/offline policy
   tests plus separate review before native execution. Native proof is not
   authorized merely by accepting this proposal. Freeze controller/tool hashes,
   argv/environment, dependencies, isolation and cleanup ownership first.
4. One foreground native test, at most300seconds including owned cleanup,
   at most8MiB synthetic inputs/128MiB test state; clean private HOME/config,
   synthetic test key only, no existing secrets. Enforce no network during
   native execution and no reads outside required runtime/tool/test paths.
   Stop if isolation/prerequisites cannot be established. No services, existing
   containers or servers. No hidden retry, repository unlock/reset or deletion
   of anything outside the test's exact ownership list.
5. Real init/backup/check/restore through the local rclone transport, external
   manifest and existing prefix/replay checks. Corrupt only an owned duplicate
   test repository; preserve the successful evidence. Wrong-key/corruption/
   timeout/unsafe-destination cases must not produce a successful receipt.
   Fixed/sanitized receipts only; do not persist key values or raw diagnostics.

The exact controller does not exist yet and cannot be approved by prose.
Published checksum matching is not, by itself, independent publisher-signature
verification. Native tests may fail, leave owned partial files or need process
cleanup; the actual runner must bound that behavior before it is used.

## Separate remaining operating decisions

MEGA account/quota/authentication, dedicated backup key storage and recovery,
retention/pruning and native service/provisioning still need actual evidence.
Never switch to TeraBox, create public links, remove MFA or prune provider
objects automatically. No monthly cost or financial return is inferred.
Existing full-config/source-provenance/R10/R11 gaps remain recorded.

## Independent proposal review

SHOWN separate Rawls reviewer01a1c9d6-7c8d-7c12-86ce-08152156ac6d read
the full proposal/task card and relevant official docs; log/Git checked
2026-11-12 03:29:32UTC. ACCEPTED_WITH_RISK for proposal only, no blocking
planning defect. Confirmed documented restic/rclone transport, not native
MEGA compatibility. Exact binary provenance, controller/process ownership,
enforced isolation and resource bounds remain unproved. Published checksums
alone are not publisher-signature proof. No reviewer download, install,
native execution, account access or file changes. One owner decision remains:
adopt the stack for bounded download/preparation, with execution held until
the separate controller/tool/isolation GATE and applicable authorization.

Historical proposal checklist (before owner continuation):
DONE:this source-fit/proposed proof boundary. NOT DONE:owner adoption of the
toolchain/download/native-test scope; actual controller and independent source
proof; binary pin/download/verification; native encryption/recovery; MEGA or
service operation. No source/config changes, installs, credentials, native
client actions, uploads, schedules, services, trading, commit or push.

What do I know that could change the owner's decision that I have not yet said?
The local source tests cannot establish that either native program works here
or that MEGA authentication will work unattended. Real local encryption and
recovery is the next useful proof; choosing this stack is not cloud readiness.
