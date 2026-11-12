**Finding**
**P2, SHOWN: loaded-code fingerprint misses active runner decision bindings.** [signal_input_capture.py:353](/Users/baitus/Downloads/crypto-bot-pro/services/strategies/signal_input_capture.py:353) fingerprints four runner functions, but omits `_position_aware_signal_action` and imported decision-helper bindings actually used by `run_forever`.

Two independent probes replaced `_position_aware_signal_action` and `signal_transition` separately. In both cases, the fingerprint remained unchanged and replay returned **`decision_match: true`**, rather than rejecting changed loaded code. An earlier fingerprint-only probe also failed.

Fingerprint the relevant active runner bindings, not only their defining modules, and add these regressions. This is an evidence-integrity defect; no operational mutation is alleged.

**Independent Evidence**
- Targeted kernel/archive/real-runner suite: **124 passed in 29.65s**.
- Additional probes: **three failed**, covering the single finding above.
- Hash-bound fresh-process CLI demo: **three decision matches, zero mismatches/errors**, exit `0`.
- **11/11 submitted hashes matched** [submitted_hashes.json](/Users/baitus/Downloads/crypto-bot-pro/docs/review_artifacts/paper_simulation_r6r9_20261103/submitted_hashes.json); whitespace check passed.
- Author's **643-pass** consolidated receipt inspected, **not independently rerun**.

The targeted run included actual before/on/off intent-and-state comparisons, failure paths, archive integrity/concurrency checks and six synthetic-hour scenarios. It does not establish observed runtime behavior.

**Capacity And Disposition**
Six summary hashes and their **366 synthetic matches** were consistent. Independently recalculated the **public-OHLCV journal-only** scenario: **56.54-57.84 GiB** for nine accounts; **113.07-115.69 GiB** for eighteen, assuming 182 days and one record every 15 seconds. These are conditional arithmetic, **not forecasts or capacity passes**. CAS, backups, other storage and potentially faster skip-sleep recording remain excluded.

**R6/R9 source GATE: REJECTED pending the fingerprint correction.** R12 acceptance is not reopened.

Literal elapsed hours held, an observed-hour replay, intended-host capacity/timing and commissioning remain **INCOMPLETE**. Replay covers signals/transitions/intended exits, not gate execution, fills or profits. No source, tests, runtime configuration or operational state was changed.

What do I know that could change the owner's decision that I have not yet said?
