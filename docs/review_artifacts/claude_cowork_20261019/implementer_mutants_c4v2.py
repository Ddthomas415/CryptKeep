import sys,subprocess,shutil,os
S=sys.argv[1]; F="scripts/research/pinned_run_inputs.py"; src=open(f"{S}/c4v2/{F}").read()
M={
"F1 no deepcopy for compute": ("compute(copy.deepcopy(plan))","compute(plan)"),
"F2 no output-dir listing check": ("    if extra:\n        failures.append(\"unexpected_output_files:\"","    if False:\n        failures.append(\"unexpected_output_files:\""),
"F3 no canonical-root check": ("    if os.path.realpath(value) != str(Path(value)):","    if False:"),
"F4 no walk onerror": ("os.walk(top, onerror=walk_error, followlinks=False)","os.walk(top, followlinks=False)"),
"F5 no pre-open regular-file check": ("    if not stat.S_ISREG(before.st_mode):\n        raise PinError([\"not_a_regular_file:\" + name])\n",""),
"F6 stop at first structural failure": ("    if failures:\n        raise PinError(failures)\n    return {","    if failures:\n        raise PinError(failures[:1])\n    return {"),
"F6 no set_members_not_checked": ('        failures.append("set_members_not_checked:" + label)\n',""),
"F7 no plan re-hash": ('            failures.append("plan_changed_during_run")','            pass'),
"F8 duplicate keys allowed": ("object_pairs_hook=_unique_pairs","object_pairs_hook=dict"),
"F9 empty runtime allowed": ('    if "python" not in spec and not packages:','    if False:'),
"F9 model null allowed": ('    if "model" in plan:\n        candidate','    if plan.get("model") is not None:\n        candidate'),
"F10 no out-dir-in-set check": ("    _refuse_out_inside_sets(plan, out)\n",""),
"F11 empty dirs allowed": ("                if member not in allowed_dirs:","                if False:"),
"F14 case duplicates allowed": ("        if name.casefold() in folded:","        if False:"),
"refusal record not written": ("    if failures:\n        _write_refusal(out, failures)","    if failures:\n        pass"),
"check_output ignores link": ("            or link.get(\"receipt_sha256\") != hashlib.sha256(blobs[RECEIPT_NAME]).hexdigest()\n",""),
}
for name,(a,b) in M.items():
    assert src.count(a)==1,(name,src.count(a))
    d=f"{S}/m5"; shutil.rmtree(d,ignore_errors=True); shutil.copytree(f"{S}/c4v2",d)
    open(f"{d}/{F}","w").write(src.replace(a,b))
    try:
        r=subprocess.run([f"{S}/venv312/bin/python","-m","pytest","-q","-p","no:cacheprovider","tests/test_pinned_run_inputs.py"],cwd=d,capture_output=True,text=True,timeout=60,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        last=[l for l in r.stdout.splitlines() if " passed" in l or " failed" in l][-1:]
        print(f"{'CAUGHT ' if r.returncode else 'SURVIVED'} {name}: {last}")
    except subprocess.TimeoutExpired:
        print(f"CAUGHT  {name}: test run hung (timeout 60s) -> FIFO opened")
