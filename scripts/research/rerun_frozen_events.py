"""Run frozen event signals with corrected execution in a separate artifact.

Requires the original cloud input root (cb/h1, cb2/h1, bv). Never downloads a
replacement dataset. Historical results remain unchanged, no fresh-holdout claim.
"""

import argparse
import ast
import contextlib
import hashlib
import io
import json
from pathlib import Path
import sys

from scripts.research.corrected_research_math import corrected_event_exit, corrected_forward

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "docs/research/blast_vara_20261009/events.py"


class Corrections(ast.NodeTransformer):
    def __init__(self, fee):
        self.fee = fee

    def visit_FunctionDef(self, node):
        if node.name in ("simulate_exit", "fwd"):
            replacement = "corrected_event_exit" if node.name == "simulate_exit" else "corrected_forward"
            return ast.Assign(targets=[ast.Name(id=node.name, ctx=ast.Store())],
                              value=ast.Name(id=replacement, ctx=ast.Load()))
        if node.name == "run_events":
            return self.generic_visit(node)
        return node

    def visit_Assign(self, node):
        if any(isinstance(t, ast.Name) and t.id == "FEE" for t in node.targets):
            node.value = ast.Constant(self.fee)
        if any(isinstance(t, ast.Name) and t.id == "g" for t in node.targets):
            if isinstance(node.value, ast.Subscript) and isinstance(node.value.value, ast.Call):
                call = node.value.value
                if isinstance(call.func, ast.Name) and call.func.id == "simulate_exit":
                    node.value = ast.Call(func=ast.Name(id="event_return", ctx=ast.Load()),
                                          args=call.args, keywords=call.keywords)
            return [node, ast.If(test=ast.Compare(left=ast.Name(id="g", ctx=ast.Load()),
                                                ops=[ast.Is()], comparators=[ast.Constant(None)]),
                                 body=[ast.Continue()], orelse=[])]
        return node


def event_return(*args):
    result = corrected_event_exit(*args)
    return None if result is None else result[0]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-root", type=Path, required=True)
    parser.add_argument("--fee-bps", type=float, choices=(50, 60, 120), default=50)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    files = []
    for folder in ("cb/h1", "cb2/h1", "bv"):
        entries = sorted((args.input_root / folder).glob("*.json"))
        if not entries:
            raise ValueError(f"original input archive missing: {folder}; no replacement downloaded")
        files.extend(entries)
    hashes = {str(p.relative_to(args.input_root)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    tree = ast.fix_missing_locations(Corrections(args.fee_bps / 10000).visit(ast.parse(SOURCE.read_text())))
    namespace = {"__file__": str(SOURCE), "corrected_event_exit": corrected_event_exit,
                 "corrected_forward": corrected_forward, "event_return": event_return}
    previous = sys.argv
    try:
        sys.argv = [str(SOURCE), str(args.input_root)]
        with contextlib.redirect_stdout(io.StringIO()):
            exec(compile(tree, str(SOURCE), "exec"), namespace)
    finally:
        sys.argv = previous
    output = {"artifact_type": "corrected_frozen_event_diagnostic_v1", "not_promotion_evidence": True,
              "fee_bps": args.fee_bps, "input_sha256": hashes,
              "original_script_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "correction_script": Path(__file__).read_text(),
              "correction_math": (ROOT / "scripts/research/corrected_research_math.py").read_text(),
              "original_script": SOURCE.read_text(),
              "execution": "next open; stops gap-aware; incomplete/gapped paths excluded, not liquidated at last known close",
              "result": namespace["out"]}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("x") as stream:
        json.dump(output, stream, allow_nan=False)
    print(json.dumps({"file": str(args.out), "not_promotion_evidence": True}))


if __name__ == "__main__":
    main()
