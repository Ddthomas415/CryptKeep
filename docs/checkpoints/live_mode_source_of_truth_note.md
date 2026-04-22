# Live Mode Source-of-Truth Note

Status: LANDED

## Objective
Record the post-implementation runtime truth layer for the hardened live path, separating what the repo already enforces from optional future runtime-truth infrastructure.

## Runtime Truth Enforcement Layer
You do not want more prose docs. You want the repo to make these questions mechanically answerable:

- who may submit live orders?
- what services are allowed in live mode?
- what path actually crossed the broker boundary?
- which state-write paths are legitimate?
- what should hard-fail if topology drifts?

This runtime truth layer should be described in two parts.

## Part A — Implemented Hardening Primitives

### 1. Submit authority enforcement
Implemented now:

- live submit authority is explicit
- canonical live submit owner is `intent_consumer`
- enforcement occurs at the true money-exit boundary: `services/execution/place_order.py`
- unauthorized live submit attempts fail closed before any broker call

### 2. State-write authority enforcement
Implemented now:

- submit-side and reconcile-side state writes are guarded
- canonical allowed authorities are:
  - `INTENT_CONSUMER`
  - `RECONCILER`
- legacy and non-canonical state-write paths are blocked or demoted

This is a guarded submit-side and reconcile-side state-write authority model, not a single global state owner.

### 3. Live topology alignment
Implemented now:

- canonical live topology is:
  - `intent_consumer` as submit owner
  - `pipeline`, `ops_signal_adapter`, and `ops_risk_gate` as support-only services
  - `reconciler` as reconcile-only
- legacy executor paths are excluded from the canonical live runtime

### 4. Operator-visible runtime truth
Implemented now in patched status/reporting surfaces for the hardened live topology:

- canonical submit owner
- active services
- blocked legacy services
- state authority roles
- topology-aligned status signal

This should be read as status/reporting truth, not as a fully unified supervisor control plane unless the code proves that stronger claim.

## Part B — Optional Next-Layer Runtime Truth Subsystem
If you want to make future human and AI misinterpretation harder, add a dedicated runtime truth subsystem.

### 1. Topology registry
A canonical machine-readable spec declaring:

- allowed live nodes
- blocked live nodes
- canonical submit owner
- state authority roles
- runtime version or fingerprint

### 2. Startup verifier
Before live services start, verify:

- no disabled-in-live nodes are requested
- exactly one canonical live submit owner is active
- requested live topology matches the approved runtime truth spec

### 3. Audit ledger
Record structured events for:

- startup verified or blocked
- live submit allowed or blocked
- topology mismatch
- disabled node requested

### 4. Runtime truth report
Expose one read-only report surface showing facts like:

- mode
- canonical submit owner
- active services
- blocked legacy services
- state authorities
- topology aligned
- runtime truth fingerprint

## Design Rules

### Authority rule
- permission is based on authority
- origin is audit and observability only

### Money boundary rule
- the true live submit boundary is `services/execution/place_order.py`
- not merely adapter-level helper aliases

### State rule
- current hardening is about guarded write authority
- not full single-store canonicalization yet

### Topology rule
- status surfaces should reflect the hardened live topology
- avoid broader supervisor-control claims unless the code proves them

## Future Explicit Declaration
A declaration like this is still useful, but it is a future operator-truth enhancement, not a solved architecture statement:

```python
LIVE_STATE_TRUTH = {
    "intent_state": "LiveIntentQueueSQLite",
    "order_state": "LiveTradingSQLite",
    "execution_audit": "ExecutionStore",
    "fill_sink": "CanonicalFillSink",
}
```

What is hardened today is write authority, not full canonical-state consolidation.

## Short Version
Build the runtime truth layer around four enforced facts:

1. only `intent_consumer` may submit live orders
2. all live submission must cross `services/execution/place_order.py`
3. only currently approved submit-side and reconcile-side state-write paths may mutate guarded live state
4. patched status surfaces must expose the canonical live topology and blocked legacy paths

Then optionally add:

- topology registry
- startup verifier
- audit ledger
- runtime truth fingerprint

Those make the system self-describing, but the repo already contains the core hardening primitives.

## Landed Evidence
- `services/execution/place_order.py`
- `services/execution/execution_context.py`
- `services/supervisor/supervisor.py`
- `tests/test_hardening_smoke.py`
- `tests/test_execution_boundary_regression.py`
- `tests/test_no_direct_create_order.py`
