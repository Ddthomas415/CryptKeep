# AGENTS.md edits applied 2026-11-14T23:44:52Z (Claude, owner-approved)

Owner approval: after Claude's report on Codex's defect pattern (12 own-draft defects caught before acceptance,
3 pre-existing, 3 process/scope errors O-155/O-165/O-166 in 26 hours), Claude proposed two changes; the owner
answered "get it done" (2026-11-14, about 23:40Z).

Applied (before `b6b847ef437a5fd9…`, after `4ef66389f399d1f4…`; `edits.diff`, `AGENTS_md_before.md`):
1. "Evidence and omissions": new rule **Authority and scope**: accountability records always; every other change
   needs owner authorisation or an approved task; no agent lifts or widens a restriction, approval, stop or scope by
   inference from a general instruction; reused commands/packets re-read against the current approval (O-155, O-165).
   This is edit 2 of `/mnt/user-data/outputs/AGENTS_md_proposed_edits_20261113.md`, reworded to name inference.
2. "Task card": the card states its failure matrix; **Self-check before review**: every matrix row tested
   (fail-before/pass-after) or declared untested with a reason, before an independent review is requested; a request
   without the record is returned (O-156 to O-172).

Not applied (still proposals, owner decision pending): edit 1 (INFERRED/DISPUTED labels), edit 3 ("found by relative
to author" and "repeat of" register fields), edit 4 (quality gate: "implementation complete (self-checked)" vs
"verified complete"), the auditor charter v3.

Applies to both agents; Claude's own O-154/O-173 are the same class as rule 2's intent (re-check before hand-off).
