# Approved corrections C8 (survey: 2024-26 is not an untouched holdout) and C9 (E6 README pointer). 2026-10-15.
# Each old string must occur exactly once; pre-edit copies are in originals/*.pre_C8 / *.pre_C9.
import hashlib, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[1]
E = {
 "crypto_trading_edges_survey_20261013.md": [
  ("with trial counting and an untouched post-ETF holdout.",
   "with trial counting. The post-ETF years 2024–26 were already used during candidate selection, so they are not a clean out-of-sample test; only data after the rule froze is (C8 correction, 2026-10-15)."),
  ("The post-ETF period from January 2024 to the present should be a final holdout opened once:",
   "The post-ETF period from January 2024 to the present is the regime that matters most, but it was already used during candidate selection, so it is not a clean out-of-sample test (C8 correction):"),
  ("on the untouched 2024–2026 holdout,",
   "on 2024–2026 (already used during candidate selection, so not a clean out-of-sample test; clean evidence requires data after the rule froze — C8 correction),"),
 ],
 "xs_momentum_20261012/README.md": [
  ("- **Status reminder:** the stored result still contains the known stale-price defect described above. It remains labelled DEFECTIVE until a corrected simulation is run.",
   "- **Status reminder:** the stored result still contains the known stale-price defect described above. It remains the registered (defective) record.\n- **Corrected retrospective analysis (C9 pointer, 2026-10-15):** a corrected-execution rerun, using a rule written down before it was run (`../integrity_audit_20261015/E6_CORRECTED_RULE_prestated.md`), is archived in `../integrity_audit_20261015/` (`blind/e6_blind_real_result.json`, cross-check in `corrected_crosscheck/`). Two implementations give period A strategy $1,009–$1,011 (vs about $1,120 in the registered run) and FAIL on all four checks. This is a RETROSPECTIVE analysis done after the results were seen. It does NOT replace the registered result or verdict above."),
 ],
}
dry = "--apply" not in sys.argv
for path, pairs in E.items():
    p = R / path; t = p.read_text(); before = hashlib.sha256(t.encode()).hexdigest()
    for old, new in pairs:
        n = t.count(old)
        if n != 1: sys.exit(f"ABORT {path}: {n} occurrences of {old[:50]!r}")
        t = t.replace(old, new)
    print(("DRY " if dry else "APPLY ") + path, before, "->", hashlib.sha256(t.encode()).hexdigest())
    if not dry: p.write_text(t)
