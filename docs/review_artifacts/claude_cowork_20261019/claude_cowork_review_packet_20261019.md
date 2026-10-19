# Review packet: Claude (Cowork) session, 2026-10-19 00:14-05:10 UTC

Purpose: let the operator and Codex audit everything this agent did before anything is finalized.
Nothing here is self-approval. Status words: SHOWN (re-checked against current files when this packet
was written), CLAIMED, UNVERIFIED. The work log entries named below are the primary record; this
packet is an index to them. The entry at 2026-10-19T00:02:22Z ("daily research scout") was written by
the previous agent, not this session.

## 1. What was done, in order

| # | Item | Changes | Work-log entry | State |
|---|---|---|---|---|
| 1 | Read-only verification of Codex's C1 (workbook) and C2 (VOLFC-1 supplement) | none | (reported in chat only) | Codex's claims matched files: workbook only Done!B7:C7 changed; 6,414 + 7 = 6,421 recounted from both manifests; supplement checksums and counts (214/4,999/50) match study files |
| 2 | Cross-agent read-only review of C3 (v1 stopped-recipe fix) | none in repo | 00:48:48Z | concurred ACCEPTED_WITH_RISK; 5 mutants caught; noted a wrong line in Plato's review file |
| 3 | C4: fail-closed pinned-input guard (v1) | new `scripts/research/pinned_run_inputs.py`, `tests/test_pinned_run_inputs.py` | 00:53:56Z | superseded |
| 4 | Independent review 1 | none | 01:01:50Z | **BLOCKED** (F1-F4); report: `review1_v1_BLOCKED.md` |
| 5 | Fix round v2 | replaced the two C4 files | 01:08:31Z | superseded |
| 6 | Independent review 2 | none | 01:24:29Z | **BLOCKED** (R1); report: `review2_v2_BLOCKED.md` |
| 7 | Fix round v3 | replaced the two C4 files | 01:37:21Z | current |
| 8 | Independent review 3 | none | 03:57:55Z | **ACCEPTED_WITH_RISK**; report: `review3_v3_ACCEPTED_WITH_RISK.md` |
| 9 | ENTR-CB-1 pre-registration DRAFT + checkpoint/backup plan | new `docs/research/coinbase_tradable_entrants_20261019/`; outside repo `~/Documents/cryptkeep_data_archive/checkpoint_plan_draft_20261019/` | 04:17:22Z | DRAFT, not frozen; nothing fetched |
| 10 | Correction: stale draft copy in repo | draft replaced | 04:39:01Z | see mistakes, section 3 |
| 11 | Operator-approved lock removal + local checkpoint commit | `.git/index.lock` deleted; commit `933d7ea2` on `checkpoint/2026-10-19` | 04:57:45Z | committed, NOT pushed |

## 2. Current artifacts (SHOWN)

| Path | SHA256 |
|---|---|
| `scripts/research/pinned_run_inputs.py` (C4 v3) | `6baef879499d10480a3685ccba4c0f5820c2a2fde2ee894221b600d1122ebae8` |
| `tests/test_pinned_run_inputs.py` (94 tests) | `b49b1a35d99d7fdb5501e7141cae1770006182806798ac5e7750ae447d2ae674` |
| `docs/research/coinbase_tradable_entrants_20261019/PREREGISTRATION_DRAFT.md` | `6b5cb12c57aa1e0f6e1461b986fd006a3851a0ddb33d935eb7220b42d7de33b5` |
| `.../entrant_ids_v2.csv` (107 IDs, 133 selections) | `aa9cd966206820afe3303ab633d6e12cfa69cea95b57cba7ac2337c280af0714` |
| `.../control_ids_v2.csv` (383 IDs, 8,382 selections) | `e2ad776fe21b10fbd84ef3a1350ba437dc71b59a46267d2a168ce8b1de28318f` |
| `.../SHA256SUMS` (covers the three files above, excludes itself) | `aff13bb14ee50824cf5fa3ef7a10fdfe48b8f376c74a3a1aa6b37341c70a9f6f` |
| Git commit on `checkpoint/2026-10-19` (parent `620bc8dbe`) | `933d7ea2f3c870993cf9bfd6de008b6c7c6adea5` |

Git state: working tree is on `checkpoint/2026-10-19`; `codex/research-bundle-proof` unchanged at
`620bc8dbe`. Uncommitted after the commit: the work-log entries written after it, this review folder,
and the 9 keep-out files listed in the plan folder's `archive_outside_git.txt`. No push, no bundle.

