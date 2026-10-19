# Rev37-39 bounded review

2026-10-04. AUDITOR. 0027, 0028 and series: INCOMPLETE.

## Findings

1. P1, SHOWN: ambiguous position ownership becomes trusted on the next turn.
   In the patched runner, _position_hold (lines 661-675) chooses the first
   plausible owner with an ambiguity block. _venue_and_entry_permission then
   stores it as active_venue. On the next turn the recorded-owner shortcut
   returns open_position with no block, without resolving conflicting evidence.
   Real SQLite state with entry_price under coinbase and kraken, and a position
   double holding qty=1: first call returns position_owner_ambiguous; second
   returns ('coinbase', ''). This is a helper-level proof, not an actual trade.
   Keep inferred/ambiguous ownership distinct from confirmed position identity.
   Merely choosing a venue for a turn must not resolve ownership. Do not change
   exit routing or erase stop history without an explicit supported policy.

2. P2, SHOWN: filtered inspection can return success despite a global blocker.
   scripts/inspect_exit_events.py main uses only the filtered unresolved count
   for exit status. A pending row with non-UTF8 scope blocks every scope, but
   --scope ETH/USD filters it away, reports 'unresolved: none' and returns 0.
   A warning line does mention the global block. Real SQLite probe reproduces
   this contradiction. Global blockers must survive filtering in the exit
   status and summary; retain filtered detail without declaring the scope clear.

## Evidence

- SHOWN: rev39 ZIP SHA256 is
  a250b7278368d8340b607b27c34ccad7da25a941844d4a59a10af102ab86f5b2.
- Existing patch bytes unchanged: rev37 adds 0027, rev38 adds 0028, rev39
  changes no patch. No claim that all bundled documents were re-reviewed.
- VERIFIED_ENV: isolated /tmp/cryptkeep-rev32.NyLA3f, local Python 3.12.10;
  patches 0027/0028 applied to reviewed rev36 tree, not the user's checkout.
- Command prefix: /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python
  -B -m pytest -q -p no:cacheprovider.
- tests/test_inspect_exit_events_script.py tests/test_runner_venue_switch_kill.py
  tests/test_review_rev35_history.py tests/test_review_rev34_venue.py
  tests/test_review_rev32_malformed_event.py: 52 passed in 2.56s.
- Independent tests/test_review_rev39.py: 2 failed in 0.35s.
  Probe: docs/review_artifacts/20261004_rev32/rev39_probe.patch.
- No source implementation repair, config/account change, merge or deployment.
  Full suite, long matrix, CI and Hetzner not rerun; cloud figures CLAIMED.

Next: correct these two bounded findings. Read-only inspection is not an
authorization to release quarantine. Economic research remains separate.
