#!/usr/bin/env python3
"""Which patches of the October review series (rev88) are in a given commit? Read-only.

For each patch: the code lines it adds (at least 20 characters, not comments, outside docs/ and tests/) that were not
already in the base commit 97c24c8e4; then the share of those lines present, after stripping whitespace, in the same
file at the target commit. 80% or more: in code; 20-79%: partly; under 20%: not in code. A fix written differently
would show as not in code, so the verdict means "this patch's code is not there", not "the defect is unfixed".
Usage: python3 -I check_patch_presence.py <repo> <target commit> <out.csv>"""
import csv, io, os, re, subprocess, sys, zipfile

REPO, TARGET, OUT = sys.argv[1:4]
BASE = "97c24c8e4"
BUNDLES = os.path.join(REPO, "docs/review_artifacts/20261004_rev32_bundle")
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0")


def show(commit, path):
    r = subprocess.run(["git", "-C", REPO, "show", f"{commit}:{path}"], capture_output=True, text=True, env=ENV)
    return set(l.strip() for l in r.stdout.splitlines()) if r.returncode == 0 else None


z88 = zipfile.ZipFile(os.path.join(BUNDLES, "cryptkeep_series_on_be34a18a_rev88.zip"))
root = "cryptkeep_series_on_be34a18a_rev88/"
pmap = {r["patch"]: r for r in csv.DictReader(io.TextIOWrapper(z88.open(root + "PATCH_MAP.csv"), encoding="utf-8"))}
z87 = zipfile.ZipFile(os.path.join(BUNDLES, "cryptkeep_review_bundle_2026-10-02_rev87.zip"))
status = {}
for line in io.TextIOWrapper(z87.open("cryptkeep_review_bundle_2026-10-02/REVIEW_HANDOFF.md"), encoding="utf-8"):
    m = re.match(r"^\| (00\d\d) \| ([^|]+)\| ([^|]+)\|", line)
    if m and m.group(1) not in status:
        status[m.group(1)] = m.group(3).strip()
status.update({
    "0001": "Combined review with 0002 ACCEPTED_WITH_RISK (cooldown_exit_quantity_treatment_20261007.md); deployment not authorised",
    "0002": "Combined review with 0001 ACCEPTED_WITH_RISK (cooldown_exit_quantity_treatment_20261007.md); deployment not authorised",
    "0076": "Replaces 0059; READY_FOR_INDEPENDENT_REVIEW (Claude), HIGH risk (series_rebase_check_on_master_be34a18a_20261007.md)",
})
DEFAULT = "READY_FOR_INDEPENDENT_REVIEW by Claude's statement only (rev88 README); see docs/research/*_review_2026100*.md"
base_c, tgt_c, rows = {}, {}, []
for name in sorted(n for n in z88.namelist() if n.startswith(root + "patches/") and n.endswith(".patch")):
    patch = os.path.basename(name).split("-")[0]
    cur, new = None, {}
    for line in io.TextIOWrapper(z88.open(name), encoding="utf-8", errors="replace"):
        if line.startswith("+++ b/"):
            cur = line[6:].strip()
            continue
        if line.startswith("+++ "):
            cur = None
            continue
        if cur and line.startswith("+") and not cur.startswith(("docs/", "tests/")) and not cur.endswith(".md"):
            t = line[1:].strip()
            if len(t) >= 20 and not t.startswith("#"):
                b = base_c.setdefault(cur, show(BASE, cur) or set())
                if t not in b:
                    new.setdefault(cur, set()).add(t)
    total = sum(len(v) for v in new.values())
    found = 0
    for path, lines in new.items():
        h = tgt_c.setdefault(path, show(TARGET, path) or set())
        found += sum(1 for l in lines if l in h)
    pct = round(100 * found / total) if total else None
    verdict = "no new code lines" if not total else "in code" if pct >= 80 else "partly" if pct >= 20 else "not in code"
    rows.append({"patch": patch, "subject": pmap.get(patch, {}).get("subject", ""),
                 "review_status": status.get(patch, DEFAULT), "rev88_note": pmap.get(patch, {}).get("status", ""),
                 "new_code_lines": total, "found_in_target": found, "pct": pct, "verdict": verdict,
                 "files": ";".join(sorted(new))})
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
from collections import Counter
print(TARGET, dict(Counter(r["verdict"] for r in rows)))
