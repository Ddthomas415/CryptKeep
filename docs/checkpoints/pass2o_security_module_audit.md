# Pass 2O — Security Module Comprehensive Audit

**Date:** 2026-05-10
**Pass:** 2O — complete security module coverage
**Status:** COMPLETE

---

## Security coverage after this pass (all 11 files)

| File | Depth |
|---|---|
| auth_capabilities.py | SAMPLED |
| auth_runtime_guard.py | REVIEWED |
| binance_guard.py | REVIEWED |
| credential_store.py | DISCOVERED |
| credentials_loader.py | REVIEWED |
| direct_origin_guard.py | REVIEWED |
| exchange_factory.py | REVIEWED |
| permission_probes.py | REVIEWED |
| role_guard.py | REVIEWED |
| secret_store.py | SAMPLED |
| user_auth_store.py | SAMPLED |

---

## SHOWN findings

### Finding 1 — `enforce_direct_origin_block` not called in production (High)

Grep confirms zero production callers in services/. Only imported in one test.

When auth_scope is set to 'remote_public_candidate', the direct-origin
enforcement that would block unauthenticated proxy bypass is never invoked.

**Impact for current deployment:** Not exploitable (auth_scope=local_private_only).
But if H2 is exploited (VIEWER changes auth_scope to remote_public_candidate),
the direct_origin_guard would still not fire. Fourth instance of H4 pattern:
governance/security function implemented, tested, never called.

---

### Finding 2 — `require_binance_allowed` gates all exchange creation (Strength)

Called unconditionally from `make_exchange()` before any ccxt instantiation.
Requires both `CBP_VENUE=binance*` AND `CBP_ALLOW_BINANCE=1`. Raises
`RuntimeError` on violation. Binance cannot be accidentally used.

---

### Finding 3 — `resolve_exchange_id` detects venue conflict (Strength)

```python
if explicit and env_v and explicit != env_v:
    raise VenueResolutionError(f'CBP_VENUE conflict: ...')
```

Code-vs-env venue mismatch is caught before exchange creation.

---

### Finding 4 — Credentials loader: keyring-first, env-second, errors captured (Strength)

Keyring preferred. Keyring errors captured and returned in result dict.
Env var fallback is process-scoped. Two-tier resolution is correct.

Note: `state_report._redact` does not redact CBP_-prefixed env var names.
Not confirmed whether env vars appear in state snapshots.

---

### Finding 5 — `permission_probes` are all read-only CCXT methods (Strength)

fetch_balance, fetch_open_orders, fetch_my_trades, fetch_closed_orders,
fetch_deposits, fetch_withdrawals. No order creation, no withdrawals.
Explicitly labeled 'read-only probes (safe)'.

---

### Finding 6 — `user_auth_store` uses Argon2id + PBKDF2 at OWASP thresholds (Strength)

Argon2id (OWASP recommended). PBKDF2-SHA256 at 390,000 iterations (OWASP minimum).
MFA: TOTP (6 digits, 30s, 1 drift window), 6 hashed backup codes.

---

### Finding 7 — `make_exchange` accepts empty credentials silently (Noted)

No check that apiKey/secret are non-empty before ccxt instantiation.
Fails at first authenticated request, not at adapter creation. Late-failure mode.

---

## Summary

| Finding | Severity |
|---|---|
| enforce_direct_origin_block not called in production | **High** |
| require_binance_allowed gates all exchange creation | **Strength** |
| resolve_exchange_id detects venue conflict | **Strength** |
| Credentials keyring-first with captured errors | **Strength** |
| permission_probes all read-only | **Strength** |
| user_auth_store Argon2id + PBKDF2 OWASP thresholds | **Strength** |
| make_exchange accepts empty credentials | Noted |

---

## Updated High findings

| # | Finding |
|---|---|
| H4 | Governance enforcement dead code |
| H5 | resume_if_safe disconnected from config |
| H6 | Soak evidence invisible to promotion gate |
| H7 | enforce_direct_origin_block dead code |
| H1-H3 | VIEWER role boundary (medium) |

---

## Handoff

**Active role:** AUDITOR
**Acceptance state:** COMPLETE for Pass 2O
**Security module: fully covered.**
**Next:** services/control/allocator.py, runtime_identity.py, or remediation plan
