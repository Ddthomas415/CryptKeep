import sys,re,subprocess,shutil,os
S=sys.argv[1]; src=open(f"{S}/cur/scripts/research/collect_companion_recreation_metadata.py").read()
G='''        if any(s[k] != LEGACY_DEFAULTS[k] for s in computed for k in LEGACY_DEFAULTS):
            raise ValueError("reconciliation_fingerprint_mismatch")
'''
P='''        computed = [{k: s[k] for k in LEGACY_SNAPSHOT_KEYS} for s in computed]
'''
assert G in src and P in src
muts={
 "M1 drop default guard": src.replace(G,""),
 "M2 filter SAVED payload instead of projecting computed": src.replace(G+P, G+'''        computed = [{k: s[k] for k in LEGACY_SNAPSHOT_KEYS} for s in computed]
        observation = {**observation, "snapshots": [{k: s.get(k) for k in LEGACY_SNAPSHOT_KEYS} for s in observation.get("snapshots") or []]}
'''),
 "M3 project v2 too (apply to all versions)": src.replace("    if version == 1:\n        # v1","    if True:\n        # v1"),
 "M4 drop 'attempt' from legacy keys": src.replace('("attempt", ','('),
 "M5 v1 uses v2 digest": src.replace("computed = reconcile(rows, fingerprint_version=version)","computed = reconcile(rows, fingerprint_version=2)"),
}
for name,m in muts.items():
    d=f"{S}/mut"; shutil.rmtree(d,ignore_errors=True); shutil.copytree(f"{S}/cur",d)
    open(f"{d}/scripts/research/collect_companion_recreation_metadata.py","w").write(m)
    r=subprocess.run([f"{S}/venv/bin/python","-m","pytest","-q","-p","no:cacheprovider","tests/test_companion_stopped_recipe.py","tests/test_collect_companion_recreation_metadata.py"],cwd=d,capture_output=True,text=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    tail=[l for l in r.stdout.splitlines() if l.startswith("FAILED") or " passed" in l or " failed" in l]
    print(f"== {name}: exit {r.returncode}"); print("\n".join(tail[-8:]))
