# Root Runtime Launch Blockers

Status: FROZEN_WITH_EXTERNAL_EXCEPTION

## Snapshot
- Repo truth docs updated: yes
- Scope record present: yes
- Trading config comment aligned: yes
- External sandbox proof present: blocked by venue availability from current environment
- Private authenticated connectivity proof present: yes, for Coinbase read-only with `sandbox=False`
- Live lifecycle authority fully governed: yes, on the canonical root-runtime path
- Live-mode source of truth singular: yes, on the canonical root-runtime path

## Scope
This note tracks the visible launch blockers for the root runtime baseline only.
It does not automatically include companion trees or broader governance surfaces unless explicitly pulled into scope.

Canonical scope record:
- docs/checkpoints/root_runtime_scope_record.md

Next actions board:
- docs/checkpoints/root_runtime_next_actions.md

## Frozen scope outcome
- The canonical launch scope is now frozen in:
  - `docs/checkpoints/root_runtime_scope_record.md`
- No remaining repo-side implementation blockers are shown on that frozen canonical path.

## Deferred external exception

### Sandbox lifecycle proof is deferred in this environment
Why it remains deferred:
- Coinbase authenticated read-only proof is complete, but no supported Coinbase sandbox path is available in the current repo/client combination
- Binance sandbox lifecycle proof is blocked by external HTTP `451` venue restriction from the current location
- Gate.io sandbox lifecycle proof is blocked by current operator-environment access constraints
- Direct network probes captured on April 9, 2026 strengthened that classification:
  - `curl https://testnet.binance.vision/api/v3/ping` -> HTTP `451`
  - `curl https://fx-api-testnet.gateio.ws/api/v4/futures/usdt/contracts` -> HTTP `502`
  - `traceroute testnet.binance.vision` resolved and routed beyond local/DNS layers, so the Binance failure is upstream venue restriction rather than a local DNS problem

What is already proven:
- private authenticated connectivity for one supported venue
- boundary-governed live lifecycle authority on the canonical root-runtime path
- singular live-mode source of truth on the canonical root-runtime path

What is still missing:
- redacted sandbox evidence for:
  - order placement
  - fetch/status reconciliation
  - cancel
  - post-cancel verification

Close condition:
- run the lifecycle proof in an environment with one reachable supported sandbox/testnet venue
- or make an explicit launch decision to accept the environment-blocked exception

Risk:
- Medium as a launch decision
- High if runtime code changes are needed later

Review lane:
- Human decision / external environment

## Launch-support tasks

### P3. Pipeline exit evidence capture before live
Problem:
- supervised pipeline child stdout/stderr are not persisted, so an unhandled pipeline exit can leave no durable crash log for postmortem review
- `pipeline.status.json` can remain at the last successful `running` write if the process exits before writing a failure state

Visible evidence:
- `services/runtime/process_supervisor.py` starts child processes with stdout/stderr redirected to `subprocess.DEVNULL`
- direct foreground pipeline run writes actionable output to `/tmp/pipeline_exit.log`, but supervised startup does not create an equivalent `pipeline.log`

Close condition:
- supervised `pipeline` startup captures stdout/stderr to a durable runtime log, for example `runtime/logs/pipeline.log`
- pipeline unhandled exits leave a failure status or log entry that includes the exception/reason before any live run is considered ready

### P3A. Canonical AI alert monitor and runtime log analysis
Problem:
- the repo-wide oversight watch is read-only and one-shot, not a continuous monitor
- dashboard and CLI copilot surfaces are split between different context builders
- AI incident analysis is not wired to `runtime/alerts/critical_alerts.jsonl`, current service status files, or the runtime log directory used by active services

Close condition:
- one canonical AI monitor watches `runtime/alerts/critical_alerts.jsonl`, status files, and selected runtime logs
- new alert-worthy events trigger persisted operator-facing incident reports under `runtime/ai_reports/`
- CLI and dashboard both expose the monitor status and recent incident surface

### A. Align docs/config with actual supported state
Evidence:
- config/trading.yaml now states that paper is the default and that live-capable surfaces exist, but live readiness is not yet established
- the scope record and blocker list should continue to reflect that same repo truth

Close condition:
- Operator-facing docs and active config describe the same supported state

### C. Produce launch evidence packet
Close condition:
- One packet containing:
  - restart/recovery drill
  - kill-switch drill
  - reconciliation halt/resume drill
  - rollback drill
  - supported venue lifecycle evidence, or the explicit environment-blocked exception record documented here

## Non-blocking repo discipline
- Keep compatibility layers frozen
- Align REMAINING_TASKS.md with actual remaining work

## Recent landed fix
- Canonical root-runtime launch scope is now frozen:
  - `docs/checkpoints/root_runtime_scope_record.md`
- Private authenticated connectivity for one supported venue is documented:
  - `docs/checkpoints/private_connectivity_and_readonly_lifecycle_evidence.md`
- Live-mode source of truth on the canonical root-runtime path is now singular and published:
  - `49dd99c` — `execution: persist canonical live enable contract`
- Live lifecycle authority on the canonical root-runtime path is now boundary-routed and published:
  - `ffc8686` — `execution: route open-order reconcile through boundary`
- Hidden defaults on the chosen launch path are fenced and no longer tracked as an active blocker:
  - `docs/checkpoints/hidden_defaults_note.md`
