# Final Independent R6/R9 Correction Review

Date: 2026-11-03. Active role: GATE. Risk: HIGH.

Bot relation: BOT_RULES; runtime configuration not checked.

**Final disposition: ACCEPTED_WITH_RISK for the bounded R6/R9 source correction.**
The initial P2 fingerprint finding is SHOWN corrected. No remaining finding was
identified within this correction scope. The original rejection remains preserved
in `original_review.md`; it was not silently replaced or treated as acceptance of
the rejected candidate. R12 acceptance is unchanged. Full simulation is INCOMPLETE.

## Provenance

This file persists the reviewer's already completed review and execution evidence
at the owner's explicit request. Commands and results below are transcribed from
the existing review chat/tool outputs. No command was rerun, no implementation
file was inspected or edited, and no operational action was performed to create
this report. It is not a newly generated test receipt.

## Correction Assessed

- The real runner passes ten whitelisted active caller bindings: `run_forever`,
  `_strategy_signal`, `_registry_signal_with_context`, `_synth_ohlcv`,
  `_position_aware_signal_action`, `position_aware_signal_action`,
  `signal_transition`, `select_exit_decision`, `evaluate_strategy_exit_stack`,
  and `compute_signal`. Capture no longer assumes the canonical import is the
  active caller; replay compares with canonical current bindings.
- V2 fingerprints use deterministic typed code/constant content rather than
  marshal bytes whose interning/sharing representation can differ for equivalent
  code. Filename, Python-version and implementation binding remain. The equal-AST
  recompile and tuple/list distinction checks were included in the focused tests.
- Integration observers use profile hooks without replacing fingerprinted signal
  or evaluator bindings. The final zero-timestamp observer is bounded by
  `try/finally` around `h.run(6)` and stops before replay.
- AST comparison confirmed the correction left `_code_identity`, `_store`,
  `capture_es_inputs`, and `replay_es_inputs` unchanged (ES-v1 functions).

## Independent Commands And Results

All commands were run from `/Users/baitus/Downloads/crypto-bot-pro`. Original
randomized temporary directory names were not returned by the shell and are not
invented here. Commands retain their original `mktemp` expressions. The tests
used temporary stores and synthetic inputs, not services or private accounts.

### Four-File Focused Run

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-correction.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_runner_decision_capture.py tests/test_runner_recording_integration.py tests/test_runner_decision_kernel.py tests/test_signal_input_capture.py --tb=short
```

SHOWN independent result (original completion chunk `07a47d`, exit 1):

```text
FAILED tests/test_runner_recording_integration.py::test_zero_tick_timestamp_captures_exact_actual_synthetic_rows
1 failed, 143 passed in 81.52s (0:01:21)
```

That intermediate fixture still replaced `compute_signal`; the corrected strict
fingerprint properly detected the different binding. The production source did
not change after this run. The subsequent fixture-only profile version initially
observed replay calls too, growing its comparison list: one focused independent
run failed with `ValueError: zip() argument 2 is longer than argument 1`
(`805a5c`: 1 failed, 34 deselected in 1.51s). That intermediate failure is also
retained here rather than silently discarded.

### Final Zero-Timestamp Case

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-zero-final.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -m pytest -q -p no:cacheprovider tests/test_runner_recording_integration.py -k zero_tick_timestamp --tb=short
```

SHOWN independent final result (original chunk `94574f`, completion `000983`,
exit 0):

```text
1 passed, 34 deselected in 1.00s
```

The owner's separate final receipt reported 1.11s; that is not substituted for
the reviewer's independently observed 1.00s. These are distinct-run results,
**not one uninterrupted all-green 144-case run**. No broad matrix rerun was
required after the bounded fixture correction.

### Original Three Probes

