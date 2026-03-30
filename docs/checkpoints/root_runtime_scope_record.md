# Root Runtime Scope Record

Status: PROVISIONAL

## Current status
- Scope frozen: not yet
- Paper default: yes
- Live-ready: no
- External sandbox proof present: no
- Runtime story unified: no

## Purpose
This record freezes the currently supported launch scope for the root runtime baseline only.
It is intentionally narrow and should be updated only by explicit scope decision.

Related blocker record:
- docs/checkpoints/launch_blockers_root_runtime.md

## In scope
- Root repo baseline
- Canonical operator path: `scripts/bot_ctl.py` -> `scripts/run_bot_safe.py`
- Canonical strategy/runtime family: `services.strategy_runner.ema_crossover_runner`
- Local/manual operator flow
- Paper-first posture with guarded live-capable surfaces present in repo

## Present but not yet treated as canonical launch scope
- `services/execution/paper_runner`
- `scripts/run_paper_engine.py`
- `scripts/run_live_trader.py`
- companion trees and broader governance/program surfaces unless explicitly pulled into scope

## Current repo truth
- `DECISIONS.md` defines the canonical repo direction
- `config/trading.yaml` still presents paper-mode / "live not implemented yet" language
- runtime-capable paths previously included hidden defaults such as `coinbase` and `BTC/USD`
- the canonical operator/config path now requires explicit venue/symbol inputs in:
  - `scripts/run_bot_safe.py`
  - `scripts/bot_ctl.py`
  - `services/execution/live_executor.py`
- hidden-default cleanup may still remain outside the fully verified canonical operator path
- live lifecycle authority is not yet fully boundary-governed on all active paths
- live-mode source of truth is not yet singular

## Confirmed blockers within this scope
- sandbox venue configuration
- private authenticated connectivity proof
- private lifecycle runtime proof
- live lifecycle authority decision
- live-mode source-of-truth consolidation
- docs/config alignment
- hidden-default fencing or removal on launch-capable paths

## Explicitly excluded until separately approved
- remote/public deployment hardening
- companion-surface contract packs
- broader governance/campaign completion work
- deprecated/compatibility surfaces as canonical runtime paths

## Exit condition
This record stops being provisional when:
1. one supported launch path is explicitly approved
2. one sandbox venue is configured
3. the root runtime blocker list is updated against that frozen path
