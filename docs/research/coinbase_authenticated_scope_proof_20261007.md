# Laptop Coinbase authenticated scope observation

Active role: AUDITOR. Read-only operation approved by user continuation of the
recommended actual-session verification. Observed 2026-10-07T22:46:59Z.

SHOWN: existing shared credential loader selected Keychain, key and secret were
present, and no Keychain error was reported. A fresh installed CCXT Coinbase
session used those credentials for the portfolio observer's key-permissions
request. Observer validated a non-nil portfolio UUID, DEFAULT portfolio type,
can_view=True and can_trade=True. Process exited 0. Secrets, raw response and
portfolio identifier were not displayed or saved. No credential writes occurred.

Redacted observed output:
```json
{"surface":"laptop","credential_source":"keyring","key_present":true,
"secret_present":true,"keyring_error_present":false,"private_request_sent":true,
"status":"verified_portfolio_response","portfolio_uuid_valid":true,
"portfolio_type":"DEFAULT","can_view":true,"can_trade":true}
```

VERIFIED_ENV: laptop checkout, existing Python/CCXT, existing Keychain source.
One permissions request attempted; no order, transfer, balance mutation, config
change, credential rotation, collector restart or database binding performed.
No tests rerun; this was a scoped integration observation, not a suite run.

Official contract:
https://docs.cdp.coinbase.com/api-reference/advanced-trade-api/rest-api/data-api/get-api-key-permissions

UNVERIFIED: identity of historical position/order rows, global user identity,
Hetzner credentials/session, credential persistence in future sessions, all
production writers, endpoint-hardening against configurable override, and live
exit authority. Permission to trade is not authorization to submit orders.

The observed UUID was retained only transiently in process memory. No dedicated
database can be declared bound from this redacted record alone. Next step is a
reviewed same-session portfolio namespace contract and binding of a NEW isolated
database only after holdings/open orders provenance is addressed. Never adopt
old balances merely because current permissions succeed.

Acceptance: READY_FOR_INDEPENDENT_REVIEW for interpretation and next scope.
Review outcome: Hume ACCEPTED_WITH_RISK for bounded interpretation; actual
request was not independently repeated. No database binding or live approval.
