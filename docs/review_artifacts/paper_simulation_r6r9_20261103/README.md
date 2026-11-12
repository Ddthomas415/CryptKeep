# R6/R9 offline source evidence

Bot relation: BOT_RULES; runtime configuration not checked.

Active role: ENGINEER. Source handoff: READY_FOR_INDEPENDENT_REVIEW (self-checked).
R6/R9 operational acceptance: INCOMPLETE.
Separate final source GATE: **ACCEPTED_WITH_RISK** after the bounded O-47 correction. Initial source GATE:
REJECTED for O-47 (preserved). The original 643-pass
receipt is not a current-source acceptance or proof that the fingerprint was sufficient.
Question: can the current default-trio runner explain and exactly replay its decisions without changing them?
This is engineering item 2, stage 2 in `docs/PROJECT_STATE.md`, not a market experiment or a new trading rule.

## Scope and implementation

- Extend `services/strategies/signal_input_capture.py` and its existing CAS, retaining ES-v1 behavior/API.
- Add opt-in `CBP_CAPTURE_RUNNER_DECISIONS=1` instrumentation to the real runner; it is not enabled here.
- Share pure transition/exit selection in `services/execution/runner_decision.py` with offline replay.
- Record pre-filter default-trio signals, exact numeric inputs/indicators, all exit predicates, chosen rule,
  intended action, gate disposition and actual queue-write receipt. A failed/uncertain write is not called absent.
- Whitelist settings and diagnostics; never record raw configuration extras or exception text.
- Completed bars, completed-window references, settings and loaded-code identities use shared content hashes;
  per-turn forming rows/outcomes use append-only session journals. Partial tails are refused, not rewritten.
- Replay uses the real registry/helpers. Diagnostic receipt integrity is not recomputed decision proof.

## Evidence lanes

- SHOWN: seven pre-change source snapshots and `baseline_hashes.json` preserve the preceding R1/R12/multi-symbol
  work. They are not pristine master; this checkout already had changes from earlier accepted work.
- SHOWN development check: 92 existing runner/multi-symbol tests passed after the extraction.
- SHOWN development check: 72 ES-capture/registry/EMA/helper tests passed. The helper test extracts the actual
  old exit block from the hash-checked snapshot and compares 1,152 fixed-input combinations. A progress message
  incorrectly said 4,608; corrected immediately to 1,152. These comparisons have no market or profit result.
- SHOWN consolidated source verification: **643 passed, 30 files, 53.09 seconds**, no failures/skips/errors.
  `focused.command.json`, `focused.log`, `focused.xml` preserve the exact invocation, isolated environment and
  result; `submitted_hashes.json` binds the initial eleven source/test files. `stage.diff` is against that saved stage
  baseline, excluding unrelated pre-existing work. Independent review rejected that candidate: see
  `independent_review/original_review.md` and the probes. These initial passing tests did not detect O-47.
- Six real-runner synthetic clock-hour integrations replayed **366/366** decisions. Each saved
  `synthetic_hour_<strategy>_<source>.json` records counts, bytes and its limits. This is not an observed market hour.
- `offline_cli_demo/` preserves a three-record synthetic archive plus CAS; `offline_cli.command.json` and
  `offline_cli.log` show a fresh-process offline CLI run with three matches, zero mismatches/errors. This fixture
  demonstration is separate from the real-runner tests and does not establish an actual campaign's behavior.
- `capacity_model.json` preserves the arithmetic and six input-summary hashes: scaling measured public-candle
  journal bytes per synthetic record to nominal 26-week, 15-second service gives **56.54-57.84 GiB for nine
  accounts**, **113.07-115.69 GiB for eighteen**, journals only. This excludes CAS/backup/ledger/log/FS growth;
  blocked turns can run faster. It is a conditional sizing scenario, not a forecast or commissioning capacity pass.
- No full-suite, current runtime, server, alert delivery, deployment, campaign or financial validation is claimed.

