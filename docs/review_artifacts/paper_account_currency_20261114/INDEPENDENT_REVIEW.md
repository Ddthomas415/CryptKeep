# Independent source review receipt

Bot relation: BOT_RULES; actual runtime configuration/processes not inspected.
Reviewer Nash (separate agent01a1cee8-b4ec-7343-9992-b771df07aba1), not author.
GATE2026-11-14T12:19:55Z: ACCEPTED_WITH_RISK for O163 source/synthetic repair.
No material blocker. No operating or commissioning acceptance follows.

Confirmed fresh-only currency persistence, equity-history exclusion and atomic
cash/currency/origin transaction. Legacy currency not inferred; inherited
nonfresh default-writing behavior is explicitly disclosed. Original profile
tests unchanged; historical store binding superseded only by the new source seal.

Independent command:
```sh
./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q \
  tests/test_paper_account_currency.py \
  docs/review_artifacts/paper_profile_candidate_20261114/test_profiles.py::test_fresh_account_is_immediately_readable_by_cash_sizing \
  --runxfail --tb=short
```
Result:25passed0.99s, including nine unseeded profiles, rollback, restart and
concurrent different-currency initialization. Author243passed5.24s not repeated
as one selection by reviewer. No full-suite proof claimed.

Accepted SHA256:
```text
0c7651ea0e47217b700cbbb2e1874962e2ad6241301de414a5f0c809f676c96f  storage/paper_trading_sqlite.py
3f533431ec8d540e6bc17e4fe71e691d67d7c354c18f911876aa6cbd6a87cf75  tests/test_paper_account_currency.py
```

Reviewer did not edit files, inspect actual state, send HTTP or perform operations.
Plan review12:16:52Z first identified the missing equity-only history boundary;
it was reproduced before correction and included before final source acceptance.

What do I know that could change the owner's decision that I have not yet said?
This closes the demonstrated fresh-bootstrap defect, not legacy-account
qualification or simulation commissioning.
