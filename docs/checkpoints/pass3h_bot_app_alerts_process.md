# Pass 3H — bot/, app/, validation/, alerts/, process/

**Pass:** 3H | **Status:** COMPLETE

## Findings

**Strength:** bot/process_manager and bot/start_manager labeled COMPATIBILITY_ONLY.
Canonical control via scripts/start_bot.py. Clear ownership documentation.

**Strength:** alerts/alert_dispatcher — 3-tier dispatch with guaranteed local
fallback using atomic_write. 'Never silently dropped' explicitly documented.

**Confirms H9:** crash_snapshot._managed_service_logs() includes market_ws but
NOT the pipeline. Third confirmation the pipeline is excluded from all
monitoring/crash collection infrastructure.

**Strength:** app/dashboard_diagnostics uses py_compile for syntax checking.
No code execution risk. Consistent with drift_auditor AST-only approach.

**Strength:** validation/paper_multi_symbol_validation clean defensive utility.
_safe_float and _norm_symbol guards. Pure, no side effects.

**Noted:** alerts/rate_limiter reads/writes state via plain file I/O without
atomic_write or file lock. Race condition risk if concurrent alert dispatches.
Low risk for single-process bot.

## Coverage

- services/bot/: 4 of 4
- services/app/: SAMPLED
- services/validation/: 1 of 1
- services/alerts/: 4 of 4
- services/process/: SAMPLED (7 files)
