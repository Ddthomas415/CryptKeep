# Auth Scope And MFA

## Current Default

- The repo defaults to `local_private_only` auth scope.
- Built-in dashboard auth is acceptable for local/private use with caution.
- The repo should not be described as hardened for remote/public exposure by default.

## Built-In MFA

- Built-in TOTP MFA is available for keychain-backed users.
- MFA enrollment is user-scoped and can be completed from the dashboard auth surface.
- Backup codes are generated during enrollment and are one-time recovery codes.
- Password-only login is not sufficient once MFA is enabled for a user.

## Dev-Only Exceptions

- `BYPASS_DASHBOARD_AUTH` is only honored when `APP_ENV=dev`.
- `CBP_ALLOW_ENV_LOGIN` is only honored when `APP_ENV=dev`.
- Bootstrap auth env must be complete to avoid partial configuration warnings.

## Remote/Public Rule

- Remote/public deployment requires MFA plus stronger outer access controls.
- Acceptable outer controls include VPN access, reverse-proxy auth, or equivalent gated access.
- The dashboard settings should explicitly name the configured outer access-control layer when remote/public candidate mode is selected.
- Built-in MFA alone is not enough to claim that the repo is remote/public hardened.

## Honest Deployment Claim

Use this description:

`The repo supports local/private sign-in with optional built-in TOTP MFA for keychain-backed users, but remote/public deployment still requires stronger outer access controls and should not be treated as hardened by default.`
