# Rev40/41 bounded review

2026-10-04. AUDITOR. 0029 and 0030: ACCEPTED_WITH_RISK for their scoped
corrections only. Overall series/deployment readiness remains INCOMPLETE.

## Findings and disposition

No new blocking defect found within this bounded review. Both original rev39
probes pass unchanged: ambiguous ownership continues to refuse entries on
later turns, and damaged-scope global blockers survive inspection filtering
with nonzero exit status. 0030 adds refusal logging and recovery documentation;
it does not authorize any state repair.

Important residual risk: position_owner_conflict deliberately keeps the recorded
venue, even when the only stored stop state belongs elsewhere. Passing these
tests does NOT establish correct protective exits for that position or safe
multi-venue operation. Ambiguity is exposed, not resolved. Logging a problem
is not remediation. Position identity and any repair/closure action remain
separate operator decisions; no approval to clear history is implied.

## SHOWN verification

- Existing patch bytes unchanged from rev39 through rev41. Rev40 adds 0029
  and the received probe copy; rev41 adds 0030.
- Applied 0029 and 0030 to the isolated reviewed rev39 tree at
  /tmp/cryptkeep-rev32.NyLA3f. No patches applied to the working checkout.
- VERIFIED_ENV: local Python 3.12.10; temporary databases/test doubles.
- Command: /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -B -m pytest
  -q -p no:cacheprovider tests/test_inspect_exit_events_script.py
  tests/test_runner_venue_switch_kill.py tests/test_review_rev39.py
  tests/test_review_rev35_history.py tests/test_review_rev34_venue.py
  tests/test_review_rev32_malformed_event.py
- Result: 61 passed in 3.07s, including nine earlier reviewer probe cases.

No full suite, matrix, CI, host inspection or full Git tree reproduction in this
pass. Cloud figures remain CLAIMED. No deployment, push, merge, config/account
mutation, campaign start/stop, or automatic quarantine release.

## Economic handoff corrections

The September 26 work-log entry records an authenticated Coinbase SPOT fee
observation: maker 25 and taker 50 bps per side. This is historical evidence,
not a fresh account check or proof of historical rates on every archive date.
FC-01 has been corrected to preserve that distinction and the 100-bps nominal
round-trip fee hurdle. Ten-bps incremental improvement is not sufficient to
establish absolute positive net returns.

The supplied E03 chronology withdraws allocating the entire shared-host bill
to SMA200. Preserve that correction. A shared host does not prove exactly zero
marginal cost, nor do stale zero-fill snapshots prove the current host is idle.
Current host state and actual billing remain UNVERIFIED here. Do not stop,
extend or migrate any collector based on these notes.

The EMA three-to-six-year estimate is conditional extrapolation from a single
filtered trade, a different venue/pair and assumed timing/filters. It is not
validated strategy economics. Low observation coverage is a measurement-design
issue; a separately labelled coverage experiment can be proposed without
rewriting the original campaign or treating the strategy as disproven.

Next economic step remains FC-01 eligibility counting without outcome analysis,
not a new collector or a declaration of profitability. E03 remains undecided.
