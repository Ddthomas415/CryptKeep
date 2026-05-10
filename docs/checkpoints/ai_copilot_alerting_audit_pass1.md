# AI Copilot and Alerting Audit — Pass 1

**Date:** 2026-05-10
**Section:** 7. AI Copilot and Alerting
**Status:** COMPLETE

---

## Scope

- `services/ai_copilot/alert_monitor.py`
- `services/ai_copilot/context_collector.py`
- `services/ai_copilot/safety_auditor.py`
- Active soak incident ledger

---

## Checklist status

- [x] Alert monitor status truth and report-pointer fidelity.
- [x] Log/alert dedupe behavior.
- [x] Context sources reflect canonical runtime/log surfaces.
- [x] Read-only boundaries in UI.
- [x] Copilot artifacts discoverable and interpretable.

---

## SHOWN findings

### Finding 1 — Log event dedup is incremental by line count (Strength)

`_new_log_events()` tracks `previous_counts[path.name]` — the line count of
each monitored log on the last check. New events are only lines after the
last known count:

```python
start = max(0, int(previous_counts.get(path.name) or 0))
new_lines = lines[start:]
```

An error that appears once generates one event. Subsequent checks skip it.

---

### Finding 2 — Service-down fires once per state transition (Strength)

```python
if previous is False:
    continue   # already known down — skip
```

A service transitioning `running → down` fires one event. Remaining down
across poll cycles generates no further events. No alert flooding.

---

### Finding 3 — `incidents_written` is cumulative, not unique-failure count (Shown)

The counter is read from the health file at startup and incremented on each
write. Never reset. The active soak has `incidents_written=9`:
- 3 pre-window reports
- 6 current-window reports (2 per failure family × 3 families)

Each family generated 2 reports: one for the traceback burst, one for the
summarized `run_once_failed` line. Raw count overstates unique failures.
Correct interpretation requires the incident ledger.

---

### Finding 4 — Monitored log names are a fixed whitelist (Shown)

```python
_LOG_NAMES = (
    "pipeline.log", "intent_consumer.log", "reconciler.log",
    "executor.log", "ops_risk_gate.log", "ops_signal_adapter.log",
)
```

Only these 6 files are scanned. `app.log` (written by the paper campaign
runner) is not in `_LOG_NAMES`. Paper campaign errors are not detected by
the alert monitor.

---

### Finding 5 — Keyword matching is substring, not pattern (Shown)

```python
_KEYWORDS = ("traceback", "exception", "error", "failed", "critical", "networkerror")
if any(keyword in line.lower() for keyword in _KEYWORDS)
```

Any line containing `"error"` as a substring matches — including benign lines
like `"no error found"`. False positives are possible. Current soak incidents
are genuine failures, but the matching is imprecise.

---

### Finding 6 — Context collector reads canonical runtime truth (Strength)

`context_collector.py` reads last 20 lines of all `runtime/logs/*.log` files,
all `runtime/flags/*.status.json` files, and calls `get_system_health()`.
Same sources as manual operator soak checks.

---

### Finding 7 — Fallback analysis when AI provider fails (Strength)

Fallback writes a templated report when the API call fails. Report is still
persisted and counted. Operators can see the fallback was used.

---

### Finding 8 — Safety report writes are not atomic (Low)

`safety_auditor.py` uses `Path.write_text()` not `atomic_write()`. Same
inconsistency as PID files. Safety reports are advisory artifacts so partial
writes are low-risk.

---

## Summary

| Surface | Finding | Severity |
|---|---|---|
| Log event dedup | Incremental by line count | **Strength** |
| Service-down dedup | Once per state transition | **Strength** |
| `incidents_written` | Cumulative, not unique-failure | Shown (known) |
| Log name whitelist | `app.log` not monitored | Shown |
| Keyword matching | Substring — false positives possible | Shown |
| Context sources | Canonical health + logs | **Strength** |
| Fallback analysis | Report written on provider failure | **Strength** |
| Safety report writes | `write_text` not `atomic_write` | Low |

---

## UNVERIFIED points

- Whether keyword false positives have produced misleading incidents.
- Whether `app.log` exclusion is intentional.

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Section 7
**Next target:** Section 8 — Evidence, Promotion, and Governance
or Section 10 — Release, Validation, and Operator Docs
