# Phase 258 — Mark Cache UI Locks + Warnings

Adds UI guardrails so users don't accidentally run two mark-cache instances.

Rules:
- If `mark_cache.owner == runner`:
  - Streamlit supervisor Start/Stop buttons are disabled.
- If `mark_cache.owner == supervisor`:
  - Streamlit Start/Stop are enabled and recommended.

Also:
- Mark Cache Status panel displays current owner.
