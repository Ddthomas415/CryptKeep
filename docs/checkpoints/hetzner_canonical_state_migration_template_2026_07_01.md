# Hetzner Canonical State Migration Template - 2026-07-01

## Scope

Active role: ENGINEER

Objective:
- Add a docs-only canonical `.cbp_state` migration packet template.
- Force a reviewed Hetzner canonical campaign manifest decision before any
  stop-copy-verify-start operation.
- Preserve the safety boundary: no SSH, no restore, no start/stop, no state
  copy, no campaign mutation, and no canonical migration in this change.

## Reason

The accepted isolated `ema_cross_default` Hetzner proof does not authorize
canonical `.cbp_state` migration. The runbook listed Stage 3 requirements, but
there was no dated packet template for the future high-risk operation.

SHOWN:
- `configs/paper_evidence_campaigns.hetzner.example.json` currently owns only
  `ema_cross_default`.
- `configs/paper_evidence_campaigns.laptop.json` currently owns canonical
  `es_daily_trend_v1` at `.cbp_state`.
- `docs/HETZNER_PAPER_HOST.md` requires a separate canonical migration review.

## Change

Added:
- `docs/deployment_records/hetzner_canonical_state_migration_TEMPLATE.md`

Updated:
- `docs/HETZNER_PAPER_HOST.md`
- `REMAINING_TASKS.md`
- `docs/work_log/review_stabilized_work_log.md`

The template requires:
- reviewed Hetzner canonical campaign manifest;
- baseline laptop/gate evidence;
- fresh runtime ownership payloads;
- laptop canonical stop proof;
- canonical state manifest creation;
- canonical state backup proof;
- scoped transfer proof;
- Hetzner preflight with `--require-state`;
- manifest verification;
- isolated restore rehearsal before start;
- Hetzner start proof;
- post-migration gate comparison;
- rollback plan.

## Verification

Template/reference grep:

```bash
rg -n 'hetzner_canonical_state_migration_TEMPLATE|reviewed Hetzner canonical campaign manifest|Reviewed Hetzner Canonical Manifest|READY_FOR_INDEPENDENT_REVIEW|stop-copy-verify-start' docs/deployment_records/hetzner_canonical_state_migration_TEMPLATE.md docs/HETZNER_PAPER_HOST.md REMAINING_TASKS.md docs/checkpoints/hetzner_canonical_state_migration_template_2026_07_01.md docs/work_log/review_stabilized_work_log.md
```

Result:
- passed; references were found in the template, runbook, backlog, checkpoint,
  and work log.

Manifest ownership grep:

```bash
rg -n 'es_daily_trend_v1|\.cbp_state|ema_cross_default' configs/paper_evidence_campaigns.hetzner.example.json configs/paper_evidence_campaigns.laptop.json
```

Result:
- passed; Hetzner example owns only `ema_cross_default`, while the laptop
  manifest owns canonical `es_daily_trend_v1` at `.cbp_state`.

Whitespace check:

```bash
git diff --check
```

Result:
- passed.

## Interpretation

SHOWN:
- This is documentation-only.
- The template does not provide or run transfer, restore, start, stop, SSH, or
  scheduler commands.
- The template explicitly ends at `READY_FOR_INDEPENDENT_REVIEW` until the
  future evidence packet is complete and separately accepted.

UNVERIFIED:
- Current Hetzner host runtime state.
- Future reviewed Hetzner canonical campaign manifest.
- Future canonical migration readiness.

## Acceptance State

Risk: HIGH

Reason:
- The template controls a future high-risk migration of persistent financial
  evidence state.

Acceptance state: READY_FOR_INDEPENDENT_REVIEW
