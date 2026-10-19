# Rev32 bounded review

Active role: AUDITOR. State: INCOMPLETE (runner wiring).
Target: frozen wiring 531260ff1d413e78c203ca8833bae53880afca1b,
store extension 3ec6642a689d0387137d38056b153cbd8b570bf0.

## Finding

P1, SHOWN: explicit malformed exit events are silently skipped.
In patched strategy_runner.py, lines 501-503 of
_reconcile_exit_events_from_queue skip a non-dict event or one without a
matching scope. The cursor subsequently advances past the row. Unlike invalid
JSON metadata or malformed PnL inside a correctly scoped dict, these events
are not quarantined. Later reconciliation skips the anchor and never revisits
the evidence. The journal reports no unresolved event, so this accounting
entry gate provides no protection for the missing outcome or owed kill.

Independent real-SQLite probe: a filled strategy sell belonging to the current
venue/symbol/strategy carries exit_event=null, [], or a loss dict missing scope.
After two reconciliation calls, all three cases have cursor=1|written-loss
and has_unresolved=False. All three assertions requiring unresolved evidence
fail. This is a helper-level reproduction, not proof of an actual submitted buy.

Required correction: distinguish absent legacy event metadata from an explicit
but malformed event. Use queue identity to determine ownership, preserve raw
evidence, and block entries until resolved without blocking protective exits.
Do not silently reassign a genuinely different strategy's event.

## Verification

VERIFIED_ENV: isolated base archive in /tmp/cryptkeep-rev32.NyLA3f;
local Python 3.12.10, real temporary SQLite files. Applied ordered patches
0001-0010, 0012-0018, 0020-0021, then 0022 after storage tests.
0011 and 0019 were excluded. No patch applied to the working checkout.

SHOWN: ZIP SHA256
6256a5926ebcf9a39dcb66bd0d6cb20be504047aee39f6ccfbbb64d383bf8366
matches the handoff; all manifest SHA256 entries verify.

Commands use /Users/baitus/Downloads/crypto-bot-pro/.venv/bin/python
with -B -m pytest -q -p no:cacheprovider in the isolated tree:

- tests/test_exit_event_journal.py tests/test_exit_event_journal_contract.py:
  65 passed in 6.83s on 0021.
- tests/test_runner_exit_accounting_event.py tests/test_review_exit_write_failure.py
  tests/test_review_exit_event_loss.py tests/test_review_restart_degraded.py:
  53 passed in 6.02s on 0022.
- tests/test_review_rev32_malformed_event.py: 3 failed in 0.21s on 0022.
  Probe: docs/review_artifacts/20261004_rev32/malformed_event_probe.patch.

0021: no blocking defect found in this bounded storage review; ACCEPTED_WITH_RISK
as a storage component only. Risks: quarantine has no recovery procedure,
legacy settle permits unrestricted keys, WAL NORMAL is not a power-loss
guarantee. This does not approve runner integration or deployment.

0022 and the series: INCOMPLETE. Stop at the demonstrated blocker; no repair
implemented. The four late fixes are not exhaustively validated.
Cloud full-suite/matrix totals remain CLAIMED. No full suite, large matrix, CI,
Hetzner, live integration, or reconstructed Git tree-hash verification was run.
No config, account, source implementation, deployment, push or merge changed.
