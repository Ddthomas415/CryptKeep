# CryptKeep Config Authority Decision

Status: `POLICY_DOCUMENTED`

## Purpose

Define the config authority rules that must hold before live expansion. This
document does not migrate readers or remove compatibility shims.

## Current Boundary

SHOWN:

- `execution.live_enabled` is the canonical final live-enabled flag consumed by
  the live-arming contract.
- Compatibility code still normalizes older `live.enabled` style config into
  the runtime shape in some paths.
- Strategy/campaign configuration lives under `configs/`, while local operator
  runtime config also exists under `config/`.

UNVERIFIED:

- Not every runtime config reader has been migrated to one strict schema.
- Not every legacy compatibility shim has a retirement date.
- Capped-live startup has not been proven from one documented config bundle.

## Canonical Rules

For new code:

- read final live-enable state through `services.execution.live_arming`;
- write final live-enable state through `set_live_enabled()`;
- do not introduce new aliases for `execution.live_enabled`;
- treat `live.enabled`, `live_trading.enabled`, and risk-local enable flags as
  compatibility inputs only, not new authorities;
- fail closed when trading-critical config is unreadable or malformed.

For strategy and campaign config:

- strategy contracts belong in `configs/strategies/`;
- campaign manifests belong in `configs/paper_evidence_campaigns*.json`;
- paper/shadow/live stage transitions require explicit decision records and
  promotion-gate evidence, not silent config edits.

For local operator config:

- `config/user.yaml` may store operator/runtime preferences;
- `config/trading.yaml` remains legacy/live-startup compatibility until the
  migration is complete;
- any new live-risk limit should have one canonical key and one documented
  reader.

## Compatibility Policy

Compatibility shims may remain during paper and shadow, but they must be:

- read-only or write-through to the canonical field;
- covered by tests that show canonical precedence;
- visible in the work log when touched;
- retired or explicitly accepted before capped live.

## Capped-Live Proof Required

Before capped-live approval, record:

- a config-reader inventory for live, risk, dashboard, preflight, and executor
  paths;
- proof that `execution.live_enabled` is the only final live-enable authority;
- corrupt-config fail-closed tests for trading-critical readers;
- one startup from the documented config bundle;
- a list of any remaining compatibility shims with accepted rationale and
  retirement conditions.

