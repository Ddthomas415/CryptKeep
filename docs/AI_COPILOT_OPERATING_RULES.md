# AI Copilot Operating Rules

## Principle

The deterministic core remains authoritative for:

- order submission
- risk enforcement
- reconciliation
- live arming and halt state
- database state transitions

The copilot layer is advisory.

## Current jobs

### Incident Analyst

Entry point:

- `services/ai_copilot/incident_analyst.py`

Purpose:

- collect runtime context
- summarize current health
- explain likely causes
- recommend operator next steps

Hard rule:

- read-only only

SQLite context access:

- incident context reads SQLite stores through read-only URI connections;
- caller-provided SQL must be a `SELECT` statement;
- non-`SELECT` SQL returns no rows and must not mutate or create a database.

### Safety Auditor

Entry points:

- `services/ai_copilot/safety_auditor.py`
- `scripts/run_ai_safety_audit.py`

Purpose:

- inspect current guard posture
- verify required safety docs and critical code surfaces exist
- report whether the current runtime is `ok`, `warn`, or `critical`

Hard rules:

- no live control changes
- no config writes
- no database mutation

### Drift Auditor

Entry points:

- `services/ai_copilot/drift_auditor.py`
- `scripts/run_ai_drift_audit.py`

Purpose:

- detect concrete repo mismatch between docs, backend support, dashboard options, and fallback/default truth surfaces

Initial checks:

- backend exchange support vs dashboard venue list
- docs exchange list vs backend exchange support
- fallback/sample dashboard truth helpers
- dashboard default watchlist assets vs configured trading symbols

Hard rules:

- read-only only
- no code or config mutation

### Simulation Runner

Entry points:

- `services/ai_copilot/sim_runner.py`
- `scripts/run_ai_simulation.py`

Purpose:

- run only approved offline paper/replay jobs
- capture their output as JSON + Markdown evidence packets
- keep the first lab-runner surface strictly read-only

Initial jobs:

- `paper_diagnostics` via `scripts/report_paper_run_diagnostics.py`
- `paper_loss_replay` via `scripts/replay_paper_losses.py`

Hard rules:

- no live commands
- no config writes
- no database mutation
- reject any job outside the fixed allowlist

### Strategy Lab

Entry points:

- `services/ai_copilot/strategy_lab.py`
- `scripts/run_ai_strategy_lab.py`

Purpose:

- summarize the latest persisted strategy evidence and paper-history posture
- surface persisted strategy-feedback summaries and conservative research-weighting metadata
- surface descriptive anchored walk-forward summaries from the persisted evidence row
- attach recent losing replay rows for the selected top strategy
- recommend next experiments without changing live, paper, or config state

Initial inputs:

- `strategy_evidence.latest.json`
- persisted paper-history summary from the evidence payload
- persisted strategy-feedback summary and feedback-weighting metadata from the evidence payload
- persisted walk-forward summary from the evidence payload
- loser replay rows from `paper_loss_replay`

Hard rules:

- read-only only
- no config writes
- no database mutation
- no live strategy promotion or parameter application
- no live sizing authority from feedback weighting

### Repo Reviewer

Entry points:

- `services/ai_copilot/pr_reviewer.py`
- `scripts/run_ai_review.py`

Purpose:

- inspect changed files
- classify risk by touched surfaces
- state whether human approval is required
- write JSON + Markdown review artifacts

Hard rules:

- no code mutation
- no live control changes
- no merge authority

## Review workflow

1. Detect changed files
2. Classify risk (`green`, `yellow`, `red`)
3. Attach verification evidence
4. Generate a report
5. Require human approval for protected paths

## Minimum evidence packet

Every copilot review should preserve:

- changed files
- risk tier
- protected paths touched
- verification commands or notes
- recommendations
- approval-required yes/no

## External Provider Data Boundary

External LLM providers may be used only when an operator explicitly enables an
AI-backed summary, for example through a `use_ai=true` option or an accepted
environment/provider setting.

Provider governance is enforced at the central provider boundary:

- `CBP_COPILOT_PROVIDER` selects the requested provider.
- Missing `CBP_COPILOT_ALLOWED_PROVIDERS` preserves the current supported
  provider set: `anthropic`, `openai`, `google`.
- Set `CBP_COPILOT_ALLOWED_PROVIDERS` to a comma-separated subset such as
  `anthropic,openai` to narrow external-provider access.
- Set `CBP_COPILOT_ALLOWED_PROVIDERS=none` to block all external-provider
  calls.
- Unknown or malformed allow-list entries fail closed before SDK import or
  API-key lookup.
- `services/ai_copilot/providers.py` is the only `services/ai_copilot` module
  allowed to import provider SDKs, read provider API-key environment variables,
  or call provider APIs directly; other copilot modules must go through
  `call_llm()`.

Allowed provider payload fields:

- high-level campaign health and status summaries
- strategy ids, strategy labels, venue names, and symbols
- non-secret gate status, blocker names, and recommendation labels
- aggregate fill counts, qualified round-trip counts, and PnL summaries
- recent error messages after redaction of secrets, tokens, URLs with
  credentials, and private key material
- file paths and commit ids that are already part of the repo/audit context

Forbidden provider payload fields:

- API keys, access tokens, signing keys, webhook secrets, or credential prompts
- raw exchange authentication headers or account secrets
- private SSH material, Tailscale auth links, or cloud-provider write tokens
- full unredacted config files
- raw SQLite dumps
- raw order/fill payloads containing account identifiers unless explicitly
  redacted and needed for an accepted incident packet
- any field whose only purpose is live order routing, live arming, or
  credential recovery

Provider-backed summaries are advisory. They must not:

- submit orders
- change config
- promote stages
- arm or resume live trading
- mark work accepted
- override deterministic gates

If a copilot job needs data outside the allowed boundary, stop and require a
separate accepted data-disclosure decision before sending it to a provider.

## Planned jobs

These should remain read-only, paper-only, or draft-only until explicitly
approved to broaden their scope.
