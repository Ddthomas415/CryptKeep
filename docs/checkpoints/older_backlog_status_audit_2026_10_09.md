# Older backlog items - current status audit (read-only), 2026-10-09

Claude (cloud session). Source: REMAINING_TASKS.md (current working copy) + work log. No commands that touch
hosts, collectors or campaigns were run; the laptop checkout has no live Hetzner stores, so data-readiness checks
were NOT executed here (they would not reflect the host).

| Item | What the record shows | Is it unfinished coding work? |
|---|---|---|
| Funding/basis research | 2026-09-01 refresh: funding-threshold research ok=true, NO actionable funding candidates. OKX chosen as read-only derivatives context source (2026-07-05). Crypto-edge numeric ingestion slice (2026-07-14) recorded "ready for independent review"; no acceptance entry found by CLOUD. | No new coding. Open: (a) review/acceptance of the 07-14 ingestion slice; (b) data readiness - `make check-short-context-readiness` must report live_public_replay_ready=true ON THE HOST. |
| Shadow execution-cost measurement | Shadow would-be-fill recorder is on master (_executor_submit.py), tests show zero live side effects. | No coding. Open: operational shadow session producing real shadow_would_be_fill records, then manual slippage/cost review. Needs operator approval to run shadow stage. |
| Operational recovery evidence | Launch evidence packet still listed: restart/recovery, kill-switch, reconciliation halt/resume, rollback, lifecycle or exception evidence. Prior recovery fixes (07-18, 09-04 recovery_attempt_override) recorded. | Mostly operational drills, not coding. Needs operator-scheduled drills on the host. |
| Private lifecycle sandbox proof | Open: place/fill/cancel/reconcile on a supported sandbox/testnet, or explicit human exception. | Operational; needs sandbox credentials. |
Conclusion: none of these is blocked on new code from this session; each needs a review acceptance or an
operator-approved operational run.
