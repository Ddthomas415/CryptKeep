# Rev35 / 0025 bounded review

Role: AUDITOR. Acceptance: INCOMPLETE.
Target claimed commit: 7fc03cda11769e1ee81b6b89d184c059d75f89d4.
ZIP SHA256 verified:
5d74f4bb3d8e359cf53cbf7791bae3b60d1e94ca84551b27b2c93f53f1d064a5.

## Findings

1. P1, SHOWN: multiple historical holds are reduced to one permanently.
   Patched strategy_runner.py:668-669 checks only the recorded owner after
   lines 682-684 record the first historical owner with a hold. Real SQLite:
   coinbase and kraken each have a remaining kill of 49; selection first holds
   coinbase. After its cooldown is zeroed to represent completion, selecting
   binance returns binance although kraken still has 49. Historical discovery
   must not forget other unresolved scopes merely because one was selected.

2. P1, SHOWN: a failed history scan is not an entry refusal.
   strategy_runner.py:673-677 returns the configured venue on scan failure.
   Real SQLite contains a coinbase kill; inject failure only in keys_ending,
   leaving ordinary state and queue reads healthy. With configured kraken,
   selection returns kraken normally. Thus the author's total-store-failure
   explanation does not cover partial failures: the selected venue's ordinary
   reads need not fail, and do not inspect the old venue's kill. Propagate an
   explicit unknown/block-entry result rather than representing uncertainty
   solely by a venue string. Preserve protective exit processing.

These are helper-level demonstrations, not evidence of a submitted buy or
exchange fill. Both expected-safety assertions fail; the test is available at
docs/review_artifacts/20261004_rev32/rev35_history_probe.patch.

## Verification and scope

VERIFIED_ENV: isolated /tmp/cryptkeep-rev32.NyLA3f, local Python 3.12.10.
Applied 0025 on the previously reviewed rev34 tree. The patch contains copies
of the two existing review test files, so the first apply refused duplicate
paths atomically. One test invocation therefore ran the unchanged rev34 tree
(74 passed, the two expected old probes failed); this is not a rev35 result.
Reapplied excluding only those already-present probe paths; retained the
original probes unchanged.

Command prefix:
/Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python -B -m pytest -q -p no:cacheprovider

- tests/test_runner_venue_switch_kill.py tests/test_review_rev34_venue.py
  tests/test_review_rev32_malformed_event.py tests/test_runner_exit_accounting_event.py:
  83 passed in 7.86s on rev35. Both prior venue blockers and the malformed-event
  cases pass; those specific findings are resolved.
- tests/test_review_rev35_history.py: 2 failed in 0.34s.

No production implementation changes. No full-suite/matrix rerun, CI, Hetzner,
config/account mutation, push, merge or deployment. Cloud full-suite results
remain CLAIMED. Full bundle/tree reproduction was not reverified in this pass.

Recommended next correction: separate the venue used for exit processing from
permission to open new exposure. All known unresolved historical scopes and
unreadable history must preserve entry refusal until resolved. Do not clear
history, rename counters, or change stop ownership to make these tests pass.
0025 and overall series remain INCOMPLETE.
