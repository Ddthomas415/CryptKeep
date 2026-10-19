# Claude (Cowork) handoff to Codex, 2026-10-18

Written 2026-10-18T23:10:12Z by Claude (Cowork) at the operator's request ("document our work for codex to take over").
Status words: VERIFIED = re-checked by Claude against current files today; CLAIMED = stated, not verified.
This file grants no authorization. AGENTS.md, runtime_prompt.md and the "Current correction scope"
in REMAINING_TASKS.md control. Where this file and those disagree, they win.

## Standing limits (unchanged)
- No live trading, Docker, server, account, credential or secret access. Never read `.env`,
  `.env.private.local`, `.browser-access-token`, `.browser-compose-override.json`, `config/user.yaml`.
- No strategy run on market data without operator approval. Do not edit verdicts, frozen criteria,
  manifests or artifacts.
- No commit, push, lock removal (`.git/index.lock`, 0 bytes, Oct 4) or companion retry/startup
  without explicit operator authorization. Work is reviewed before any push.

## 1. Open item ready to pick up: two stopped-recipe test failures
Tests: `tests/test_companion_stopped_recipe.py::test_legacy_evidence_not_upgraded_to_paired_proof` and
`::test_paired_payload_can_be_verified_offline`, both `ValueError("reconciliation_fingerprint_mismatch")`
from `reconcile_manifest` in `scripts/research/collect_companion_recreation_metadata.py`.

Cause (VERIFIED): `docs/review_artifacts/companion_recreation_metadata_20261017/capture4/observation.json`
(fingerprint_version 1) stores 11-key snapshots (attempt, foundation, id, image, metadata, name, networks,
policy, restarts, started, state). `Snapshot` in `scripts/research/companion_installer.py` now also has
configured_metadata, configured_networks and network_evidence (with defaults), so `asdict()` gives 14 keys and
the canonical JSON differs. The 11 shared fields are equal. List vs tuple for networks is irrelevant
(`_canonical` is json.dumps). Codex's 20:28Z log already shows the failures on the preserved pre-change
source, so they predate the 20:25Z installer change.

Proposed fix, NOT APPLIED: `~/Documents/cryptkeep_data_archive/stopped_recipe_fix_proposal_20261018/`
(README.md, `collect_companion_recreation_metadata.proposed.diff` sha256 f299204a..., SHA256SUMS).
For v1 evidence only: require the three new fields to be defaults, then compare the 11 legacy keys. v2 path
unchanged; frozen evidence untouched. Scratch-copy result: 24 passed (was 22 passed / 2 failed). Seven tamper
cases rejected (metadata digest, foundation digest, network id, extra key, missing key, v1 relabelled v2,
tampered observation row).
To finish (needs operator approval; HIGH-risk installer code):
1. Apply the diff. 2. Add a permanent regression test for the seven tamper cases.
3. Run the focused selection (was 163 passed / 2 failed; expect 165 passed before the new test is added). 4. Independent review.

## 2. Reviews done by Claude today (read-only)
- Module A candidate (`scripts/research/module_a_candidate.py` bd7139ff..., tests 8939cbc7...):
  reproduced 26 passed at the time of review. Real-data blockers found: 89 of 492 Coinbase markets stop and
  15 have gaps; a missing price stops the run; benchmark 4 is missing; harness parity not done. Since then
  GATE-MA-001 closed (see `docs/checkpoints/module_a_allocator_coverage_20261018.md`); the blockers above are
  not addressed by that test-only change.
- Information-edge feasibility count: best near-term candidate is a NEW, pre-registered funding-rate hypothesis
  on BTC/ETH using `research/crash_brake_20261013/binance_funding_raw.jsonl`. Data reuse caution: D_FUND
  Dec 2020-Oct 2026 has already been seen by E7; only roughly late 2019-Nov 2020 is unseen. The collector
  store `.cbp_state/data/crypto_edge_research.sqlite` covers OKX BTC only, Jul 11-Oct 18, with gaps.
  Exchange status-incident rate (~25 per 3.5 weeks, mostly wallet delays) is CLAIMED from an aggregator.
  Compare with `docs/research/information_edge_assessment_20261018.md`. No data run was made.
- Audit of Codex's Oct 18 work: operator spreadsheet `~/Documents/cryptkeep_data_archive/codex_oct18_audit.xlsx`.

## 3. Claude drafts outside the repo (all unapplied, under ~/Documents/cryptkeep_data_archive/)
- `companion_build_manifest_draft_20261016/`: build-context manifest draft, proposed `.env.example` (v2 with
  empty MinIO values) and `.dockerignore`.
- `operating_contract_draft_20261018/`: proposed AGENTS.md / runtime_prompt.md / CODEX_REMEDIATION_PROMPTS.md
  edits with diffs. Not adopted (see correction scope).
- `checkpoint_plan_draft_20261018/`: 4,104-row checkpoint file list (4,062 commit / 9 archive / 33 review).
  Needs refresh before any use; files changed since.
- `module_a_draft_20261018/`: SUPERSEDED. Has a look-ahead defect Codex found. Do not integrate.
- `git_bundle_20261018/`: bundle of unpushed commits 15bc4455a and 620bc8dbe (bundle verify OK, needs
  adde462ff). Restore command in README.txt.
- `stopped_recipe_fix_proposal_20261018/`: section 1 above.

Repo edits made by Claude today (logged): AGENTS.md "## Research questions" section; REMAINING_TASKS.md
operator queue (now historical) and off-machine backup status; this file and its pointer; work-log entries.

## 4. Decisions waiting on the operator (do not decide these)
1. Approve applying the section 1 fix (and who reviews it).
2. Git: remove the stale index.lock; make a checkpoint commit; push after review.
3. Confirm the TeraBox/MEGA uploads (still CLAIMED).
4. Module A rules: dated delisting settlement and missing-day handling.
5. Next research line: funding-rate pre-registration vs continuing Module A.
6. Whether to adopt any part of the operating-contract draft.
7. Cross-check audit comparison table (Claude's state audit) is still unfilled by Codex.

## 5. Claude Docs (operator can open on claude.ai; Codex cannot)
ED-001 scope; companion packaging scoping; Codex patterns review; state and Codex behaviour audit;
Module A pre-registration draft (with corrections); information-edge feasibility count. Repo files and the
work log are the source of truth for Codex.
