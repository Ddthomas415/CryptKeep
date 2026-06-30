# Hetzner Paper Runtime Ownership Proof - 2026-06-30

## Scope

Active role: ENGINEER

Objective:
- Add a read-only checker that compares already-captured laptop and Hetzner
  paper-campaign status JSON payloads.
- Detect duplicate running campaign ownership across hosts before any
  stop-copy-verify-start operation.
- Do not SSH to Hetzner, stop collectors, start collectors, restore campaigns,
  copy state, or migrate canonical `.cbp_state`.

## Reason

Manifest ownership proves the configured split, not the live process split. The
remaining Hetzner blocker needs a runtime duplicate-process proof using current
status payloads. Before this change, the operator had to manually compare the
laptop and Hetzner status outputs.

SHOWN:
- `restore_paper_campaigns.py --status` emits per-campaign runtime status,
  including `name`, `session_strategy_id`, `state_dir`, `running`, and `pid`.
- `report_paper_campaign_status.py` formats status payloads but does not prove
  cross-host runtime uniqueness.
- Manifest ownership is accepted separately in
  `docs/checkpoints/hetzner_paper_campaign_ownership_proof_2026_06_30.md`.

## Code Change

Changed:
- `services/analytics/paper_campaign_runtime_ownership.py`
- `scripts/check_paper_campaign_runtime_ownership.py`
- `tests/test_paper_campaign_runtime_ownership.py`
- `tests/test_check_paper_campaign_runtime_ownership_script.py`
- `scripts/SCRIPTS.md`

Operator command shape:

```bash
./.venv/bin/python scripts/check_paper_campaign_runtime_ownership.py \
  --laptop-status-json /path/to/laptop-status.json \
  --hetzner-status-json /path/to/hetzner-status.json
```

The report checks running campaigns for:
- duplicate campaign `name`
- duplicate `session_strategy_id`
- duplicate normalized `.cbp_state*` state directory
- runtime owner mismatch against the accepted split:
  - `es_daily_trend_v1` -> laptop
  - `breakout_default` -> laptop
  - `ema_cross_default` -> Hetzner

The report includes:
- `read_only=true`
- `restore_invoked=false`
- `ssh_invoked=false`
- `status_payload_only=true`

## Verification

Compile check:

```bash
./.venv/bin/python -m py_compile \
  services/analytics/paper_campaign_runtime_ownership.py \
  scripts/check_paper_campaign_runtime_ownership.py \
  tests/test_paper_campaign_runtime_ownership.py \
  tests/test_check_paper_campaign_runtime_ownership_script.py
```

SHOWN:
- passed

Targeted tests:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_paper_campaign_runtime_ownership.py \
  tests/test_check_paper_campaign_runtime_ownership_script.py
```

SHOWN:
- `5 passed in 0.15s`

Root-script bootstrap slice:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_bootstrap_helper_adoption.py \
  tests/test_no_duplicate_script_bootstrap.py \
  tests/test_paper_campaign_runtime_ownership.py \
  tests/test_check_paper_campaign_runtime_ownership_script.py
```

SHOWN:
- `18 passed in 0.64s`

## Interpretation

SHOWN:
- The checker proves runtime uniqueness for the captured payloads only.
- The checker fails closed on duplicate running names, duplicate
  `session_strategy_id`, duplicate normalized state directories, missing
  expected campaigns, and wrong runtime owner.
- The checker itself does not collect status from either host.

UNVERIFIED:
- Whether the current laptop and Hetzner hosts pass this checker right now.
- Whether Hetzner has completed the next healthy server-hosted UTC cycle.
- Whether backup restore rehearsal works.
- Whether canonical `.cbp_state` can be safely migrated.

Recommendation:
- Capture fresh laptop and Hetzner status JSON immediately before state
  transfer planning.
- Run this checker over those captured payloads.
- Do not rely on this as proof after process state changes; rerun with fresh
  payloads.

## Acceptance State

Risk: HIGH

Reason:
- Runtime ownership affects persistent financial-evidence background jobs and
  state migration safety.

Acceptance state: ACCEPTED

Acceptance reference:
- Independently reviewed and accepted by human operator on 2026-06-30 before
  PR #147 merge.
