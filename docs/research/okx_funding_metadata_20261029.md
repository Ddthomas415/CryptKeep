# OKX funding metadata: one public evidence capture

2026-10-29, America/New_York. Active role: AUDITOR.
Evidence review: READY_FOR_INDEPENDENT_REVIEW. Original Fix3: INCOMPLETE.

## Result

SHOWN: at 06:36:17-18 EDT (10:36:17-18 UTC), three fixed public GETs
returned HTTP200/API code0 with BTC-USDT-SWAP identity throughout. Capture
elapsed0.772 seconds, three requests, no retries or redirects. All three raw
body hashes and byte lengths were checked after capture. The existing sample
plan names OKX BTC/USDT:USDT; its configured8h value was not used as evidence.

One fresh directory preserves original response bytes, local request/receipt
times, public URLs, HTTP/API outcomes, instrument identity and source/curl/SDK
hashes:

`docs/review_artifacts/okx_funding_metadata_20261029/20261029T103617Z_2668220f5a85484580a593b0207494d4/`

## What the responses show

- Current endpoint: fundingRate0.0000436849743302, fundingTime16:00UTC Oct29,
  nextFundingTime00:00UTC Oct30, prevFundingTime08:00UTC Oct29. Scheduled
  difference8h; source ts10:36:13.443UTC. These times have distinct meanings.
- Current response reports settState=settled and
  settFundingRate0.0000338041564747. That is NOT the same number as fundingRate.
  Do not apply settState to every numeric field in the response.
- History endpoint: five rows, four adjacent8h gaps. Its newest fundingTime
  matches current.prevFundingTime, and its realizedRate matches the current
  settFundingRate exactly by Decimal comparison. Current fundingRate differs.
- Current/history rows report formulaType=withRate and method=current_period.
  Instrument response identifies a live linear swap settled inUSDT.

SHOWN is limited to payload contents and cross-response arithmetic. The venue's
claims that rates are realized/settled and the instrument is live are CLAIMED
by the public API, not independently observed account settlement or execution.
Eight-hour spacing in these rows does not certify every historical interval.
formulaType does not by itself certify the effective formula or migration date.

## Capture and verification boundaries

The one-shot capture.py is a local evidence artifact, not an installed job or
collector. VERIFIED_ENV: installed SDK routes and /usr/bin/curl8.7.1 inspected.
Execution used a clean environment, TLS verification, no curl configuration,
no proxy, no redirects/retries, max1MiB per response, max10s per subprocess and
45s request-loop deadline. Initial/final local file work is outside that deadline;
it is not a hard kill bound on filesystem stalls. No extra fetch was attempted.

Before the capture, four synthetic cases passed: valid response, wrong identity,
API error and subprocess timeout. They exercised the actual capture function
with a fake subprocess and disposable directories, asserting three calls,
environment, timeout, redirect/retry controls and no normalization authority.
These are capture checks, not financial-validity tests or a full suite.

Command actually run once, exit0:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -B docs/review_artifacts/okx_funding_metadata_20261029/capture.py
```

An offline check then verified3/3 hashes/lengths, converted timestamps, checked
four historical gaps and compared the two latest-settlement fields exactly.
No normalized/annualized values were calculated, no production source changed,
and no original observation/model artifact was rewritten. capture_complete
means transport/JSON/API/identity checks passed, not semantic qualification.

## Next source consequence

The existing default collector reads a current rate. Historical realizedRate
is a different evidence lane, not permission to relabel or backfill the current
rate as settled. A positive qualification contract must retain endpoint/field,
settlement time, interval evidence and formula evidence separately. Preserve
unknown cases and distinguish cash-cost normalization from crowding inference.

Next useful step: specify and synthetically test endpoint-specific qualification
against this saved sample, keeping all strategy eligibility disabled until that
contract is independently reviewed. No additional capture is necessary merely
to repeat this sample. Do not rewrite legacy history or run a new market study.

No SDK client, private account, credential, database/schema, collector/service,
scheduler, Docker/server, capital/risk-setting, trading, deployment, commit or
push operation. Endpoint semantics beyond the documented cross-checks,
historical formula applicability, operational integration and economics remain
UNVERIFIED. Existing Fix3 source acceptances are not reopened by this capture.

## Sources accessed

- Public current: https://www.okx.com/api/v5/public/funding-rate?instId=BTC-USDT-SWAP
- Public history: https://www.okx.com/api/v5/public/funding-rate-history?instId=BTC-USDT-SWAP&limit=5
- Public instrument: https://www.okx.com/api/v5/public/instruments?instType=SWAP&instId=BTC-USDT-SWAP
- Installed route/field source: .venv/lib/python3.12/site-packages/ccxt/okx.py;
  exact SHA in capture manifest. No SDK was instantiated.
- Prior primary-document limits: docs/research/funding_formula_evidence_20261029.md.
