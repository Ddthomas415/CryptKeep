import sys,subprocess,shutil,os
S=sys.argv[1]; F="scripts/research/pinned_run_inputs.py"; src=open(f"{S}/c4v3/{F}").read()
M={
"R1 no receipt structure check": ("    problems = _receipt_problems(receipt)\n    if problems:\n        raise PinError(problems)\n", ""),
"R1 link plan hash not compared": ('            or link["plan_sha256"] != receipt["plan_sha256"]):', '            ):'),
"R1 expected plan ignored": ('    if expected_plan_sha256 is not None and receipt["plan_sha256"] != expected_plan_sha256:', '    if False:'),
"R2 receipt bytes not rechecked": ('    if _read_at(out_fd, RECEIPT_NAME) != receipt_bytes:', '    if False:'),
"R2 out dir identity not rechecked": ('        if not stat.S_ISDIR(st.st_mode) or _ident(st) != out_id:', '        if False:'),
"R3 post-run errors not caught": ("        except Exception as error:\n            failures, data, payload = [\"post_run_check_error:\"", "        except ZeroDivisionError as error:\n            failures, data, payload = [\"post_run_check_error:\""),
"R3 encode errors not caught": ("        except Exception:  # NaN", "        except ValueError:  # NaN"),
"R4 paths not absolutised": ("    out = Path(os.path.abspath(out_dir))", "    out = Path(out_dir)"),
"R5 compute result not set aside": ("        for name in (RESULT_NAME, REFUSED_NAME):", "        for name in ():"),
"R7 no identity check of out ancestors": ("        if ident in identities:", "        if False:"),
"R8 parent opened following symlinks": ("_DIR_FLAGS = os.O_RDONLY | getattr(os, \"O_DIRECTORY\", 0) | _NOFOLLOW", "_DIR_FLAGS = os.O_RDONLY | getattr(os, \"O_DIRECTORY\", 0)"),
"R9 NUL root not checked": ("    if not _text_ok(value):\n        failures.append(\"bad_root\")", "    if False:\n        failures.append(\"bad_root\")"),
"R9 RecursionError in plan not caught": ("    except (ValueError, RecursionError):", "    except ValueError:"),
"R10 created parents not fsynced": ("    for created in reversed(missing):\n        _fsync_path(created.parent)\n", ""),
"R11 no NFC normalisation": ('    return unicodedata.normalize("NFC", name).casefold()', '    return name.casefold()'),
"file inode not compared after open": ("        if not stat.S_ISREG(opened.st_mode) or _ident(opened) != _ident(before):", "        if not stat.S_ISREG(opened.st_mode):"),
"walk identity not compared": ("                if _ident(os.fstat(child)) != _ident(st):\n                    failures.append(\"replaced_while_opening:\" + shown)\n                else:\n                    _walk(", "                if False:\n                    pass\n                else:\n                    _walk("),
"unreadable dir not reported": ('        failures.append("unreadable_directory:" + here)\n        return\n', '        return\n'),
}
for name,(a,b) in M.items():
    assert src.count(a)==1,(name,src.count(a))
    d=f"{S}/m6"; shutil.rmtree(d,ignore_errors=True); shutil.copytree(f"{S}/c4v3",d,ignore=shutil.ignore_patterns("bt_*"))
    open(f"{d}/{F}","w").write(src.replace(a,b))
    try:
        r=subprocess.run([f"{S}/venv312/bin/python","-m","pytest","-q","-p","no:cacheprovider","tests/test_pinned_run_inputs.py",f"--basetemp={S}/m6_bt"],cwd=d,capture_output=True,text=True,timeout=120,env={**os.environ,"PYTHONDONTWRITEBYTECODE":"1"})
        last=[l for l in r.stdout.splitlines() if " passed" in l or " failed" in l][-1:]
        print(f"{'CAUGHT ' if r.returncode else 'SURVIVED'} {name}: {last}")
    except subprocess.TimeoutExpired:
        print(f"CAUGHT  {name}: hung")
