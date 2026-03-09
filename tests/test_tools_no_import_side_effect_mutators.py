from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS_DIR = ROOT / "tools"
MUTATOR_METHODS = {"mkdir", "write_text", "write_bytes", "unlink", "rename", "replace", "rmdir", "touch"}


def _module_scope_value_nodes(tree: ast.Module):
    for node in tree.body:
        if isinstance(node, ast.Expr):
            yield node.lineno, node.value
        elif isinstance(node, ast.Assign):
            yield node.lineno, node.value
        elif isinstance(node, ast.AnnAssign):
            yield node.lineno, node.value
        elif isinstance(node, ast.AugAssign):
            yield node.lineno, node.value


def test_tools_do_not_call_file_mutators_at_import_time():
    offenders: list[str] = []
    for path in sorted(TOOLS_DIR.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        for lineno, value in _module_scope_value_nodes(tree):
            if not isinstance(value, ast.Call):
                continue
            func = value.func
            if isinstance(func, ast.Attribute) and func.attr in MUTATOR_METHODS:
                offenders.append(f"{path.relative_to(ROOT)}:{lineno} -> .{func.attr}()")
    assert not offenders, "Import-time file mutation calls detected in tools:\n" + "\n".join(offenders)
