# Rev33 / rev34 bounded review

AUDITOR. Overall acceptance: INCOMPLETE.

## Findings

1. P1, SHOWN: 0024 does not remember the initial venue. In patched
   services/execution/strategy_runner.py:617-622, the configured venue is used
   when active_venue is absent, and the same-venue branch returns without
   recording it. Ordinary operation can therefore leave this key absent
   indefinitely, not just on the first deployment turn. After a configuration
   change, the new venue becomes the assumed prior venue and bypasses the old
   kill. Real-SQLite probe: run venue selection for coinbase, set its remaining
   kill to 49, change config to kraken; selection returns kraken, not coinbase.
   Persist initial ownership; define safe handling for unknown/unreadable
   ownership instead of treating a configuration fallback as historical proof.

2. P1, SHOWN: queue-only exits are invisible to the venue-change check.
   strategy_runner.py:626-632 checks counters and journal only. Venue selection
   runs before old-scope queue reconciliation. A sell written before a crash or
   journal outage may exist only in the queue, exactly the recovery case 0022
   is intended to support. With old loss streak 2, a filled third losing sell
   in real queue SQLite, and no journal row yet, the helper allows kraken and
   records it as active. Subsequent reconciliation uses the new scope and can
   leave the old loss/owed kill stranded. Recover/check old-scope queue evidence
   before permitting migration; uncertainty must refuse new exposure while
   preserving protective exits.

Both probes are helper-level reproductions with real SQLite; no actual buy or
exchange fill is claimed. Probe artifact:
docs/review_artifacts/20261004_rev32/rev34_venue_probe.patch.

## Progress and evidence

- SHOWN: all pre-existing patch bytes are identical across rev32/rev33/rev34.
  Rev33 adds 0023; rev34 adds 0024. Applied both to the isolated rev32 tree;
  held 0011 and superseded 0019 remain excluded.
- SHOWN: the three prior malformed-event probes pass after the correction.
  That specific rev32 finding is resolved, not reopened.
- VERIFIED_ENV: Python 3.12.10, /tmp/cryptkeep-rev32.NyLA3f, temporary databases.
- Command prefix: /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python
  -B -m pytest -q -p no:cacheprovider.
- Test selection: tests/test_exit_event_journal.py,
  tests/test_exit_event_journal_contract.py,
  tests/test_runner_exit_accounting_event.py,
  tests/test_runner_venue_switch_kill.py,
  tests/test_review_rev32_malformed_event.py: 164 passed in 14.38s.
- Independent tests/test_review_rev34_venue.py: 2 failed in 0.25s.

0024 remains INCOMPLETE. This is not blanket acceptance of every additional
0023 storage change or the overall series. Full-suite and matrix figures in
the supplied handoff remain CLAIMED; no broad rerun, CI or Hetzner proof.
No implementation/config/account changes, push, merge or deployment.
Next: correct these two venue-transition cases before adding operator-release
machinery. Quarantine recovery and open-position ownership remain unresolved.
