from __future__ import annotations

import argparse
import ast
from pathlib import Path
import re

# CBP_BOOTSTRAP_SYS_PATH
try:
    from _bootstrap import add_repo_root_to_syspath
except ModuleNotFoundError:
    from scripts._bootstrap import add_repo_root_to_syspath

add_repo_root_to_syspath(Path(__file__).resolve().parent)

PATTERNS = (
    re.compile(r"\.create_order\s*\("),
    re.compile(r"\.createOrder\s*\("),
    re.compile(r"getattr\s*\([^\n]*[\"']create_order[\"']"),
    re.compile(r"getattr\s*\([^\n]*[\"']createOrder[\"']"),
)

ALLOWED = {
    "services/execution/place_order.py",
}

SKIP_DIRS = {"tools", "attic", ".venv", "venv", "__pycache__", ".git", "data", "docs", "dist", "build", ".pytest_cache"}

def iter_py_files(root: Path):
    for p in root.rglob("*.py"):
        parts = set(p.parts)
        if any(part.startswith(".venv") for part in p.parts):
            continue
        if any(s in parts for s in SKIP_DIRS):
            continue
        yield p

FORBIDDEN_ORDER_NAMES = {"create_order", "createOrder"}


def _literal_string_value(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _literal_string_value(node.left)
        right = _literal_string_value(node.right)
        if left is not None and right is not None:
            return left + right
    return None


def _constant_string_assignments(tree: ast.AST) -> dict[str, str]:
    values: dict[str, str] = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        value = _literal_string_value(node.value)
        if value is None:
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                values[target.id] = value
    return values


def _getattr_name(node: ast.AST, constants: dict[str, str]) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id)
    if isinstance(node, ast.BinOp):
        return _literal_string_value(node)
    return None


def _ast_getattr_hits(txt: str) -> list[tuple[int, str]]:
    try:
        tree = ast.parse(txt)
    except SyntaxError:
        return []
    constants = _constant_string_assignments(tree)
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not (isinstance(func, ast.Name) and func.id == "getattr"):
            continue
        if len(node.args) < 2:
            continue
        name = _getattr_name(node.args[1], constants)
        if name in FORBIDDEN_ORDER_NAMES:
            hits.append((node.lineno, f"getattr(..., {name!r})"))
    return hits


def scan(root: Path) -> list[dict]:
    hits = []
    for p in iter_py_files(root):
        rel = p.relative_to(root).as_posix()
        if rel in ALLOWED:
            continue
        txt = p.read_text(encoding="utf-8", errors="replace")
        # look for direct exchange order placement patterns
        # We explicitly block direct create_order usage anywhere outside place_order.py.
        for i, line in enumerate(txt.splitlines(), start=1):
            if any(pattern.search(line) for pattern in PATTERNS):
                hits.append({"file": rel, "line": i, "text": line.strip()[:240]})
        for line_no, text in _ast_getattr_hits(txt):
            hits.append({"file": rel, "line": line_no, "text": text})
    return hits

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root")
    ap.add_argument("--print", action="store_true", help="print full hits")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    hits = scan(root)
    if not hits:
        print({"ok": True, "violations": 0})
        raise SystemExit(0)

    out = {"ok": False, "violations": len(hits), "hits": hits}
    if args.print:
        print(out)
    else:
        # compact output
        print({"ok": False, "violations": len(hits), "sample": hits[:10]})
    raise SystemExit(2)

if __name__ == "__main__":
    main()
