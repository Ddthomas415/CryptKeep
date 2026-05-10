# Release, Validation, and Operator Docs Audit — Pass 1

**Date:** 2026-05-10
**Section:** 10. Release, Validation, and Operator Docs
**Status:** COMPLETE

---

## Scope

- `scripts/validate.py`
- `scripts/pre_release_sanity.py`
- `tools/repo_doctor.py`
- `docs/CURRENT_RUNTIME_TRUTH.md`
- `docs/LAUNCH_CHECKLIST.md`
- `docs/GOLDEN_PATH.md`
- `REMAINING_TASKS.md`

---

## Checklist status

- [x] Checklist commands exist and match this branch.
- [x] Repo doctor / validation / preflight docs are current.
- [x] Release and installer docs consistent with actual scripts.
- [~] Operator docs do not mix stale and canonical runtime paths — Finding 1.

---

## SHOWN findings

### Finding 1 — `CURRENT_RUNTIME_TRUTH.md` lists `market_ws` but `start_bot.py` does not start it (Medium)

`docs/CURRENT_RUNTIME_TRUTH.md:25`:
```
- `market_ws` for the supervised WS freshness writer path
```

`scripts/start_bot.py` starts: `pipeline`, `executor`, `intent_consumer`,
`ops_signal_adapter`, `ops_risk_gate`. Not `market_ws`.

Active soak confirms this — `bot_status.py` has never shown `market_ws` running.

**Impact:** An operator reading `CURRENT_RUNTIME_TRUTH.md` expects `market_ws`
to be running. Its absence in `bot_status.py` looks like an anomaly when it
is actually the expected state.

---

### Finding 2 — `validate.py --quick` accurately reflects current state (Strength)

Runs `check_repo_alignment.py` and a targeted pytest subset. Both pass clean
throughout the active soak. The command used in daily soak checks is accurate.

---

### Finding 3 — `LAUNCH_CHECKLIST.md` commands exist and work (Strength)

Section 1 commands verified:
- `python3 -m pytest tests -q` — exists, passes
- `python3 tools/repo_doctor.py --strict --json` — exists, passes

Section 4.1 ("7 days continuous operation") is underspecified but resolved
via the three operator policy decisions committed to `PAPER_SOAK_GATE.md`.

---

### Finding 4 — `CURRENT_RUNTIME_TRUTH.md` is recent and mostly accurate (Strength)

Last updated: `2026-05-07` — within the active soak window. Correctly
documents: `start_bot.py`, `stop_bot.py` flag syntax, `bot_status.py`,
runtime truth sources, `ai_alert_monitor` in managed service set, managed
symbol selection path. Only gap: `market_ws` listed but not started.

---

### Finding 5 — `REMAINING_TASKS.md` accurately describes current state (Strength)

```
The remaining critical path is external environment proof
or a human launch decision.
```

Matches current state: B5 (sandbox exception) is the only outstanding pre-live
gate requiring a human decision.

---

### Finding 6 — Docs directory has 80+ PHASE*.md historical files (Noted)

`CURRENT_RUNTIME_TRUTH.md` correctly warns these are not canonical unless
reaffirmed. No action required — the framing is present.

---

### Finding 7 — `GOLDEN_PATH.md` correctly defers to `CURRENT_RUNTIME_TRUTH.md` (Strength)

Covers paper evidence campaign lane only. Explicitly redirects to
`CURRENT_RUNTIME_TRUTH.md` for the supervised control plane. Separation
of concerns is clear.

---

### Finding 8 — `pre_release_sanity.py` runs YAML validation + alignment (Strength)

Exists, runs YAML config validation and `check_repo_alignment.py`, emits
structured JSON with `SCHEMA_VERSION=1`. Superset of `validate.py --quick`.

---

## Summary

| Surface | Finding | Severity |
|---|---|---|
| `CURRENT_RUNTIME_TRUTH.md` — market_ws listed but not started | Doc overstates service set | Medium |
| `validate.py --quick` | Accurate, passes clean | **Strength** |
| `LAUNCH_CHECKLIST.md` commands | Exist, work, accurate | **Strength** |
| `CURRENT_RUNTIME_TRUTH.md` overall | Recent (2026-05-07), mostly correct | **Strength** |
| `REMAINING_TASKS.md` | Accurately describes current state | **Strength** |
| Historical docs volume | 80+ PHASE files; canonical framing present | Noted |
| `GOLDEN_PATH.md` | Correctly defers to CURRENT_RUNTIME_TRUTH | **Strength** |
| `pre_release_sanity.py` | YAML + alignment, structured output | **Strength** |

---

## UNVERIFIED points

- Whether `market_ws` is intended to be started separately or is a future
  service not yet wired into `start_bot.py`.
- Whether any PHASE*.md historical docs contain commands that conflict with
  the current runtime if an operator followed them.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 10

**All 10 audit sections are now complete for pass 1.**
