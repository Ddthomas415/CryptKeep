# V6e runtime packet and fixed handoff, October 24

Role: ENGINEER. Risk: HIGH. Packet and fixed handoff separately ACCEPTED_WITH_RISK,
offline scope only. Implementation and independent review complete.
Runtime/explanation: INCOMPLETE. No new operational authorization.

## Scope and change

Continue the accepted research-service reconnection objective, not a general
readiness audit. Assemble offline around the four separately reviewed stopped
replacement IDs from the V6e preparation. Preserve originals, storage, prior
attempts and all old evidence. No Docker call, credential read, startup, query,
reservation or reset is part of this scope.

Artifacts are under
`docs/review_artifacts/companion_reconnection_plan_20261024/`:

- `assemble_runtime_packet_v6e.py`: exact-hash reuse of the existing V6c assembler,
  adapting immutable V6e evidence schema without rewriting source evidence.
- `runtime_packet_v6e/`: twelve generated proposal artifacts. Draft policies
  remain UNVERIFIED, review decisions INCOMPLETE and reviewer fields blank.
- `tests/test_companion_v6e_runtime_packet.py`: fifteen offline cases, including
  real-loader composition with synthetic reviews confined to temporary files.

SHOWN: seven subjects, the same three storage subjects, four new reviewed app
IDs, 132 source pins. Of those pins, 43 are direct V6e application witnesses and
89 are inherited exact-image/storage evidence, not recaptured. Preparation has
13 consumer bindings; the runtime proposal explicitly adds seven current client,
guard and evidence-verifier bindings. This is not full host dependency closure.

The archived witness set is exactly the separately reviewed records 7, 5, 47,
18; no forced ranking or question/body/lineage relaxation. The previously
accepted headline-context correction is bound explicitly. Neither change proves
the exact historical failure cause or a working live explanation.

Three prior policy meanings and seven limitations remain unchanged. A reviewer
must independently assess their applicability to these actual IDs and consumers;
the assembler itself creates no accepted policy or runtime authority.

## Verification

VERIFIED_ENV:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6e_runtime_packet.py tests/test_explain_headline_context.py tests/test_companion_witness_proposal.py
```

SHOWN: 63 passed in 1.28 seconds. Native/network/reservation tripwires are active.
These cover offline inputs/guard/witness behavior, not current Docker state,
stored evidence, connectivity or startup. Full suite not run. The earlier
eight-case development pass is not an additional independent result.

## Separate packet review and actual inert validation

Independent GATE ACCEPTED_WITH_RISK, no findings. Review SHA256
`11a44e4bb8f50bf2beca653c4a989f01dd5381a70eb88d991365671e0b039598`.
Reviewer reproduced all twelve draft bytes, ran the fifteen packet cases
(15 passed in 0.35 seconds), and verified the real pure loader. It created a
separate scope, seven child records and a V2 runtime record. Three meanings and
seven limits retained verbatim. This accepts exact source/config applicability,
not startup, current health, loaded imports or runtime success.

Parent read the complete review, verified 65 unique bound files and checked the
three meanings/seven limits against prior scope. Then invoked the actual
`companion_cutover.main` default mode with subprocess/socket/backend/token-read/
reservation/flock tripwires: exit 0, input bindings validated, actions false,
startup false. The cutover marker was absent before and after. Receipt SHA256
`f07246611c18f3ef23b7c1256e9cd5de543e54fb33e1f688b7a803ed08a3df8b`.
No native or credential operation occurred.

## Fixed launcher

`execute_reviewed_v6e.py` is the reviewed prior V6d launcher flow with only
version labels, the new attempt and four fixed record digests changed. Default
is inert. Only an explicit separately authorized execution flag can enter its
existing private-token-source/pipe handoff. It binds all twenty current consumer
files, exact subjects and all accepted records before any token access.

VERIFIED_ENV isolated pytest command as above, substituting
`tests/test_companion_v6e_handoff.py`: 26 passed in 0.28 seconds. These reuse the
23 earlier synthetic handoff cases and add exact-delta comparison and two new
host guard/verifier drift refusals. All token responses are synthetic. No real
token was read; full suite not run.

Separate handoff review ACCEPTED_WITH_RISK, no findings. Review SHA256
`e9e82b9a50d2f67ca329e510d1fa4f992805021208bdbb20543be6bf482924cd`
at `runtime_packet_v6e/handoff_independent_review.json`. Reviewer independently
ran all 26 tests (0.32 seconds) and the actual default module via runpy, with
additional pipe, temp-directory, core-limit and write-open tripwires. Exit 0;
no tripwire calls; stdout matches the inert receipt; cutover marker absent
before/after. Parent read the entire review and verified all 43 listed bindings.
Reviewed source/tests/receipt/policy records remain unchanged.

The lexists check before a future token read is advisory, not atomic exclusion;
the existing controller lock/reservation remains mandatory. Cleared Python token
references are not secure zeroization. No whole-wrapper deadline, loaded-code,
current service, data-integrity or successful-query proof is implied.

No operation may be inferred from a passing offline packet. The next action is
the operator's separate bounded authorization: one call,
600-second controller including 180-second recovery reserve; CLI and token-source
prechecks each at most ten seconds precede that budget, not a total wall-time
guarantee. Four applications only; three storage services/volumes and trading
remain untouched. Existing fresh-state/installed-source/recipient/archive/citation
gates remain mandatory. Failure recovery is not guaranteed and logs/audit writes
may persist. No automatic retry or receipt reset. Preparation remains consumed.

If authorized, the existing fixed handoff privately reuses the original internal
service token, gracefully stops only the four original research applications,
activates the four prepared replacements and runs the existing checks plus one
cited-evidence query. It leaves replacements running only on complete success;
failure invokes owned cleanup/restoration. The three storage services, persistent
volumes, accounts, trading and schedules are outside the mutation scope. Current
state must pass existing preflights; this document does not waive drift refusal.

This completes the accepted offline packet/handoff objective. Runtime remains
INCOMPLETE until an authorized attempt actually proves the explanation path.
