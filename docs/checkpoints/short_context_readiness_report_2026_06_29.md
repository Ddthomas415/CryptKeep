# Short Context Readiness Report - 2026-06-29

## Scope

Active role: ENGINEER

Objective:
- Add a read-only readiness check that tells whether stored crypto-edge evidence
  is sufficient for short/context replay to use `live_public` rows.
- Do not contact exchanges, start collectors, enable replay, enable paper short
  simulation, change strategy routing, or modify execution behavior.

## Reason

The accepted short/context audit identified Binance derivatives public-data
collection as blocked by `NetworkError`. The repo already has storage for
funding, open-interest, basis, quote, and order-book rows, but operators lacked
a compact fail-closed command that classifies whether the stored evidence is
usable for live-public short/context replay.

SHOWN:
- `storage/crypto_edge_store_sqlite.py` stores crypto-edge rows with a `source`
  label such as `sample_bundle` or `live_public`.
- `latest_report_for_source()` can isolate stored rows by source.
- Short/context replay remains blocked unless required context row families are
  present with accepted provenance.

## Code Change

Changed:
- `services/analytics/short_context_readiness.py`
- `scripts/check_short_context_readiness.py`
- `tests/test_short_context_readiness.py`
- `tests/test_check_short_context_readiness_script.py`
- `Makefile`
- `scripts/SCRIPTS.md`

Behavior:
- Reads the crypto-edge SQLite store in SQLite read-only mode.
- Does not create a missing store.
- Checks required row families by source:
  - `funding`
  - `open_interest`
  - `basis`
  - `order_book`
- Classifies readiness as:
  - `live_public_ready`
  - `live_public_partial`
  - `fixture_ready`
  - `fixture_partial`
  - `blocked`
  - `missing_store`
  - `store_unreadable`
- Returns `live_public_replay_ready=false` unless all required row families are
  available for `source=live_public`.

Operator command:

```bash
make check-short-context-readiness
```

The command exits non-zero unless `live_public_replay_ready=true`.

## Verification

Targeted tests:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_short_context_readiness.py \
  tests/test_check_short_context_readiness_script.py
```

SHOWN:
- `6 passed in 0.18s`

Compile check:

```bash
./.venv/bin/python -m py_compile \
  services/analytics/short_context_readiness.py \
  scripts/check_short_context_readiness.py \
  tests/test_short_context_readiness.py \
  tests/test_check_short_context_readiness_script.py
```

SHOWN:
- passed

## Interpretation

SHOWN:
- The repo now has a fail-closed read-only check for short/context data
  readiness.
- Deterministic fixture data can be distinguished from live-public evidence.
- Partial live-public evidence no longer requires manual SQLite inspection to
  identify missing row families.

UNVERIFIED:
- Whether Binance derivatives public data is reachable from the operator's
  current environment.
- Whether any derivatives venue is legally or operationally available.
- Whether any short-side strategy is profitable.

Recommendation:
- Use the readiness report before any short/context replay prototype.
- Keep replay fixture-only unless `live_public_replay_ready=true`.
- Keep paper short simulation, margin, leverage, and execution blocked until
  separate high-risk reviews are accepted.

## Acceptance State

Risk: HIGH

Reason:
- This is research-governance logic for short/derivatives context data and can
  affect whether future replay work relies on live-public evidence.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW
