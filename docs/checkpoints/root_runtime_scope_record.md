# Root Runtime Scope Record

Status: FROZEN

Historical note:
- This checkpoint preserves an earlier frozen launch-scope story.
- References below to `scripts/bot_ctl.py` -> `scripts/run_bot_safe.py` describe the historical path at checkpoint time.
- Current canonical operator/runtime truth is documented in:
  - `docs/CURRENT_RUNTIME_TRUTH.md`
  - `docs/PROCESS_CONTROL.md`
  - `docs/BOT_CONTROL.md`

## Current status
- Scope frozen: yes
- Paper default: yes
- Live-ready: no
- External sandbox proof present: deferred in current environment
- Private authenticated connectivity proof present: yes, for Coinbase read-only with `sandbox=False`
- Runtime story unified: yes, on the canonical root-runtime path

## Purpose
This record freezes the currently supported launch scope for the root runtime baseline only.
It is intentionally narrow and should be updated only by explicit scope decision.

Related blocker record:
- docs/checkpoints/launch_blockers_root_runtime.md

## Frozen supported path
- In-scope tree:
  - root repo baseline only
- Historical operator path at checkpoint time:
  - `scripts/bot_ctl.py` -> `scripts/run_bot_safe.py`
- Deployment path:
  - local/manual operator execution from the root repo checkout using the repo venv
- Supported venue path:
  - Coinbase private authenticated read-only proof with `sandbox=False`
  - sandbox lifecycle proof is deferred in this environment because no supported sandbox/testnet venue is currently reachable
- Out-of-scope companion surfaces:
  - `services/execution/paper_runner`
  - `scripts/run_paper_engine.py`
  - `scripts/run_live_trader.py`
  - companion trees and broader governance/program surfaces unless explicitly pulled into scope

## In scope
- Root repo baseline
- Historical operator path at checkpoint time: `scripts/bot_ctl.py` -> `scripts/run_bot_safe.py`
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
- the historical root-runtime operator/config path at checkpoint time required explicit venue/symbol inputs in:
  - `scripts/run_bot_safe.py`
  - `scripts/bot_ctl.py`
  - `services/execution/live_executor.py`
- hidden-default cleanup may still remain outside the fully verified historical checkpoint path
- live lifecycle authority is boundary-governed on the canonical root-runtime path
- live-mode source of truth is singular on the canonical root-runtime path
- Coinbase is the only venue with confirmed private authenticated connectivity from the current environment
- Binance sandbox/testnet returned HTTP `451` from the current location on April 8, 2026
- Gate.io is not currently usable from the operator environment

## Confirmed blockers within this scope
- one reachable sandbox/testnet venue for lifecycle proof, or an explicit launch decision to accept the environment-blocked exception
- private lifecycle runtime proof remains deferred in this environment because no reachable supported sandbox/testnet venue is available

## Explicitly excluded until separately approved
- remote/public deployment hardening
- companion-surface contract packs
- broader governance/campaign completion work
- deprecated/compatibility surfaces as canonical runtime paths

## Change control
This frozen scope record should change only when a new explicit launch-scope decision is made.
