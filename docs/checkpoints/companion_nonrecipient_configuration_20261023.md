# Dormant Nonrecipient Configuration

Role: ENGINEER, after AUDITOR observation. Risk: HIGH.
State: READY_FOR_INDEPENDENT_REVIEW. Runtime: INCOMPLETE.

## Current Observed Blocker

At 2026-10-23 23:02 EDT (2026-10-24T03:02:49Z), six bounded native read calls
captured the container list, restricted metadata and known network identity twice.
Inventory (23 containers) and network observations were stable. All seven original
research IDs/images matched and were running. No environment fields, token,
volume contents, endpoint request or container execution/lifecycle action.

The accepted configured-binding predicate, replayed on these captured fields,
returned false: configured_eligibility / unselected / no exception. Four
unselected containers on the reviewed network have blank reported network IDs,
created/never-started state, zero restarts, disabled restart and no reserved
recipient alias. The old guard refuses these solely because they are not one of
the selected application names. Current false positive SHOWN; historical V6c
cause remains UNVERIFIED because its activated rows were not retained.

Saved observation:
docs/review_artifacts/companion_worker_preparation_20261023/recipient_observation_20261024T030249903885Z.json
SHA256 7ac74271a4d81c020be17920f33b74206d3547e0e247c9d547a7e420d77c2d92.
It stores selected IDs and value-free witnesses, not raw unselected metadata.
The report is parent-capture evidence, not independent native observation or
proof of a complete compatibility gate. Timing fields are capture-time UTC.

## Chosen Correction

Permit an unselected configured-only row on the reviewed network only when it
is created, never started, has integer zero restarts and disabled restart policy,
claims no reserved recipient alias, and passes the existing network projection
(including empty endpoint/address requirements). Keep its row in full-inventory
ownership checks. Do not start, detach, delete or rename unrelated containers.

Selected storage still needs a reported network ID. Selected application
eligibility is unchanged. Unselected alias collisions, wrong reported network
IDs, nonempty endpoint/addresses, started state or restart drift still refuse.
Post-start attachment checks remain unchanged. The deliberate behavior change
is limited to rejecting fewer dormant nonrecipients; this is not a no-behavior-
change diagnostic patch and requires independent review.

Implementation: one guard condition/comment in companion_runtime_adapter.py;
eleven new tests appended to test_companion_recipient_diagnostics.py. Installer
and accepted diagnostic format are unchanged. Existing tests are not reworded
to accept a failure. No old packet, receipt, ID or approval is rebound/reset.

## Verification

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_recipient_diagnostics.py tests/test_companion_active_network_contract.py tests/test_companion_staged_composition.py tests/test_companion_running_update.py tests/test_companion_runtime_adapter.py -k 'not test_pinned_bash_mode_ignores_inherited_startup_file'
```

211 passed, 1 deselected in 2.08s. Deselected test is unrelated native Bash.
Tests forbid native process/socket use; no full-suite or service proof inferred.
git diff --check passed for changed source/test.

Prior accepted source/test:

```text
adapter 4d32ab77c9183381f342f4202a9bd6bf1084de636e9d23b6ec30e7739a4fd248
test e255c9555ce4066fb4721d3621c3688505374dece6b9645cdc52cf60b0791a2a
```

Current source/test:

```text
adapter 4ecdb04d1109e6b70c2f0d439f8235e4344bc5c9b9a75206cfe685a30c60bbe3
test e0ac5f052f2e0bfc5f35e4e71ecfc62fb5daba6744ba50d75ca699bd1d95da84
```

## Next Proof

Separate review of the exact policy delta and offline tests. After acceptance,
one further read-only snapshot replay can check whether current binding refusal
is gone without changing services. It cannot authorize a new cutover or establish
the explanation data path. Runtime remains INCOMPLETE; V6c remains consumed.
