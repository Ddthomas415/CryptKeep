# Minimal reconnection plan, October 24

Roles by stage: DIRECTOR plan, then ENGINEER offline inputs. Risk: HIGH.
Plan and fresh inputs separately ACCEPTED_WITH_RISK; inert CLI validation passed.
Runtime: INCOMPLETE. Offline design only; no operational authority.

Chosen path: reuse the existing four-application staged preparation, actual-ID
review and separately bounded cutover. Three storage services stay untouched.
No application rewrite, new controller, model, collector or deployment framework.
Two sampled legacy main files motivate the update; they do not prove all four
apps defective. Four apps are the existing reviewed lifecycle/recovery unit.

Full plan and side effects:
`docs/review_artifacts/companion_reconnection_plan_20261024/plan.md`, SHA256
`c08e107aac535ca0ac700e9b3358c90b7098ca3a37a23f6695ecd2611be87b90`.
Reuse proof:
`docs/review_artifacts/companion_reconnection_plan_20261024/reuse_proof.json`,
SHA256 `776b4142a4b976c8408e3a401a5d841f1126ae609cf4e635934720adcd547820`.

SHOWN locally: all43application-source entries and13preparation-tool hashes
match the prior reviewed inputs. Existing baseline projection/fingerprint code
accepts the saved inventory identity/configuration constraints; only four app
start timestamps differ. Storage baseline deltas are empty. This is not live
preflight, installed-source equivalence, image-cache or dependency-policy proof.
The43deduplicated selected input/source bindings are distinct from the43app-entry
count and are not a complete runtime dependency audit.

VERIFIED_ENV:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_reconnection_plan.py tests/test_companion_evidence_packet_v2.py
```

Six passed in0.65s, including two new plan-proof cases. Full suite not run.
Tests forbid network/process calls; review/input drift refuses. Only the new
test/reuse report/plan/docs are authored. No new manifest, attempt, reservation,
image/container, credential, native, HTTP/DB or application operation occurs.

Next design gate: independent review of this bounded reuse path. Next safe
implementation, if accepted, is fresh offline input derivation using the existing
pure recipe, adapting the new observation shape without rewriting its evidence.
Only then may an independently reviewed, inert-validated preparation packet be
presented for a separate stopped-preparation decision. No cutover/start/query,
old-ID/attempt reuse or automatic retry is included.

## Accepted plan and completed offline input derivation

Separate plan GATE ACCEPTED_WITH_RISK, no blockers. Review SHA256
`f0f3d0ff17b359bc6fe1f10d27876787ed586dc6f66fed84b58efcc707733ca4`.
Reviewer reproduced reuse proof, verified43selected bindings/13consumers/43app
entries and independently passed two new tests in0.14s. Parent read full review
and verified47direct/inherited bindings unchanged. Plan acceptance grants no
preparation or runtime operation.

Continued routine offline derivation through the exact existing pure recipe:

- `derive_preparation_inputs.py`, SHA256
  `6f724e6b04b3b79eff4d36b4297fc83001cc711eb4775a16bcd4475dc610edfb`.
- `fresh_inputs/candidate_manifest.json`, SHA256
  `4c0512d6f5e737653d1067bdd28185acb76258753dd2a231e56d4fa127c4aad6`.
- `fresh_inputs/provenance.json`, SHA256
  `9407ddedf5b573286af1de56c7c867fe5a09d3e8bfa31bf6f4e14fc0a7f31fed`.

Paths are under the plan artifact directory. No existing file was overwritten.
The wrapper imports exact reviewed helper bytes under a non-main name and
supplies five fixed inputs plus unused proposed label `workerprep20261024v6e`.
The new inventory's paired row arrays are projected in memory to the earlier
recipe schema after raw-hash verification; original capture stays unchanged.
The derived projection has a separate hash. Generic inherited commentary about
older exited-state captures is historical, not a claim that the new capture
required exited containers. The explicit new schema-adapter field identifies it.

The new candidate changes only attempt, decision/reviewer reset and baseline
relative to prior accepted preparation. Four app start times change; commands,
policies/options/applications/network contract remain unchanged. Candidate is
INCOMPLETE with empty reviewer and is refused by the real loader. Old staged
rows are configuration models, not future IDs. New IDs/images remain null.

Both old V6d consumed marker paths still exist. Both proposed V6e marker paths
were absent before/after derivation; absence is not a reservation or proof that
future daemon names are free. No directory under operation state was allocated.

Final focused command:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_fresh_preparation_v6e.py tests/test_companion_reconnection_plan.py tests/test_companion_evidence_packet_v2.py
```

**14 passed in0.65s**, including eight new input cases. Full suite not run.
Native/network calls forbidden. Tests cover exact delta, unchanged capture,
source/helper drift, consumed new label and identity/state/config/restart drift.
Actual candidate is never self-approved; temporary accepted values in one test
are explicitly synthetic loader-composition fixtures.

Separate input review accepted. Actual preparation CLI default validation passed
offline with native/reservation tripwires, as recorded below.
No `--execute-preparation`, build, image inspection, config copy, create, startup,
cutover, token/query or reset is part of this stage. Witness integration remains
non-effective until a fresh actual-ID runtime packet is reviewed later.

## Accepted inputs and actual inert command

Separate input GATE ACCEPTED_WITH_RISK, no findings. Review at
`fresh_inputs/inputs_independent_review.json`, SHA256
`68a7e008f9a84541db7b7484cf67c6e6e5e41f96a8cee872e464bcfec208423b`.
Reviewer reproduced candidate/provenance exactly, checked53distinct bound files,
verified schema adaptation/unchanged scope/old consumed markers/new absence,
and independently passed eight new tests in0.18s. Parent read the full review.

Reviewer created `fresh_inputs/reviewed_preparation_manifest.json`, SHA256
`2075f3b98abc53be9e8336d425dd8d158aca4b1934a1b9da46c2ae9d3cd562d4`.
Only decision/reviewer fields differ from the candidate; the final newline is
included in the trusted hash. This accepts preparation inputs, not an operation.

Parent verified54bound files including the derivative, then called the actual
`companion_prepare.main` default mode against it, with no execution flag.
Subprocess/socket/backend/reservation/lock tripwires were active; `os.open` was
restricted to that exact manifest. Exit0; one manifest open; actions false,
startup authorization false. No new marker before/after. Receipt:
`fresh_inputs/inert_validation.json`, SHA256
`22456fc9f5171b4fdd8c44bbb0891a7e6369a6c68a8881cd6365244f6b1d1e8b`.
This parent-performed check was not independently rerun and establishes no live
engine/cache/image/configuration or runtime compatibility.

The offline plan/input/inert-proof work is complete. No more speculative source
repair or blanket audit is proposed. The next decision is one actual stopped
preparation: existing controller may build/reuse four local source-only images
and copy existing private service configuration into four new stopped containers;
original applications and storage remain untouched. Existing300s controller
budget includes120s recovery, not a whole-command hard wall. Cache/config/log
effects may persist and cleanup is not guaranteed. No startup, cutover, token
query, old-attempt reset, trading or subsequent automatic operation is included.
If authorized later, actual new identities must be independently reviewed before
any separately authorized cutover/query. Runtime remains INCOMPLETE.