The original exact code remains in `probe_fingerprint_only.py` and
`probe_active_bindings.py`; original rejection commands/results remain in their
adjacent `.command.sh` and `.result.json` files. The correction recheck executed
that archived code unchanged:

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-original-probe.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c 'from pathlib import Path; p=Path("docs/review_artifacts/paper_simulation_r6r9_20261103/independent_review/probe_fingerprint_only.py"); exec(compile(p.read_bytes(),"<string>","exec"))'
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-original-probes.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c 'from pathlib import Path; p=Path("docs/review_artifacts/paper_simulation_r6r9_20261103/independent_review/probe_active_bindings.py"); exec(compile(p.read_bytes(),"<string>","exec"))'
```

SHOWN independent results (chunks `0d99d5` and `2bc34c`, both exit 0):

```text
1 passed in 0.35s
2 passed in 0.38s
```

All three original probes now pass. An additional in-memory plugin probe drove
the real runner through its alias module, substituted only that alias's
`signal_transition` with an equivalent wrapper, confirmed the stored identity
bound that active wrapper rather than the canonical import, and confirmed replay
rejected it with `runner_code_mismatch`. SHOWN result (`ccf604`, exit 0):

```text
1 passed in 0.54s
```

### Rejected-Source Regression Comparison

```sh
env -i PATH=/usr/bin:/bin HOME=/private/tmp CBP_STATE_DIR="$(mktemp -d /private/tmp/r6r9-before-correction.XXXXXX)" PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 CBP_CAPTURE_MARKET_CONTEXT=0 CBP_CAPTURE_EXECUTION_IDENTITY=0 ./.venv/bin/python -B -c 'from pathlib import Path; from services.strategies import signal_input_capture as capture; p=Path("docs/review_artifacts/paper_simulation_r6r9_20261103/services__strategies__signal_input_capture.py.submitted"); exec(compile(p.read_bytes(),str(p),"exec"),capture.__dict__); import pytest; raise SystemExit(pytest.main(["-q","-p","no:cacheprovider","tests/test_runner_decision_capture.py","-k","active_runner_alias_change or explicit_active_caller","--tb=no"]))'
```

SHOWN independent result (`852bf2`, exit 1):

```text
7 failed, 50 deselected in 0.48s
```

Six active-alias mutations and the explicit-active-caller case fail against the
rejected capture implementation. This is an isolated component override in
memory, not a pristine-tree baseline or a claim of seven distinct defects.

## Final Hash-Bound Candidate

The reviewer independently recomputed all eleven SHA256 values against
`../corrected_hashes.json` after its final fixture-hash refresh. Final verification
chunk `3f0a25` reported `11/11 corrected hashes match`. The final fixture hash is
the bounded-profile version, not either intermediate failing fixture.

```text
services/execution/runner_decision.py
1b400cd9feba3f8ccb3f635f25ba76b440c08ad2d394b91eabe990559d90faee
services/execution/strategy_runner.py
2bccce94b22cbc6f52692a8c9a2373016f89b0adb8eab7697bfda3d0a4ec3c94
services/strategies/signal_input_capture.py
2664bad55b22a20390a8c98b529e94432fe92a712804e6601eac6cec09389ddc
services/strategies/strategy_registry.py
db4cc349310eac07ef82d50e6c8c779b39fa788a265fc837681325f797049692
services/strategies/ema_cross.py
68b3522c816b94d6e1b864398dbf212558492e2d8143c849f64d17926e5b8a6f
services/strategies/breakout_donchian.py
5de5765593c9addc540a4d32da77c8ac879ddb9d7b3697719d970793fa57975a
services/strategies/mean_reversion_rsi.py
63d125e3ec914c1118f523ca81337f7647faa14cfba3ad8ce0c2b5956dca37d3
scripts/replay_runner_decisions.py
806b3d0fab9d5e312a5abff3fb5598af62d3819aea56c870fc30779333e79624
tests/test_runner_decision_kernel.py
9770fa40ab5f64bba5ed57b7cf7a36c17183c1195d077903212eef3f4586f9f9
tests/test_runner_decision_capture.py
f8d2e22faa3f5a0f9bcc403e373df1b6c105f0190999eb2d1c92ec99c2b6b6cb
tests/test_runner_recording_integration.py
4064d78d99b180bdbb0852620b7d1287ee6a71a304fa8bca05f680e2c15c5ed3
```

Changed-path `git diff --check` passed during the correction review. The earlier
30-file 643-pass author receipt was inspected, not independently rerun and not
represented as post-correction verification. The corrected three-record CLI
receipt was inspected: three matches, zero mismatches/errors, exit 0. It was not
independently rerun in the correction stage.

## Corrected Capacity Evidence And Limits

The reviewer independently checked all six corrected summary hashes against
`../capacity_model.corrected.json`, their 61 records/61 matches each (366 total),
stream/CAS byte counts, and the conditional public-OHLCV journal arithmetic.
Verification chunk `c8a5d1` reported:

```text
9 accounts: 56.74-58.05 GiB
18 accounts: 113.47-116.09 GiB
6 corrected summary hashes, 366 synthetic matches and conditional arithmetic verified
```

These corrected-phase ranges supersede the earlier phase's journal-size ranges.
They assume 182 days and nominal 15-second recording. They exclude CAS growth,
backups, filesystem overhead, ledgers, logs and other data. They scale synthetic
public-OHLCV journal records, not measured multi-account host traffic; R1 blocked
turns skip sleep and can increase recording rate. **Neither forecast nor capacity
pass.** Summary/hash consistency is not an actual market-hour or host test.

## Acceptance Boundary

Inspected evidence: frozen correction source/test deltas; active caller and
canonical replay bindings; deterministic code/constant fingerprints; ES-v1
preservation; observer changes; existing independent tests/probes; final eleven
hashes; corrected CLI and capacity receipts. Production code was unchanged during
the final fixture-only corrections. No source rules or trading thresholds were
changed by this review.

Acceptance covers the corrected offline R6/R9 source dependency. Literal elapsed
hours held, observed-hour replay, intended-host timing/capacity and commissioning
remain INCOMPLETE. Replay covers signals, transitions and intended exits, not
gate execution, queue durability, fills or profits. R8 initial-write/accounting,
R4 quote identity, R1 skip-sleep timing, actual runtime configuration and operation
remain separately scoped dependencies. R12 source acceptance is not reopened.

No services, private accounts, network calls, runtime configuration changes,
deployment or trading operations were performed for this correction review.
Counterevidence about an unbound active decision dependency, false matching replay,
decision parity, archive integrity or actual host behavior could change this
bounded disposition. Accepted source proof is not permission to start the
unfinished simulation.

What do I know that could change the owner's decision that I have not yet said?
