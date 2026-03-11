from __future__ import annotations

from typing import Any, Dict, List


def _walk(before: Any, after: Any, path: str, out: Dict[str, List[dict]]) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        keys = set(before.keys()) | set(after.keys())
        for k in sorted(keys):
            nxt = f"{path}.{k}" if path else str(k)
            if k not in before:
                out["added"].append({"path": nxt, "after": after[k]})
            elif k not in after:
                out["removed"].append({"path": nxt, "before": before[k]})
            else:
                _walk(before[k], after[k], nxt, out)
        return

    if isinstance(before, list) and isinstance(after, list):
        if before != after:
            out["changed"].append({"path": path, "before": before, "after": after})
        return

    if before != after:
        out["changed"].append({"path": path, "before": before, "after": after})


def diff_configs(before: Dict[str, Any], after: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, List[dict]] = {"added": [], "removed": [], "changed": []}
    _walk(dict(before or {}), dict(after or {}), "", out)
    return {
        "ok": True,
        "added_count": len(out["added"]),
        "removed_count": len(out["removed"]),
        "changed_count": len(out["changed"]),
        **out,
    }