## Bounded O-47 correction

The initial source/test files remain as `*.submitted`; the reviewer report and unchanged probes are in
`independent_review/`. The correction fingerprints ten active caller bindings, including helpers actually invoked
by `run_forever`, instead of assuming canonical imports are the executing instance. Replay compares these with
the currently loaded canonical implementation. V2 uses deterministic typed code/constant content rather than
marshal's object-sharing/interning representation; ES-v1 identity/API remains unchanged.

Seven added regressions **fail on the initial capture implementation** (process-only source override;
`correction.before.command.json`, log and XML); the corrected alias/equal-code/parity/capture-failure subset passed
16 tests. `correction.after.command.json`, log and XML show **143 passed / 1 fixture failure** on the affected four-file
slice. The remaining zero-timestamp fixture was itself replacing the now-hashed registry binding; observing calls
without replacing it, and ending that observation before replay, gives **1 passed / 34 deselected** in
`correction.zero_tick.final.xml`. The intermediate failing fixture is retained as `*.correction_run` and matches
its receipt hash. Do not describe these separate runs as one all-green 144-test command, or the earlier 643 as a
rerun of the corrected source. No production source changed after the 143-pass run.

`corrected_hashes.json` binds final source/tests and `stage.corrected.diff` records the change. Six corrected
synthetic-hour summaries retain **366/366** matches in `corrected_synthetic_hours/`; `capacity_model.corrected.json`
retains the corrected-phase size inputs: **56.74-58.05 GiB for nine accounts**, **113.47-116.09 GiB for eighteen**,
journals only under the same nominal scenario. These supersede, not erase, the earlier phase's byte estimates.
The corrected three-record archive
and fresh-process CLI result are in `offline_cli_demo_corrected/` and `offline_cli.corrected.command.json`/log.
Original archives, receipts and rejected-candidate evidence are preserved, not relabelled as corrected results.
Separate correction GATE **ACCEPTED_WITH_RISK**: all three original probes plus an active-alias probe pass;
eleven final hashes match. The reviewer independently ran the affected slice (143 passed/one fixture failure),
then the corrected isolated zero-timestamp case (one passed/34 deselected). This corroborates separate-run proof,
not an uninterrupted 144-pass run. See `independent_review/final_review.md`; original rejection/probes remain preserved.
Engineering item 2 and operational R6/R9 are not declared complete. O-46's hours-held gap remains open.

## Limits that can change acceptance

The capture is synchronous local I/O. Fixed-input parity does not establish equal live timing, acceptable disk
latency or operational capacity. The real observed-hour replay and host commissioning remain required.
Timestamp/timeframe-derived candle completeness is not independently verified provider truth. Tick-derived rows
are synthetic, not historical market candles. The runner has a distinct-bar counter, not measured hours held;
that literal field requirement is not silently declared satisfied. Loaded fingerprints supplement the commit:
the commit alone does not bind a dirty implementation. Hashes detect content changes, not authenticity or omitted
lines/files without a retained inventory and whole-file hash anchor. Gate/fill execution and financial accounting
are outside exact replay.
Unsupported strategy families remain supported by the runner but are outside this default-trio exact replay proof.
V2 shared CAS across distinct account roots requires explicit `CBP_RUNNER_DECISION_OBJECT_DIR`; unset stays local.
Use CLI `--object-directory` for shared archives. No real setting was changed. Replay requires a matching loaded
Python/implementation fingerprint; cross-installation/path compatibility is not certified by local checks.
R8 first-write accounting, R4 quote identity and the R1 skip-sleep caveat remain staged dependencies, not fixed here.

Open questions: does independent review find a parity/integrity omission; does intended-host recording meet
latency/storage limits; does an actual observed hour replay fully; and how should literal elapsed holding time be
represented without changing the existing bar-clock rule? No trading/cost thresholds or symbol support changed.

What do I know that could change the owner's decision that I have not yet said?
