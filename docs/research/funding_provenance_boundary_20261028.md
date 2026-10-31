# Original Fix3: funding provenance and interval boundary

2026-10-28. Active role AUDITOR. HIGH-risk financial evidence.
Acceptance: READY_FOR_INDEPENDENT_REVIEW, diagnostic scope only.
Fix3 implementation and operational repair: INCOMPLETE.

## Question and answer

Can existing funding collection/storage/scoring distinguish rate origin and
interval before comparing or annualizing rates?

SHOWN in selected current source with invented inputs: no. Recording an interval
alone would not repair the scoring and summary consumers. This is the original
derivatives funding-rate Fix3, not CBA-FUNDING-SCOPE-20261028.

## Reproduced findings

- Collector uses plan interval or 8.0, including when the payload says 1h/4h.
  A missing interval is emitted as 8.0 with an OK check.
- fundingRate and nextFundingRate-only payloads produce identical collected
  rows; predicted origin cannot be distinguished in that result.
- Supplied exchange timestamp, next settlement timestamp, source-field and
  formula provenance do not survive collection.
- Existing store append drops those fields even when explicitly provided.
  The local capture timestamp is separate from exchange time; it is not shown
  to be future-dated by this test.
- Alternative-data scoring ignores the provided interval and uses rate times
  three times 365 for annualization.
- Archive summarize_funding_carry ignores each row's interval_hours, using its
  single argument (default 8.0) instead.

In invented equivalent constant-rate schedules, 0.0001 per hour and 0.0008
per eight hours have the same simple annualized magnitude. Current summary/
alternative-data code emits 10.95% and 87.60% respectively; alternative-data
crowding signals are neutral and overleveraged_longs. This demonstrates the
code's interval sensitivity error under that toy contract. It does not certify
any venue's funding formula, realized cash flow, current API contents or yield.

## Verification

VERIFIED_ENV, isolated repository venv. AST-select actual collector, store
append, alternative-data and summary bodies. No application-entry/config/
credential loader imports, real SDK client or request. Invented SDK module,
fixed clock input and in-memory SQLite initialized from unchanged source DDL.
Socket/DNS entry points refuse access. Pure decimal helper imported.

    env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q --tb=short tests/test_funding_provenance_boundary.py

Final author result: 8 passed in 0.19s, exit 0. Earlier seven-case run passed
in 0.21s before adding the downstream summary reproduction. Tests intentionally
assert current defects; passing means reproduced, not repaired.

No production source changed. No market-data run, historic strategy rerun,
real database, schema/migration, collector/scheduler/service operation,
account/credential access, dependency, trading or git publishing action.

## Next bounded treatment

Repair the provenance contract across collector, storage and scoring together:
retain raw rate/source field and predicted/settled/unknown meaning; separate
receipt time, exchange observation time and settlement time; require an
evidenced interval and formula basis before normalized scoring/annualization.
Unknown must not silently mean eight hours or neutral. Preserve unknown raw
observations for diagnosis and keep legacy rows explicitly unverified.

Storage compatibility is a material boundary: funding_snapshots currently
requires interval_hours NOT NULL, append defaults it to eight, and readers
coerce it to float. Do not insert a fabricated zero/eight, silently lose raw
observations, modify frozen archives or run a migration to bypass this.
The unknown-observation persistence contract and venue/formula evidence must
be settled before applying a production writer/consumer change.

No current Binance/OKX formula, timestamp semantics, vendor claim or historical
cutover date was independently verified in this diagnostic. No blanket
rate-times-eight-over-interval fix is approved by these toy tests.
