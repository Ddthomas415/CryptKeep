import sys,subprocess,shutil,os
S=sys.argv[1]; F="scripts/research/pinned_run_inputs.py"; src=open(f"{S}/c4/{F}").read()
M={
"skip post-run recheck": ("    after = verify(plan)\n", "    after = receipt\n"),
"receipt written after compute": ("    receipt_sha256 = _write_new(out / \"pin_receipt.json\", receipt)\n    result = compute(plan)\n",
                                  "    result = compute(plan)\n    receipt_sha256 = _write_new(out / \"pin_receipt.json\", receipt)\n"),
"no O_NOFOLLOW": ('os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)', "os.O_RDONLY"),
"no parent symlink check": ("    current = root\n    for part in rel.parts[:-1]:", "    current = root\n    return\n    for part in rel.parts[:-1]:"),
"no unlisted-file check": ("    for name in sorted(present - set(listed)):", "    for name in []:"),
"no dir symlink walk check": ('                failures.append("symlink_refused:" + full.relative_to(root).as_posix())', "                pass"),
"runtime not checked": ("    observed = {}\n    if \"python\" in spec:", "    return {}\n    observed = {}\n    if \"python\" in spec:"),
"model files not checked": ("            for rel, expected in sorted(model[\"files\"].items()):\n                _check(", "            for rel, expected in []:\n                _check("),
"plan hash not checked": ('    if actual != _hex(plan_sha256, _HEX64, "plan_sha256"):', "    if False:"),
"prereg not checked": ('    _check(root, prereg["path"], prereg["sha256"], seen, failures)\n', ""),
"unknown keys allowed": ("    if set(plan) - PLAN_KEYS:", "    if False:"),
"dotdot allowed": ('any(part in ("", ".", "..")', 'any(part in ("", ".")'),
"NaN results allowed": ("allow_nan=False", "allow_nan=True"),
"report first failure only": ("    if failures:\n        raise PinError(failures)", "    if failures:\n        raise PinError(failures[:1])"),
"sums self-entry tolerated": ("    present.discard(sums_inside)\n", "    present.discard(sums_inside)\n    listed.pop(sums_inside, None)\n"),
}
for name,(a,b) in M.items():
    assert src.count(a)==1,(name,src.count(a))
    d=f"{S}/m4"; shutil.rmtree(d,ignore_errors=True); shutil.copytree(f"{S}/c4",d)
    open(f"{d}/{F}","w").write(src.replace(a,b))
    r=subprocess.run([f"{S}/venv312/bin/python","-m","pytest","-q","-p","no:cacheprovider","tests/test_pinned_run_inputs.py"],cwd=d,capture_output=True,text=True,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
    last=[l for l in r.stdout.splitlines() if " passed" in l or " failed" in l][-1:]
    print(f"{'CAUGHT ' if r.returncode else 'SURVIVED'} {name}: {last}")
