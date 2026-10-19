# AI and probability order gates: independent review (deferred live-money item 16)

Date: 2026-10-05. Reviewer: Claude (AUDITOR then ENGINEER).
Status: READY_FOR_INDEPENDENT_REVIEW, HIGH risk (live order routing; the
change only refuses). Patch 0056 (`d39f74ff`), bundle rev67, folder
`64_order_gates_cannot_pass_blind`. Not pushed, not applied to this checkout.

## What holds

An enabled AI or probability gate that raises refuses the order. A disabled
gate is not evaluated. Both gates are off in this checkout's runtime config
(`ai_engine.enabled: false`), and no model file exists here.

## Findings (shown by test; reachable only with a gate enabled)

| Broken state | Old behavior |
|---|---|
| AI gate on, model file missing | every order allowed (`model_missing_pass_through`) |
| AI gate on, model file corrupt | every order allowed, reported as "missing" |
| NaN weight in the model | read as probability 1.0; every buy allowed |
| `CBP_AI_BUY_THRESHOLD=nan` (or sell) | no order ever refused |
| Probability gate on, `CBP_FUSED_PROBA` = `nan` or `inf` | clamped to 1.0; every buy allowed |
| Probability gate on, value missing or unparseable, not strict | 0.5 substituted |

Enabling the AI gate on this machine today would have hit the first row.

## Correction

- `AISignalService.evaluate`: no usable model returns `ok: false`
  (`model_missing`, `model_unreadable`).
- `LinearSignalModel`: non-finite score or threshold raises; the router
  already refuses on an exception.
- `proba_gate`: an enabled gate needs a finite probability in 0..1 and
  finite thresholds; `strict` no longer decides this.
- `docs/AI_ENGINE.md`: pass-through wording removed.

Contract change: `model_missing_pass_through` no longer exists; a
probability outside 0..1 is invalid instead of clamped.

## Verification

48 new tests, 40 fail on the previous code. Full suite at the code of 0056:
4738 passed, 33 skipped, 19 failed (the same 19 as master).

## Not changed

The gates stay off by default and still sit outside the
strategy/evidence/promotion system, which item 16 also flags.
