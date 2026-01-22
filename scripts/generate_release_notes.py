from __future__ import annotations

import argparse
import glob
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HDR_RE = re.compile(r"(?m)^\s*##\s*\[(?P<ver>\d+\.\d+\.\d+)\]\s*-\s*(?P<date>\d{4}-\d{2}-\d{2})\s*$")

@dataclass
class ChangelogSection:
    version: str
    date: str
    body: str

def load_changelog(path: Path) -> list[ChangelogSection]:
    if not path.exists():
        return []
    txt = path.read_text(encoding="utf-8", errors="replace")
    matches = list(HDR_RE.finditer(txt))
    out: list[ChangelogSection] = []
    for i, m in enumerate(matches):
        ver = m.group("ver")
        date = m.group("date")
        start = m.end()
        end = matches[i+1].start() if i+1 < len(matches) else len(txt)
        body = txt[start:end].strip()
        out.append(ChangelogSection(version=ver, date=date, body=body))
    return out

def pick_section(sections: list[ChangelogSection], version: str | None) -> ChangelogSection | None:
    if not sections:
        return None
    if version:
        for s in sections:
            if s.version == version:
                return s
    # fallback: first section in file (assumes newest on top)
    return sections[0]

def load_manifests(paths: list[Path]) -> list[dict[str, Any]]:
    out = []
    for p in paths:
        try:
            d = json.loads(p.read_text(encoding="utf-8", errors="replace"))
            if isinstance(d, dict):
                d["_path"] = str(p)
                d["_mtime"] = p.stat().st_mtime
                out.append(d)
        except Exception:
            continue
    out.sort(key=lambda x: float(x.get("_mtime", 0.0)), reverse=True)
    return out

def summarize_artifacts(manifests: list[dict[str, Any]], top_n: int = 12) -> list[dict[str, Any]]:
    # Merge artifacts across manifests by path; keep largest bytes entry (should match if same file)
    merged: dict[str, dict[str, Any]] = {}
    for m in manifests:
        arts = m.get("artifacts") or []
        if not isinstance(arts, list):
            continue
        for a in arts:
            if not isinstance(a, dict):
                continue
            path = str(a.get("path") or "")
            if not path:
                continue
            bytes_ = int(a.get("bytes") or 0)
            prev = merged.get(path)
            if (prev is None) or (bytes_ > int(prev.get("bytes") or 0)):
                merged[path] = {
                    "path": path,
                    "bytes": bytes_,
                    "sha256": str(a.get("sha256") or ""),
                }
    # sort by size desc
    rows = list(merged.values())
    rows.sort(key=lambda x: int(x.get("bytes") or 0), reverse=True)
    return rows[:top_n]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="", help="Git tag like v0.1.0 or 0.1.0")
    ap.add_argument("--changelog", default="CHANGELOG.md")
    ap.add_argument("--manifest-glob", default="releases/release_manifest_*.json")
    ap.add_argument("--out", default="releases/RELEASE_NOTES.md")
    ap.add_argument("--top-artifacts", type=int, default=12)
    args = ap.parse_args()

    repo = Path(".").resolve()
    tag = (args.tag or "").strip()
    version = tag[1:] if tag.startswith("v") else (tag if tag else None)

    sections = load_changelog(repo / args.changelog)
    sec = pick_section(sections, version)

    # manifests: accept glob (local) OR comma-separated list of paths (from CI downloads)
    mg = (args.manifest_glob or "").strip()
    manifest_paths: list[Path] = []
    if "," in mg:
        for part in mg.split(","):
            part = part.strip()
            if not part:
                continue
            manifest_paths.append((repo / part).resolve() if not os.path.isabs(part) else Path(part))
    else:
        for s in glob.glob(mg, recursive=True):
            manifest_paths.append((repo / s).resolve())

    manifests = load_manifests([p for p in manifest_paths if p.exists()])
    artifacts = summarize_artifacts(manifests, top_n=args.top_artifacts)

    # Derive meta
    chosen_ver = version or (sec.version if sec else "UNKNOWN")
    chosen_date = (sec.date if sec else "")
    title = f"Release v{chosen_ver}" if chosen_ver != "UNKNOWN" else "Release Notes"

    # Compose markdown
    lines: list[str] = []
    lines.append(f"# {title}")
    if chosen_date:
        lines.append(f"_Changelog date: {chosen_date}_")
    lines.append("")
    if sec and sec.body:
        lines.append("## Changes")
        lines.append(sec.body.strip())
        lines.append("")
    else:
        lines.append("## Changes")
        lines.append("- (No changelog section found.)")
        lines.append("")

    lines.append("## Build Manifest Summary")
    if manifests:
        lines.append(f"- Manifests found: **{len(manifests)}**")
        lines.append(f"- Latest manifest: `{Path(manifests[0].get('_path','')).name}`")
        lines.append("")
    else:
        lines.append("- No manifests found.")
        lines.append("")

    if artifacts:
        lines.append("### Top Artifacts (by size)")
        lines.append("")
        lines.append("| Artifact | Bytes | SHA-256 |")
        lines.append("|---|---:|---|")
        for a in artifacts:
            sha = a.get("sha256") or ""
            lines.append(f"| `{a.get('path','')}` | {int(a.get('bytes') or 0)} | `{sha}` |")
        lines.append("")
        lines.append("Note: SHA-256 values are for the exact distributables produced in this run.")
        lines.append("")

    out_path = (repo / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    print({"ok": True, "out": str(out_path), "version": chosen_ver, "manifests_n": len(manifests), "artifacts_n": len(artifacts)})

if __name__ == "__main__":
    main()