Audit evidence in this folder (`docs/review_artifacts/claude_cowork_20261019/`), previously only in the
agent's cloud workspace:
- `review1_v1_BLOCKED.md`, `review2_v2_BLOCKED.md`, `review3_v3_ACCEPTED_WITH_RISK.md`: the three
  reviewers' final reports, transcribed (faithful summaries, lightly condensed; not byte-exact).
- `first_reviewer_probes.py` (vs v1), `second_reviewer_probes.py` (vs v2), `third_reviewer_probes.py`
  and `third_reviewer_mutate.py` (vs v3): the reviewers' own probe files, unmodified copies. They
  reference the reviewers' scratch paths and venvs; adjust paths to rerun.
- `implementer_mutants_c3.py`, `implementer_mutants_c4v1.py`, `implementer_mutants_c4v2.py`,
  `implementer_mutants_c4v3.py`: this agent's mutation harnesses behind its mutant claims (scratch paths).

## 3. Mistakes this session (so you can weigh the rest)

1. C4 v1 shipped with four blocker-level defects (F1-F4) that my own 36 tests and 15 mutants did not
   catch; claims 2 ("all failures reported") and 5 ("symlinks never followed") were false as worded.
2. v2: my summary of the first reviewer's probe failures was miscounted (4/2/2; correct 3/2/2), and
   check_output accepted hand-made output (R1).
3. v3: claims 3 ("any post-run error is a recorded refusal") and 5 ("result.json is still gone") and
   the "reported, not raised" part of R9 were overstated (G1-G4, found by review 3).
4. The ENTR-CB-1 draft first placed in the repo (7f07a0f1...) was a stale pre-correction copy and my
   04:17:22Z log entry cited its hash; I had checked the hash existed, not the content. Fixed at
   04:39:01Z with a content-verified transfer.
5. In chat I first listed a BTC/ETH funding-rate study as a next option, contrary to the operator's
   stated direction; withdrawn.
6. During the C1 check my first spreadsheet style comparison reported 151 differences; it was a tool
   artifact, caught and disproved by ZIP-level and XML comparison before reporting.

## 4. How to verify (suggested for Codex)

- Hashes: `shasum -a 256` on the paths in section 2; `shasum -a 256 -c SHA256SUMS` in the ENTR-CB-1
  folder and in `~/Documents/cryptkeep_data_archive/checkpoint_plan_draft_20261019/`.
- C4 tests in the repo's own environment (this agent could not use `.venv` from its shell):
  `PYTHONDONTWRITEBYTECODE=1 ./.venv/bin/python -m pytest -q -p no:cacheprovider tests/test_pinned_run_inputs.py`
  (expected 94 passed; tested by this agent and reviewers only on Linux Python 3.12.3/3.13.16, never macOS).
- Commit: `git show --stat 933d7ea2 | tail -1` (4,186 files); compare against
  `checkpoint_plan_draft_20261019/stage_pathspec.nul`; confirm no `.env*`, browser token files,
  `config/user.yaml`, `.cbp_state/` or `.venv*` in `git show --name-only 933d7ea2`.
- Review evidence: rerun the reviewer probe files against v3 after fixing their paths.
- ENTR-CB-1: read the draft; check its numbers against `low_value_top100_20261018/results_v2.json`.

## 5. Open items (all need operator decision; none started)

1. Codex audit of this packet, then operator decision to keep or revert the commit (revert is
   `git switch codex/research-bundle-proof`; the branch can be deleted; nothing was pushed).
2. Off-machine backup: the commit exists only on this Mac. Verified git bundle + encrypted upload not done.
3. ENTR-CB-1: freeze the draft or change it; then approve the Step A probe (at most 20 public Coinbase
   requests). Without listing data the entrant question cannot be answered.
4. C4 adoption: no runner uses the guard. Known limits G1-G9 recorded; G9 lists five protections that
   work but lack shipped tests.
5. Push of `checkpoint/2026-10-19`: only after review.

## Addendum, 2026-10-19 ~05:15 UTC (work continued; nothing above rewritten)

- New, not run on market data: `scripts/research/run_coinbase_tradable_entrants.py`
  (73f16e498d32d5c5fb08e14313d908ea83e33c14b5fd6cc6935bc98c17aea437) and
  `tests/test_coinbase_tradable_entrants.py` (6336b16f974d785cd6de397160f34a8d65682d6f4a6010a71eae3ac078bac014):
  ENTR-CB-1 runner on the unchanged v2 engine (hash-pinned), refusing to compute until the draft is
  frozen. 29 synthetic tests pass on Python 3.12.3 and 3.13.16 (agent's workspace, not the repo .venv);
  10 deliberate mutants of its rules each fail at least one test.
- ENTR-CB-1 draft updated (still DRAFT): sha256 a7fb3662450b20764f1d11404543b9551283a3c50f290ab466d3b02db86c67e9
  supersedes 6b5cb12c... in section 2 above. Changes: delisted-before-entry counts as not tradable;
  never-listed vs unknown made explicit; the two 10% denominators made explicit; section 9 names the runner.

## Addendum 2, 2026-10-19 ~08:05 UTC: ENTR-CB-1 complete, audit guide (nothing above rewritten)

Outcome: pre-registered verdict STOP. Write-up `docs/research/coinbase_tradable_entrants_20261019/RESULTS_V1.md`
(65f4d12f...); guarded result `results_v1/result.json` (d06dc758...) from plan `run_plan_v1.json` (16e47201...);
declared sensitivity `results_v1_sensitivity_xrp/` (95aba21e..., plan 4155ffd6...). Ledger supplement
`docs/research/trial_ledger_supplement_20261019_entr_cb1/`. All uncommitted on `checkpoint/2026-10-19`.

Independent reviews (verbatim, with the reviewers' scripts, each folder has SHA256SUMS):
- `map_v2_review/`: identity map v2 REJECTED (4 blockers).
- `map_v3_review/`: identity map v3 ACCEPTED_WITH_RISK.
- `results_v1_review/`: results ACCEPTED_WITH_RISK; independent recomputation matched to floating-point noise;
  asked for the cash-cycle and thin-margin disclosures now in RESULTS_V1.md.

Code (sha256 prefixes; the runner hash changed at freeze from 73f16e49... above to fdcdebe4..., when its
FROZEN_PREREG_SHA256 constant was set): run_coinbase_tradable_entrants fdcdebe4, run_coinbase_tradable_entrants_pinned
597ba0b4, probe_coinbase_listings 6833cbf3, build_coinbase_identity_map 8a9cfd72 (v2 copy in
builder_versions/), fetch_cmc_contracts 4a8c27dc, fetch_coinbase_listing_dates 049a36a4, verify_first_candles
97b8842c, build_coinbase_listings 2f5afefd, report_coinbase_tradable_entrants d0f196f6. Tests: test_coinbase_tradable_entrants
6336b16f (29), test_coinbase_listing_fetch ee59b3b5 (28), test_coinbase_tradable_entrants_pinned 22bc9ed4 (9),
test_coinbase_identity_map b6edcb48 (18), test_fetch_cmc_contracts 2113662e (5), test_verify_first_candles aab3ef80 (4):
93 passed together on Python 3.13.16 and 3.12.3 in the agent's workspace (not the repo .venv).

Saved network data (SHA256SUMS prefixes): research/coinbase_listing_probe_20261019 32063621,
..._followup a6fec3bb, research/coinbase_listing_stepB_20261019 90133ee0 (currency list), candles/ 3927b351,
candles_first_check/ df733c14, cmc_contracts/ 55e4133e.

Suggested checks for Codex:
1. `sha256sum -c SHA256SUMS` in every folder named above.
2. `pinned_run_inputs.check_output(<result dir>, expected_plan_sha256=<plan hash>)` for both result folders.
3. Run the six test files listed above.
4. Read RESULTS_V1.md "Disclosures" and the work-log entries 05:46Z-08:00Z for deviations.

Mistakes and deviations after Addendum 1 (all logged): map v2 errors found by self-check and review (JUP wrong
asset, CORE/EDGE/LIT missed, no contract check); one unsaved CoinMarketCap reachability request; 1,396 Coinbase candle
requests against roughly 1,300 approved; first listing file superseded after the binary search missed XRP's
pre-2021 trading (repaired by a first-candle check before any return was computed - CLAIMED, the files cannot prove
it); a work-log header time typed instead of taken from date -u (corrected in a later entry); a "115 match" count
that counted contract checks, not coins (114 coins; corrected).

Also after Addendum 1 (separate from ENTR-CB-1): REMAINING_TASKS.md dated update (additions only); CMC trending
log task prompt wording fix; research scout TOPICS.md standing focus; tracker v2's first scheduled run left only
state/.lock (cause UNVERIFIED; its 27 offline tests pass in the agent's workspace).
