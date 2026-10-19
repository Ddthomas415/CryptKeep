# Recovery preflight correction

Date2026-10-18. ENGINEER stage, bounded correction of RC-01 and RC-02.
The first preflight was REJECTED before any actual copy. Its review and plan
remain unchanged as historical evidence. No ignored credential exposure was
observed; the findings were demonstrated with synthetic data only.

RC-01: ignored companion additions now use an explicit finite public-file
allowlist (34 Python files plus named public docs/build descriptions/originals).
The four research archive database paths are explicit, not a basename glob.
Nonallowlisted companion paths and a fifth research database are filtered out;
the same boundary is checked before reads if supplied directly to build().
Known credentials names also remain denied before opening. Ordinary Git-known
public files remain subject to the path/content exclusions and heuristic limits.

RC-02: ZIP/TAR container detection now uses content independently of the outer
suffix. Renamed TAR fixtures carrying .env are rejected as archives, while
safe text and a safe mislabeled archive pass. Unrecognized NUL-bearing text is
not treated as cleared plaintext. Existing recursive size/member/link limits
remain unchanged. CSV is written before the final success manifest.

VERIFIED_ENV same isolated synthetic command as the original plan:29passed0.38s,
exit0. New regressions include inventory positive/negative controls, a read spy
for rejected additions, renamed TARs under three suffixes, and safe controls.
Financial/research experiments, Git writes, credentials and actual copy remain
untouched. Existing screening is heuristic, not universal clearance.

Current corrected source/test hashes are recorded in the separate re-review
artifact. The single output remains the new private external directory named in
the original plan. No actual copy may run until corrected hashes clear separate
review. Implementation READY_FOR_INDEPENDENT_REVIEW; no extra framework or
operational scope added.
