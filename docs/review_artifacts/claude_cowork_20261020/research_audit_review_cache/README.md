# Research audit review cache

Recorded 2026-10-20T11:49:02Z. Active role: AUDITOR.
Purpose: preserve reviewed material so continuation reviews inspect changes,
not repeatedly navigate the same Claude conversation.

## Preserved source and coverage

- `shared_document_original.txt` is a byte-for-byte copy of the complete
  601-line attachment, not a rewritten summary. Its SHA256 matches the original:
  `f1dcd135b7758bc139ee63519b75a813c3af8a0f2013af13034cab3640d40443`.
- Original attachment:
  `/Users/baitus/.codex/attachments/b91816e3-3b63-4020-be39-cdc4da0616e5/Pasted text.txt`.
- Claude conversation: `https://claude.ai/chat/29680875-3383-4850-a7f5-e5e2137da59a`.
- The earlier audit covered positions 1-78; position 19 was empty in the UI.
  This review read the new messages 80-90 and the later storage discussion
  91-96. Position 79 was not successfully retrieved in this review. Do not
  describe this cache as a complete conversation export or claim every message
  was read. The latest completed response observed was position 96.
- Raw UI observations remain in this Codex conversation's tool outputs. They
  have not been exported here. The attached document copy is complete; the
  conversation coverage record is a checkpoint, not a verbatim transcript.
- Storage claims in messages 91-96 were observed, not independently audited.
  No deletion, backup, publication or operational change is authorized here.

## Review already delivered

Disposition: INCOMPLETE for experiment freeze, not rejection of further research.

1. SHOWN: pre-December-2020 funding records already enter E7's expanding
   thresholds. FUND-1 must not describe those inputs as untouched holdout.
2. SHOWN: a blanket claim that all altcoin rules lost is contradicted by the
   corrected top-10 result (+20.5%, while trailing BTC). Preserve absolute
   return, benchmark failure and promotion failure as separate conclusions.
3. SHOWN: E1 includes fees; the existing rebalance function charges fees
   separately. Substituting all-in cost for slippage risks charging fees twice.
   The $23-32 annual saving illustration is conditional and fee-only, not a
   profit forecast. Turnover already counts buys and sells; do not double it.
4. SHOWN: the inspected live gate does not check its parsed position-limit
   field. UNVERIFIED: effective whole-system $50 position protection. Static
   YAML alone does not establish runtime enforcement.
5. UNVERIFIED: historical unlock-schedule versions and point-in-time coverage.
   A documented `lastModified` field does not prove historical reconstruction
   possible or impossible. No paid purchase recommended before feasibility.
6. SHOWN: independent $1,000 cycles do not by themselves establish continuous
   portfolio drawdown. UNLOCK-1 needs explicit valuation, unknown-data,
   timestamped supply and placebo-cohort rules before freeze.
7. UNVERIFIED: the claim that excluding 2.6% of picks can barely affect returns.
   Selection counts alone do not bound economic contribution.

Independent reviewer Noether (`01a15192-29d6-7ac0-b554-5f7bba16ca79`)
separately checked E1, configured caps, fees and turnover. Its response is
preserved in this Codex conversation; it is not a complete second audit of
every research family. No experiments or tests were run in this review.

## Resume without repeating work

1. Read this checkpoint and compare new attachments against the saved source.
2. Request/read only new messages after position 96, explicitly changed earlier
   messages, or a specifically needed unresolved message (such as 79).
3. Message numbers are navigation hints, not immutable identities. Confirm the
   conversation URL and nearby text; editing or pagination may shift numbering.
4. Compare relevant file hashes in `SHA256SUMS` before reusing code findings.
   These pin reviewed versions, not current runtime state or acceptance of edits.
5. Reopen only findings affected by a changed source or contradictory evidence.
   Do not rerun old backtests, re-audit accepted repairs, or use repeated UI
   navigation as a substitute for retaining the reviewed material.
6. If a full chat export is later supplied, preserve it separately with its
   hash and fill the specific coverage gap; do not overwrite this original.

Cache creation: LOW risk, VERIFIED_ENV for local copy/hash verification.
Acceptance: ACCEPTED for preservation only. Research-plan disposition unchanged.
