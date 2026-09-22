# Corrected ES Prospective Evaluation Contract

## Proposed Signal Input Capture (2026-09-19)

### Read-Only Verification

`scripts/research/verify_es_signal_capture.py` verifies stored signal records
within an explicit timezone-aware half-open observation interval. Run on the
matching host/runtime; code fingerprints intentionally reject incompatible
Python/code. Example for the first post-activation UTC day:

```sh
./.venv/bin/python scripts/research/verify_es_signal_capture.py \
  --state-dir /srv/cryptkeep/app/.cbp_state_challengers/es_corrected_prospective_v1 \
  --since 2026-09-22T00:00:00Z --until 2026-09-23T00:00:00Z
```

Exit 0: every selected record verified; 1: malformed/missing/corrupt evidence,
code/provenance/output mismatch or invalid input; 2: no selected records yet.
It compares signal direction, regime, entry permission, SMA and ATR ratio,
plus source/venue/symbol/timeframe. Numeric tolerance is 1e-12 absolute/relative.
Malformed JSONL is not silently skipped, including in older inspected files.
It writes no report/evidence, fetches no market data, starts no process/service
and submits no order. Import-time logging infrastructure is unchanged.
Passing verifies existing records, NOT expected session count, continuous bars,
capture completeness or execution decisions. Combine with collector session
completion evidence; never interpret an empty scan as successful capture.

### Historical Implementation Proposal

The following is the original proposal status. Capture was subsequently accepted
and activated for isolated ES on September 21; see the work-log deployment proof.
The read-only verifier above is a separate, not-yet-deployed addition.

Implementation is READY_FOR_INDEPENDENT_REVIEW, disabled by default and not
deployed. `CBP_CAPTURE_ES_SIGNAL_INPUTS=1` opts an ES runner process into capture
at the registry-call boundary. This variable is not set on any host by this
change. Scope is SMA signal calculation, NOT execution/position/risk replay.

Exact supplied rows, including any still-forming candle, and the allowlisted
SMA/ATR parameters are stored under the active state's
`data/signal_inputs/<sha256>.json`. No user config or environment dump is stored.
Source/venue/symbol/timeframe and loaded-function/Python fingerprints accompany
the inputs. Fingerprints describe loaded signal code, not a git checkout that
may have changed while a process was running; they do not capture all external
dependencies or prove full execution reproducibility. Marshal fingerprints may
differ across Python versions or checkout paths; replay refuses mismatches.

Atomic no-replace publication preserves existing content, verifies duplicate
bytes and detects corruption. Identical payloads deduplicate; each signal record
retains its observation timestamp and hash. Changed partial candles produce
different hashes. Captured files are never automatically deleted; disk growth
must be assessed before enabling long-duration collection.

Evidence fields: `signal_input_capture_status` (`captured` or `failed`),
`signal_input_sha256` and `signal_input_observed_at` on success; error type only
on failure. Failed capture leaves signal/trading behavior unchanged and logs a
warning. It makes that observation non-replayable; it is NOT a new promotion
gate or automatic halt. If the evidence writer also fails, the log warning is
not a durable-delivery guarantee. Earlier evidence is not retroactively repaired.

Read-only signal replay (with the matching runtime available):

```python
from pathlib import Path
from services.strategies.signal_input_capture import replay_es_inputs
signal = replay_es_inputs(Path("/absolute/state/data/signal_inputs/HASH.json"),
                          expected_sha256="HASH")
```

Replay verifies checksum/schema/code identity and disables signal evidence
emission. It never places an order. A checksum does not authenticate an artifact
against a party able to replace both the artifact and its referencing evidence.

Before activation: independently review, preserve the original trial dates,
record the capture-start boundary, assess storage, and authorize the exact
state-scoped environment change/restart. No trial extension, warmup reset or
entry-policy change is part of this repair.

Active role: DIRECTOR. Research/operational evaluation only; no campaign launch.

## Isolated Runtime Proof

At research branch commit 55eb3279c, local venv executed six test files:
test_managed_exit_policy.py, test_strategy_runtime_runner.py,
test_managed_strategy_parameter_isolation.py, test_check_promotion_gates.py,
test_paper_strategy_evidence_service.py, test_ema_runner_risk_defaults.py.
SHOWN: 160 passed. Tests create temporary state and substitute market input.
Actual run-loop boundaries capture the signal block (SMA200, explicit trading
disable preserved) and exit-stack arguments (ES zero percentages/no time stop,
breakout defaults preserved). No real host child or venue session was launched.
This verifies isolated runtime behavior, not production deployment readiness.

## Frozen Evaluation Rules

Before launch, create a distinct research-only manifest/state directory and
record exact code, resolved config, dataset/source and cost hashes. Capture
resolved SMA200/ATR20 and four disabled runner controls from the actual child.
Use the explicitly approved launch manifest's quantity/capital; do not infer
portfolio sizing from the all-cash archive simulation or fitted sleeve weights.
Launch cannot proceed with missing or mismatched effective configuration.

Evaluation starts at the first completed UTC daily bar strictly after actual
launch. Fix the end at 30 calendar days after that start, with an operational
inspection after seven days. These are bounded inspection periods, not claims
of statistical sufficiency and not promotion thresholds. Missing bars remain
missing; do not slide the end date to get a favorable sample. No automatic
extension. A new period or parameter change requires a new labeled record.

Capture every expected daily observation, source availability, signal, intended
action, fill, exit reason, costs and effective config identity. Use only data
available at each decision timestamp; never substitute a later finalized daily
candle for the partial candle the runtime actually observed. Preserve raw input
snapshots so that this distinction can be checked later.

Operational success requires no configuration identity drift, no substituted
source/provenance, no duplicate execution accounting, and explicit reporting of
every missing scheduled observation. Any such failure marks the evaluation
invalid/incomplete; it cannot be repaired by counting older fills. This policy
does not install new automatic stop behavior into any existing campaign.

At the fixed endpoint, report completed trades, open position mark-to-market,
fees, drawdown, data gaps and strategy decisions including holds. Zero or few
trades is an inconclusive trading-efficacy result, not a failure to be hidden.
Compare cash and buy-and-hold with identical initial capital, source window and
explicit cost assumptions, separately labeled from actual paper fills. Do not
equate allocation matching with volatility/risk matching. No winner selection
or live promotion from this 30-day observation alone.

## Authorization Boundary

No trial has started and no future dataset is claimed reserved/observed yet.
The actual start/end and effective manifest must be recorded at launch. Existing
canonical campaign, cohort, positions, gate policy and historical evidence are
untouched. Before deploying accepted fixes to that campaign, inspect open
positions and separately authorize the transition and any restart.

Acceptance state: INCOMPLETE for prospective evidence (not yet collected).
Isolated implementation proof is SHOWN; production child proof is UNVERIFIED.
