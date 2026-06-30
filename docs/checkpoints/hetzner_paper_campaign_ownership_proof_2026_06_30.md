# Hetzner Paper Campaign Ownership Proof - 2026-06-30

## Scope

Active role: ENGINEER

Objective:
- Add a local read-only manifest ownership proof for laptop and Hetzner paper
  campaign configs.
- Do not SSH to the host, stop collectors, start collectors, restore campaigns,
  copy state, or migrate canonical `.cbp_state`.

## Reason

The accepted Hetzner paper-host plan requires one owner per campaign before any
state transfer or server restore. The repo had separate laptop and Hetzner
manifests, but no compact local proof that they do not both claim the same
campaign, session strategy, or state directory.

SHOWN:
- `configs/paper_evidence_campaigns.laptop.json` owns:
  - `es_daily_trend_v1`
  - `breakout_default`
- `configs/paper_evidence_campaigns.hetzner.example.json` owns:
  - `ema_cross_default`
- The Hetzner manifest disables desktop notifications for its headless
  campaign.

## Code Change

Changed:
- `services/analytics/paper_campaign_ownership.py`
- `scripts/check_paper_campaign_ownership.py`
- `tests/test_paper_campaign_ownership.py`
- `tests/test_check_paper_campaign_ownership_script.py`
- `Makefile`
- `scripts/SCRIPTS.md`

Operator command:

```bash
make check-paper-campaign-ownership
```

The report checks:
- duplicate campaign names across the combined manifests
- duplicate `session_strategy_id` values across the combined manifests
- duplicate `state_dir` values across the combined manifests
- expected owner assignment:
  - `es_daily_trend_v1` -> laptop
  - `breakout_default` -> laptop
  - `ema_cross_default` -> Hetzner
- Hetzner campaigns are headless (`desktop_notify=false`)

The report includes:
- `read_only=true`
- `restore_invoked=false`
- `ssh_invoked=false`

## Verification

Targeted tests:

```bash
./.venv/bin/python -m pytest -q \
  tests/test_paper_campaign_ownership.py \
  tests/test_check_paper_campaign_ownership_script.py
```

SHOWN:
- `5 passed in 0.15s`

Compile check:

```bash
./.venv/bin/python -m py_compile \
  services/analytics/paper_campaign_ownership.py \
  scripts/check_paper_campaign_ownership.py \
  tests/test_paper_campaign_ownership.py \
  tests/test_check_paper_campaign_ownership_script.py
```

SHOWN:
- passed

## Interpretation

SHOWN:
- The current laptop and Hetzner manifests are single-owner at the manifest
  level.
- The accepted Hetzner challenger remains separate from laptop-owned campaigns.
- No restore/start/stop/SSH path is invoked by this proof.

UNVERIFIED:
- Whether any matching collector process is running on either host.
- Whether Hetzner has completed a healthy server-hosted UTC cycle.
- Whether backup restore rehearsal works.
- Whether canonical `.cbp_state` can be safely migrated.

Recommendation:
- Use this as manifest-level ownership proof before any Hetzner state transfer.
- Still perform runtime duplicate-process checks before stop-copy-verify-start.
- Do not migrate canonical `.cbp_state` until backup restore proof and the full
  reviewed procedure are accepted.

## Acceptance State

Risk: HIGH

Reason:
- Campaign ownership affects persistent financial-evidence background jobs and
  state migration safety.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW
