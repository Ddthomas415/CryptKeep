# Reviewed-patch inventory: the October review series against the current code (2026-10-31)

Bot relation: audit of the bot's own code (not a strategy result).
Research item 8 in `docs/PROJECT_STATE.md` (owner: "ok", 2026-10-31). Claude, read-only. **Self-checked; Codex to verify.**
Searches for earlier work: `docs/research/*_review_2026100*.md` (58 documents name patches 0001-0076),
`docs/review_artifacts/20261004_rev32_bundle/` (review bundles rev32-rev87 and the series on master be34a18a, rev88),
`series_rebase_check_on_master_be34a18a_20261007.md`, the work log (2026-10-02 "Rev10 series and multi-symbol review").

## What the series is (SHOWN from the bundle's README and PATCH_MAP.csv)
- 72 patches written and reviewed in early October 2026 (Claude, with Codex reviewing parts), last reissued on GitHub
  master `be34a18a` as branch `claude/series-rev34` (rev88, 2026-10-07): full suite at its head 4,989 passed, 0 failed.
- Its README: "Nothing here has been pushed, merged, deployed or applied to your checkout. Every patch is
  READY_FOR_INDEPENDENT_REVIEW by my statement only." 0058 withdrawn (superseded by PR 605); 0059 replaced by 0076; 0011
  HELD; 0019 not applied.
- The patch files, a git bundle of the branch and the patch map are in the repository:
  `docs/review_artifacts/20261004_rev32_bundle/cryptkeep_series_on_be34a18a_rev88.zip` (sha256 b8b49bee...). Nothing
  is lost.

## Result (SHOWN by running `check_patch_presence.py` against HEAD 052ed75e6)
**None of the 72 patches is in the laptop's code.** 69 have under 20% of their new code lines present (two have 5% and
15%; the rest 0%); 3 change tests only. Details per patch, with the review status recorded at the time, in
`inventory.csv`. Patches that bear on today's work:

| Patch | What it does | Review status then | Today's work it affects |
|---|---|---|---|
| 0001, 0002 | Kill cooldown expires across restarts; closing sells pass the cooldown | ACCEPTED_WITH_RISK (combined review) | Simulation R1; bot audit BA-16 |
| 0004 | Strategy runner acts on every configured symbol | "current form needs final review" | **Engineering item 1, the multi-coin fix: a fix already exists** (D-1) |
| 0016-0018 | Entries refused while an intent is in flight; exit bookkeeping order | ACCEPTED_WITH_RISK / INCOMPLETE | BA-05, BA-18 |
| 0031 | Two starters cannot both reclaim a stale runner lock | ready for review | BA-20 |
| 0037, 0071, 0072 | Live consumers refuse intents with no price, record boundary refusals and adapter failures correctly | ready for review | Live path (LP) |
| 0055 | Order gate refuses non-spot markets | ready for review | Live path |
| 0062 | Kill-switch command records its changes | ready for review | LP-08 |
| 0069 | A failed live enable really restores the config | ready for review | LP-08, LP-09 |
| 0070 | Order gate refuses buys on a symbol under a loss lock | ready for review | Live path |
| 0073-0075 | Reconciler: failed lookup is not "not found"; checks every tracked intent | ready for review | LP-06 |
| 0076 | Loss lock counts across round trips; a failed daily-loss write is a failure | ready for review, HIGH risk | Live path |

## GitHub master (added 2026-10-31 after the owner's `git fetch origin`; SHOWN)
- GitHub master is `be34a18a3` (2026-10-07, PR #606), unchanged since; two new remote branches are the sources of PRs
  #605 and #606. **None of the series is on GitHub master either** (`inventory_github_master.csv`: 69 not in code,
  3 tests-only).
- The series' git bundle verifies against GitHub master (`git bundle verify`: okay; head `5b4ebb29`, branch
  `claude/series-rev34`), so the branch can be recreated exactly on top of today's master for review.
- The laptop branch forked from master at `adde462ff` (PR #598, 2026-09-23), not at `97c24c8e4`. Master has five PRs
  since: #600, #601, #603, #605, #606. By the same new-lines check, the laptop's code contains all new code lines of
  #601 (15/15), #603 (1/1) and #605 (171/171), and none of #600 (archive research eligibility, 0/143) or #606
  (workflow signing gates 0/24, desktop build paths 0/8). The laptop's work must be reconciled with master before any
  merge. The commit review of 2026-10-31 said the laptop was "4 commits ahead"; it was also behind (O-19).

## What this does not show
- Whether a defect was fixed in another way: the check looks for each patch's own lines.
- Whether the patches still apply or pass on today's code (the series was rebased on `be34a18a`, not on the laptop's
  base).

## Method
`check_patch_presence.py` (read-only): for each patch, the code lines it adds (at least 20 characters, not comments,
outside `docs/` and `tests/`) that were not in the base `97c24c8e4`; then the share present in the same file at the
target commit. Run: `python3 -I check_patch_presence.py <repo> <commit> <out.csv>`; 84 seconds on the device.

## Proposed next steps (owner decides)
1. Done 2026-10-31: GitHub master checked (above). Next, with the owner's approval: recreate `claude/series-rev34` from
   the bundle and push it to GitHub as a review branch (no merge), so Codex and reviewers work from it.
2. Codex starts engineering item 1 and simulation R1 from patches 0004 and 0001/0002 (review, rebase, test) instead of
   writing new fixes.
3. The owner decides for the rest, in risk order (live path first), apply after independent review, or drop.
