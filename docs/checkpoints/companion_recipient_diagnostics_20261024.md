# Recipient Binding Diagnostics

Role: ENGINEER. Risk: HIGH. State: READY_FOR_INDEPENDENT_REVIEW.

## Objective And Scope

Expose the first observed recipient-binding refusal using fixed, secret-free
labels. Keep existing recipient policy, full-inventory ownership checks, native
command sequence and fail-closed result. No runtime attempt or capture.

V6c already failed and recovered. Its aggregate recipient_bindings=false did not
retain the subpredicate. This patch cannot establish that historical cause.
Existing consumed receipts, removed replacement IDs and frozen packets remain
unchanged. Updated consumers intentionally invalidate old wrapper hash bindings;
no ready-to-execute replacement packet is generated here.

## Changes

- companion_runtime_adapter.py: optional diagnostic sink for existing boolean
  binding checks, fixed predicate/exception labels and selected/unselected/none
  role. Only the seven approved names may appear as target; no unselected name,
  network metadata, raw exception text, token or environment value is emitted.
- V2 compatibility envelope: optional recipient_diagnostic. Legacy boolean maps
  remain unchanged. Reason is local to each call; successful calls emit null.
- companion_installer.py: accept old/new envelope shape, validate reason again at
  receipt boundary and record it before refusal/cleanup. Unknown fields/labels
  are dropped. Existing compatibility booleans still determine acceptance.
- tests/test_companion_recipient_diagnostics.py: 35 synthetic tests covering
  configured network checks, raw recipient policy, selected/unselected failures,
  bounded exception categories, malformed receipt diagnostics and no start/query
  after false compatibility. No native process, socket or real credentials.

Every original refusal comparison is retained. Projection of unrelated rows and
the alias/port/mount/ownership checks are not weakened or skipped. First failure
means traversal order, not a unique root cause; later failures remain unknown.
Malformed data inside the legacy recipient helper may yield the broader
recipient_policy exception category rather than a field-specific reason.

## Verification

VERIFIED_ENV for isolated local offline tests only:

```sh
env -i PATH=/usr/bin:/bin PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 ./.venv/bin/python -B -m pytest --noconftest -c /dev/null -p no:cacheprovider -q tests/test_companion_recipient_diagnostics.py tests/test_companion_active_network_contract.py tests/test_companion_staged_composition.py tests/test_companion_running_update.py tests/test_companion_runtime_adapter.py
```

201 passed in 1.94s. git diff --check passed for the two changed source files.
No full-suite claim, market study, Docker command, credential read, startup,
replacement preparation, reservation reset or query.

## Frozen Source Identity

Before this patch (accepted historical consumers):

```text
companion_runtime_adapter.py dcc33a6d454c7d6f9970103ad331d97cd88f2a8023f321cd381a729d2e05f7c7
companion_installer.py 4c684b1766fcb2e21b3dc1c03cbe5aa607694f63b9d64c512a19ad6c11792b17
```

After implementation:

```text
companion_runtime_adapter.py 4d32ab77c9183381f342f4202a9bd6bf1084de636e9d23b6ec30e7739a4fd248
companion_installer.py d0cfb0814b8884e790e794226e58629da1d587a797b4777b7dc4d3a54b232de7
test_companion_recipient_diagnostics.py e255c9555ce4066fb4721d3621c3688505374dece6b9645cdc52cf60b0791a2a
```

Pre-existing worktree changes are preserved; a git diff against HEAD also
contains earlier accepted changes, not only this patch. This bounded change is
the diagnostic constants/helpers, optional _bindings/_configured_bindings sink,
V2 reason field and installer sanitization/receipt field described above.

## Independent Review Required

Check refusal parity, no extra native work, absence of raw-value leakage,
legacy envelope compatibility and receipt ordering. Review/test only offline.
Runtime remains INCOMPLETE, with no operation or retry authorized by acceptance
of this patch. After review, select the next justified offline/observational step
without claiming the failed V6c cause or silently creating another attempt.
