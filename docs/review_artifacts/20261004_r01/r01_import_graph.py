"""Static import graph of the repo at the checked-out revision. Read-only."""
import ast, json, os, re, subprocess, sys, collections
ROOT = "."
files = subprocess.run(["git", "ls-files", "*.py"], capture_output=True, text=True).stdout.split()
files = [f for f in files if not f.startswith(("attic/", "dist/", "build/"))]
def modname(path):
    p = path[:-3]
    if p.endswith("/__init__"): p = p[:-9]
    return p.replace("/", ".")
mods = {modname(f): f for f in files}
graph = collections.defaultdict(set); has_main = set(); errors = []
for f in files:
    try:
        tree = ast.parse(open(f, encoding="utf-8", errors="replace").read())
    except Exception as e:
        errors.append((f, str(e)[:60])); continue
    me = modname(f); pkg = me if f.endswith("__init__.py") else me.rpartition(".")[0]
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                parts = pkg.split(".") if pkg else []
                parts = parts[: len(parts) - (node.level - 1)] if node.level > 1 else parts
                base = ".".join([p for p in parts if p] + ([base] if base else []))
            names = [base] + [f"{base}.{a.name}" for a in node.names]
        elif isinstance(node, ast.If):
            t = node.test
            if isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "__name__": has_main.add(me)
        for n in names:
            while n:
                if n in mods and n != me:
                    graph[me].add(n); break
                n = n.rpartition(".")[0]
    # dynamic imports by string
    src = open(f, encoding="utf-8", errors="replace").read()
    for m in re.findall(r"import_module\(\s*[\"']([\w\.]+)[\"']", src):
        if m in mods: graph[me].add(m)
json.dump({"mods": mods, "graph": {k: sorted(v) for k, v in graph.items()}, "has_main": sorted(has_main), "errors": errors},
          open("/home/claude/work/scratch/r01/graph.json", "w"))
print(len(files), "files", len(mods), "modules", sum(len(v) for v in graph.values()), "edges", len(has_main), "with __main__", len(errors), "parse errors")
