# Pass 3A — AI Copilot Services Full Audit

**Date:** 2026-05-10
**Pass:** 3A — remaining 9 files in services/ai_copilot/
**Status:** COMPLETE — services/ai_copilot/ fully covered (12 of 12)

---

## SHOWN findings

### Finding 1 — policy.py formally defines copilot governance (Strength)

PROHIBITED_ACTIONS: arm_live_trading, disarm_kill_switch, submit_order,
cancel_order, write_config, merge_code, modify_database.

PROTECTED_PATH_PREFIXES: services/execution/, services/risk/, services/admin/,
services/security/, dashboard/auth_gate.py, scripts/, config/.

Formal governance enumeration for AI scope control.

---

### Finding 2 — All copilot modules enforce hard LLM safety constraints (Strength)

incident_analyst: 'Never suggest arming live trading, disarming the kill switch, or submitting orders'
oversight_watch: 'never suggest enabling live trading, disarming the kill switch'
pr_reviewer: 'Never recommend bypassing live guards'

Every LLM module has safety constraints hardcoded in system prompt.
Copilot can only recommend -- operators must execute.

---

### Finding 3 — drift_auditor uses AST parsing, no code execution (Strength)

ast.parse() + ast.literal_eval() to read Python source. No eval/exec/import.
Safe approach to reading actual configuration values from code.

---

### Finding 4 — providers hardcodes model claude-sonnet-4-20250514 (Noted)

Configurable via CBP_COPILOT_MODEL env var. Hardcoded default will break
when Anthropic deprecates this model version.

---

### Finding 5 — strategy_lab.py is the fifth set of acceptance thresholds (Medium)

```python
RESEARCH_ACCEPTANCE_MIN_PAPER_CLOSED_TRADES = 30
RESEARCH_ACCEPTANCE_MIN_REPRESENTED_WINDOWS = 3
RESEARCH_ACCEPTANCE_MAX_DRAWDOWN_PCT = 10.0
```

Fifth separate threshold definition. Not coordinated with:
1. evidence_cycle.py gates
2. strategy_feedback.py minimums
3. cognitive_budget.py thresholds
4. live_risk_gates.py limits

---

### Finding 6 — sim_runner no path validation on script name (Noted)

_script_path(name) = code_root() / 'scripts' / name without validation.
Job name comes from operator-level LLM responses, not direct user input.
Low risk but noted.

---

## Pattern confirmed: fragmented implementations

- 5 separate acceptance threshold sets
- 4 separate strategy name normalizations
- 3 separate intent tracking stores
- 2 separate kill switch default behaviors

None coordinated. Changes to one don't propagate to others.

---

## services/ai_copilot/ FULLY COVERED (12 of 12)

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 3A
**Next:** storage/ critical stores or full findings compilation
