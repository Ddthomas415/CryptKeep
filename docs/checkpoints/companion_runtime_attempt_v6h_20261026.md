# Actual V6h Runtime Attempt, October 26

Implementation role: ENGINEER. Risk: HIGH.
Separate GATE outcome: ACCEPTED_WITH_RISK, saved failure evidence only.
Runtime INCOMPLETE. No retry or additional operation authorized.

## Authorized action

Direct operator selected one bounded runtime attempt: private existing-token
reuse, graceful stop of four original research apps, start four reviewed
replacements, mandatory checks and one frozen cited-evidence query. Three
storage services/volumes, trading and schedules untouched. Success requires all
checks; failure invokes owned cleanup/original restoration, not guaranteed.
600-second controller includes 180 recovery; separate ten-second CLI and
token-source checks precede it. Logs/audit effects can persist. No auto retry/reset.

Offline preflight checked 102 nonhistorical handoff-review bindings; its
pre-closeout checkpoint exception is explicit. Preparation consumed/cutover
marker absent beforehand. Fresh actual identity/source/configuration/SDK/
namespace/recipient/health/lineage/evidence checks were left to the controller.

Exactly one invocation, execution session 33805, exit 1:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6h_20261026.execute_reviewed_v6h --execute-once
```

## Actual result and recovery limits

SHOWN tool result: actions/services started/query attempted true, query passed
false, receipt complete, running update incomplete. Failure stage is runtime
verification. Controller reports configuration rollback verified, exact baseline
restoration false and no tracked unresolved operations. Prepared IDs reported
not preserved, preparation consumed. There was no repeat, native postcheck,
new preparation, new query or marker reset after this invocation.

Receipt records replacement quiesce/removal, original name/network restoration
and four original restart intents. Final recovery attestation:
configuration_restored true, exact_baseline_restored false,
network_connectivity_verified false. It is not proof of current health,
connectivity, volume-byte equality or exact restoration. Do not reuse the
consumed attempt or removed replacement IDs as new approved inputs.

## Diagnostic finding

The companion returned HTTP 200, five citation hashes and execution disabled;
client normalization accepted it. Recorded provider fallback is deterministic
research fallback, not a proven LLM response. No recorded foreign-asset or static
dashboard fallback rejection occurred. This client boundary passed, not the
complete explanation acceptance contract.

The stored-evidence verifier returned a valid closed diagnostic envelope:
stage bundle_market, code rejected, outcome complete, shape_valid true, all
five check fields false. This identifies a market-bundle rejection group. It
does not identify the exact predicate/field/value, and five false results are
not five independent failures. No raw response/market payload or live DB rows
were retained or reconstructed. The V6g first failure is still unknown.

Local source inspection and a two-case offline test show a producer/consumer
contract mismatch: shared.tools._default_market_snapshot("BTC") emits an
explicit unavailable snapshot (asset BTC, symbol BTC/USDT, ok false, null prices,
source unavailable, reason market_service_unavailable) which the real bundle
builder retains. The verifier allows a smaller market-field set and expects
no_market_data, so this legitimate producer shape is rejected at bundle_market.
The old controlled fixture omitted that snapshot entirely and still passes.
This is a SHOWN standalone incompatibility, not a live replay. Independent
review found the strict probe bypasses this standalone snapshot function;
do not promote this counterexample into the actual cause or sufficient repair.

No verifier rule, acceptance criterion, source implementation, archive, witness,
dataset or frozen question was changed. Do not loosen checks or rerun to force
acceptance. First follow the strict signal-market producer path, retaining
identity, null-price/no-market-evidence and all other gates. See the follow-up
companion_strict_probe_market_diagnosis_20261026.md.

## Preserved records and verification

Directory: docs/review_artifacts/companion_integration_inputs_v6h_20261026/actual_runtime_v6h/.

- receipt.jsonl: byte-identical controller-state copy, 98 events, SHA256
  ab587bb2fa1a56818b2c70f45cafc29b543e4ae3efba83c006ac696021d91b4a.
- outcome.json: explicit parent transcription of session 33805, not independent
  process-output capture.
- diagnose_saved_result.py and diagnosis.json: reproducible local receipt/hash/
  archive correlation. Five document/URL-hash pairs map to [5,47,18,5,26]; this
  is not completed persisted-identity/content/topical/causal verification.

VERIFIED_ENV offline diagnosis, exit zero:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B -m docs.review_artifacts.companion_integration_inputs_v6h_20261026.actual_runtime_v6h.diagnose_saved_result
```

Offline counterexample verification:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_v6h_market_contract_diagnosis.py
```

SHOWN: 2 passed in 0.24 seconds. Only pure functions compiled from current
producer source; no app/Settings/SDK/client initialization or real network.
These are diagnosis tests, not a repair or proof of live success. No full suite.

## Handoff

Separate GATE read all 98 events, verified state-copy equality, reproduced
diagnosis and ran both tests once (0.22 seconds). Saved evidence accepted with
risk. Finding V6H-DIAG-01 blocks treating the standalone counterexample as the
actual cause: strict tooling retrieves signal/risk only, not market snapshots.
Parent verified all 114 bound hashes before this documentation-only closeout.
Review SHA256 a79199bed7c7fbd3212313d98055e4154d2faf73c424ca3dc9d291df9e649df9.
Its checkpoint digest identifies pre-closeout text; receipt/outcome/diagnosis/
tests and production sources remain unchanged.
Approved one-attempt scope is spent. Next targeted decision concerns the market
snapshot contract, not another blind cutover. Service restoration remains
INCOMPLETE and present operational health UNVERIFIED.
