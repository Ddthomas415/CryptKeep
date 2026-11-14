# Local verification receipt

Bot relation: BOT_RULES; actual runtime configuration/processes not checked.
Author-observed 2026-11-14 UTC, current final test body hash in SOURCE_SHA256SUMS.
No production source changed. This is not independent proof of the author.

Command:
`./.venv/bin/python -B -m pytest -q -p no:cacheprovider docs/review_artifacts/paper_profile_candidate_20261114/test_profiles.py --tb=short`

Result: **18 passed, 1 xfailed in 1.26s** (exit0).
Strict expected failure:
`test_fresh_account_is_immediately_readable_by_cash_sizing`.
Do not describe this selection as a green fresh-account readiness gate.

Same regression exposed as an ordinary failure:
`./.venv/bin/python -B -m pytest -q -p no:cacheprovider docs/review_artifacts/paper_profile_candidate_20261114/test_profiles.py::test_fresh_account_is_immediately_readable_by_cash_sizing --runxfail --tb=short`

Observed output excerpt (exit1):
```text
test_profiles.py:180: in test_fresh_account_is_immediately_readable_by_cash_sizing
    assert sized["ok"], sized
E   AssertionError: {'ok': False, 'reason': 'KeyError'}
E   assert False
1 failed in 0.47s
```

The raw regression does not manually seed ledger currency. The nine passing
profile/accounting cases explicitly do; see README and test comments. No production
state was seeded and no actual configuration/cache or service was touched.

Initial test iteration10failed8passed included9instances of this KeyError plus
one invalid synthetic release label. Subsequent iteration9failed9passed1xfail
was the fixture's clock predating cache write timestamps; next9failed9passed1xfail
was the fixture deliberately denying the evidence logger's git subprocess.
Corrected only synthetic release label/read clock/version stamp; no source guard
was relaxed. The fresh-currency failure remains visible, source uncorrected.

`git diff --check` passed. No full-suite, native-host, service, market-data,
strategy-return, actual execution or profitability verification was run.

What do I know that could change the owner's decision that I have not yet said?
The unresolved failure is an actual initializer-reader contract gap, not a failed
trading signal. Making the profile fixtures pass does not repair new accounts.
