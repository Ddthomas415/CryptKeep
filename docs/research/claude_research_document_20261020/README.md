# Claude's research document, imported into the repo (2026-11-05)

Bot relation: STANDALONE; runtime configuration not checked. This is a record import: no bot code, configuration or runtime was inspected for it.

## What this is

This folder holds the complete text of Claude's (Cowork) research document "CryptKeep research audit, revised brief and
next experiments". Until now it existed only as a private claude.ai artifact, so Codex and `docs/PROJECT_STATE.md`
could not see it.

It was imported at the owner's direction on 2026-11-05 ("take care of what needs to be done for codex"). The import
answers these open items:
- Codex's on-chain handoff audit, recommendation 1 (`docs/research/onchain_handoff_audit_20261105/README.md`);
- omission O-97;
- `PROJECT_STATE.md` rows U-27 and U-28.

## Files

| File | Contents |
|---|---|
| `research_document_rev129.md` | The document as produced by the Claude Docs markdown export, unedited. 146,703 bytes, 668 lines, SHA256 `8f138aec87e859c8426320101c50b911852fa8cbf98c0273261d0a8294b67152`. |
| `proposed_rules_reconciliation.md` | The 30 research rules the document proposes, quoted word for word, each with a search of the canonical files. All are PROPOSED, not adopted. |

## Provenance

- **Source:** claude.ai artifact `9N9nKeyLa1MStLzzq9SRsh`, revision 129, exported 2026-11-05.
  - The export tool reported 4 date chips and 1 mention chip "kept as text"; they appear as plain text (for example "Oct 20, 2026 · @Damian Thomas").
  - Nothing was edited after export.
- **Dates covered:**
  - Sections 1 to 6 are dated 2026-10-20.
  - Sections 7 to 29 are dated updates from 2026-10-21 to 2026-10-30.
  - From section 29 (2026-10-30) the document says `docs/PROJECT_STATE.md` is the current record and the document is history.

## How to read it

- **Not independently reviewed.** Claude wrote and self-checked it. Its opening says an independent fact-check of the first draft found 10 errors, corrected in the text. Codex has not reviewed the whole document. Nothing in it is independently accepted unless a work-log GATE entry says so.
- **Rankings are proposals.** Its experiment rankings (sections 4 and 15) were Claude's proposals, never an owner-approved queue. The queues in `PROJECT_STATE.md` replaced them on 2026-10-30. On 2026-10-28 Claude held UNLOCK-1, FRESH-1, CTREND-OOS and Module A (`docs/checkpoints/claude_cowork_direction_20261028.md`). Apart from CTREND-OOS (listed under Closed as on hold), they were not carried into `PROJECT_STATE.md`. They are now rows U-12, U-13 and U-21 of its "Undecided ideas" table.
- **Rules are proposals.** The research rules are proposals ("proposed for the brief", section 8). No record of owner approval was found, and none is in `AGENTS.md` or `RESEARCH_BRIEF.md`. See `proposed_rules_reconciliation.md`.
- **The decision list is historical.** The "Decisions needed from you" list at the end is a record. Most of its items were never answered; the open ones are rows in the `PROJECT_STATE.md` "Undecided ideas" table.
- **Later corrections are not applied to this copy.** Labels (SHOWN, CLAIMED, UNVERIFIED) are as written at the time. Before relying on a figure, check the work log and `PROJECT_STATE.md` (open caveats, omission register). One known example: the 2026-11-05 on-chain corrections (O-98) concern a later chat answer, not this document, but its on-chain rows (family 17, ONCHAIN-1) should be read with them.
- **Scout sorting stops at T08.** Sections 8, 14, 16, 17 and 20 to 26 sort scout leads up to report T08 (2026-10-30 11:43 UTC). Reports T09 (2026-10-30 19:43 UTC) and T10 (2026-11-02) are not sorted here.

## Time-sensitive item

Proposed rule R28 says no new question may be scored on the CMC trending log unless it is registered before the log's window
opens on 2026-11-10. The document recommended against adding the scout's suggested question. Whether to adopt the
rule is the owner's decision.
