# Fresh paper-account currency repair

Bot relation: BOT_RULES; source/synthetic temporary state only. Actual runtime
configuration, processes, services and server not inspected or changed.
Owner continued the explicit offline repair recommendation. R10 STOPPED.

Status: ACCEPTED_WITH_RISK by separate Nash GATE2026-11-14T12:19:55Z,
source/synthetic repair only. Checked current Git/log2026-11-14T12:20:15Z.
This artifact preserves before/after proof of O163; no activation, legacy migration
or commissioning authorization follows.

## Result and scope

SHOWN: existing initialize_account now writes normalized quote_currency inside
the same BEGIN IMMEDIATE transaction as fresh cash and origin. Currency must be
absent and there must be no equity history before the account is certified fresh,
in addition to the existing cash/origin/order/fill/position checks. No sizing
reader fallback, inferred legacy currency or new migration was added. The one
production-file incremental diff is initializer.diff; exact before source retained.

Existing cash, currency, origin and recorded trading/equity history are preserved.
Inherited behavior is explicit: nonfresh accounts may still receive missing
cash/realized defaults as before; this is NOT a claim of no writes or byte-for-byte
identity on every nonfresh account. Missing legacy currency remains missing and
cash sizing fails closed. Even a matching pre-existing standalone currency key
does not authorize creation of a new certified origin.

## Verification

Same fresh-reader/bootstrap tests fail before and pass after. Initial new-file
before run:18failed5passed0.88s (three currency readers, four pre-existing-currency
freshness cases, currency-write rollback, concurrent coherent winner and all nine
fresh profile entries fail). Reviewer identified an equity-only freshness gap
before implementation; added case fails on old source (1failed4passed0.27s in its
legacy-history selection). BEFORE.txt retains primary failure output. Equity
counterexample is also recorded in the work log; no strategy result is altered.

After repair:24newtests passed0.91s. Consolidated five-file selection:
**243passed5.24s**, no failures/errors/skips/xfails (not full suite):

```sh
./.venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/test_paper_account_currency.py tests/test_paper_account_snapshot.py \
  tests/test_paper_account_reconciliation.py tests/test_paper_cash_entry.py \
  docs/review_artifacts/paper_profile_candidate_20261114/test_profiles.py \
  --runxfail --tb=short
```

Nine cases load the original unchanged candidate YAML files into private temporary
state, initialize the actual engine, read fresh metadata/quotes and size entries
without any manual currency write. Restart retains changed cash, and a subsequent
sizing uses that cash. Unit cases cover normalization, pre-existing/missing legacy
currency/history, currency/origin write rollback and concurrent initializers with
different cash/currencies producing exactly one internally consistent winner.
Existing account reconciliation, fee/fill and metadata/refusal regressions are
included. Synthetic operational/risk gates remain stubbed as explicitly described
in the original profile fixture; this is not those gates' acceptance evidence.

Original profile tests/receipts/checksum seal are unchanged historical evidence.
Its strict xfail now passes under --runxfail; running that old file without this
option intentionally reports XPASS(strict), not a new production failure. The old
manifest binds the previous store version and is not a current-source seal. This
artifact's new seal supersedes only that source binding; no YAML was changed.

VERIFIED_ENV: existing local venv, temporary SQLite/synthetic public inputs.
No actual config/cache/ledger, credentials/accounts, market HTTP, host/service/
schedule, R10/tool/cloud, installation, deployment/trading or commission occurred.
git diff --check passed; no full-suite or operating/financial result claimed.

## Acceptance and outstanding questions

DONE (separately reviewed source scope): atomic fresh currency, no legacy
inference/reset, all nine fresh loaders/sizers, rollback/restart/concurrent and
existing focused regression proof. NOT DONE: actual profile or metadata deployment,
refresh cadence, permissions/capacity, R7 owner decisions, monitoring/backups,
commissioning, experiment activation and forward economics. R10 stays STOPPED;
the original commissioning criteria and Group B staging remain unchanged.

Independent review receipt states exact source/test hashes and its own proof:
25focusedtests passed0.99s; author243total was not independently repeated.
What could overturn the narrow source conclusion: a missed definition of prior
history or a source/runtime-version mismatch. No actual legacy account migration
has been designed or performed; unknown denominations still need independent evidence.

What do I know that could change the owner's decision that I have not yet said?
Existing ledgers without independently established currency remain unresolved.
Fixing fresh bootstrap does not make the simulation operational or profitable.
