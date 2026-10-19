# Market-context capture v0

Date: 2026-09-24. Observe-only, default off. Not activated or deployed.
Scope: partial MCB-1 PR-A instrumentation, not a completed economic experiment.

`CBP_CAPTURE_MARKET_CONTEXT=1` opts a runner process into recording; unset or
any other value leaves capture disabled. Activation requires separate review.
Do not change campaign cadence, strategy, gate policy or order configuration
to enable this implementation. No network calls are added.

The runner hands existing bid/ask evidence to a bounded asynchronous writer.
It records BUY candidates only after queue upsert returns, and links them to
the preceding quote observation. This is not a fill or exchange acknowledgement.
SELL/protective exits are not entry candidates and are never vetoed or delayed
by a research decision. Later quote observations share venue/symbol and local
monotonic timestamps; no fixed-horizon markout calculation is implemented yet.

Output: the existing state data directory's `market_context/`, one unique JSONL
file per process and a `.status.json` sidecar. Queue capacity is 256 events;
the JSONL budget is 64 MiB per run. Admission never waits for storage. Shutdown
waits at most 250 ms for the writer. Pending events can be lost on process exit.
Worker-written status and final runner status report drops, failed writes,
pending events and errors. Sidecars are best-effort and may be stale or absent;
they are not a crash-durable journal or evidence of complete coverage.

## Evidence limits

- Quote time is runner observation time, not exchange event or receipt time.
  Those two timestamps remain null. Existing source age is recorded as supplied.
- Empty quote evidence is retained as missing, never reconstructed from candles.
- Fee policy and reporting conversion are explicitly unverified.
- Config hash identifies configuration, not the code revision or a full replay.
- HOLD observations are quotes, not rejected trade opportunities.
- Coverage is always unverified. No confidence interval, profit estimate,
  high-frequency coverage or completed MCB-1 claim follows from these files.
- Per-process bounds do not provide global retention or a disk quota.

Next step after review: an isolated observe-only capture calibration, with an
explicit duration and storage budget, before defining achievable horizons.
Actual account fee inputs and sample-size feasibility remain separate inputs.

The sidecar records processing state (`running`, `finished`, `failed`), not
thread liveness. Only the in-memory close result reports `writer_stopped`.
`finished` does not imply complete market coverage or crash durability.

Verification (2026-09-25): capture unit tests plus runner/exit integration slice,
59 passed. Normal/error sidecars, writer timeout and status-write failure tested.
Injected capture failures preserve entry/exit assertions and runner lock cleanup.
Full suite and deployed integration were not run. Ruff is absent from this venv.
Acceptance state: READY_FOR_INDEPENDENT_REVIEW.

## Read-only label report (2026-09-25)

`./.venv/bin/python scripts/research/report_market_context_markouts.py SESSION.jsonl`
prints one-session long-entry midpoint labels at 5/30/60 seconds. These are
descriptive defaults, not pre-registered primary horizons. Explicit CLI options
control horizons, observation lateness tolerance and maximum source quote age.
Only the first acceptable observation at/after a target is used. No interpolation,
cross-symbol join, synthetic fill, fee assumption or net-profit inference occurs.
Missing source age/quality or missing eligible horizon yields an unavailable
label. Inputs must be a single recorder session, never concatenated sessions.
The input hash is included. Coverage always remains unverified. Actual commission,
conversion and execution information is still required for an economic report.

Review correction: each new event carries a unique per-recorder session ID.
The evaluator rejects missing/mixed sessions and clock-order resets. Earlier
probe files without this provenance cannot be evaluated; do not retrofit IDs.
Counts distinguish admitted entries, usable entry quotes and available labels.
