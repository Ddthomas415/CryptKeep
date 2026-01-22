from pathlib import Path
import datetime

def read(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace")

def append_checkpoint(title: str, body: str):
    ck = Path("CHECKPOINTS.md")
    if not ck.exists():
        return
    t = read(ck)
    if title in t:
        return
    ck.write_text(t.rstrip() + "\n\n" + (title + "\n" + body).lstrip("\n"), encoding="utf-8")

# -------------------------
# Phase 21
append_checkpoint(
"## Phase 21) CI Signing + Notarization",
"""
- ✅ Update publish_release workflow to sign/notarize only when env vars from secrets are present
- ✅ Docs added (docs/PHASE21_CI_SIGNING.md)
- ⏳ Next: sign Windows installer too (Inno SignTool integration) + UI “Release Train” checklist page
""".lstrip("\n")
)
print("OK: Phase 21 applied (CI signing + CI notarization, gated).")

# Phase 22
append_checkpoint(
"## Phase 22) Installer Signing + Release Train",
"""
- ✅ Add Release Train report helper (services/release/release_train.py)
- ✅ Add Release Train panel in dashboard (checklist + run validate button)
- ✅ Docs added (docs/PHASE22_INSTALLER_SIGNING_AND_RELEASE_TRAIN.md)
- ⏳ Next: CI signing of installer artifact + UI buttons to run packaging builds per-OS (local only)
""".lstrip("\n")
)
print("OK: Phase 22 applied (installer signing + Release Train panel).")

# Phase 23
append_checkpoint(
"## Phase 23) CI Installer Artifacts",
"""
- ✅ Add Release Train UI buttons for local packaging builds
- ✅ Docs added (docs/PHASE23_CI_INSTALLER_ARTIFACTS.md)
- ⏳ Next: “Ops intelligence” learning/adaptability module path (market data ingestion → feature store → model training → safe deployment gates)
""".lstrip("\n")
)
print("OK: Phase 23 applied (CI installer artifacts + Release Train local build buttons).")

# Phase 24
append_checkpoint(
"## Phase 24) Learning Core v1",
"""
- ✅ Docs added (docs/PHASE24_LEARNING_CORE.md, docs/SOCIAL_LEARNING.md)
- ⏳ Next: wire ML into decision flow (paper mode first), add monitoring + rollback triggers, integrate imported trader signals as features
""".lstrip("\n")
)
print("OK: Phase 24 applied (learning core v1).")

# Update handoff timestamp
handoff = Path("docs/CHAT_HANDOFF.md")
if handoff.exists():
    lines = read(handoff).splitlines()
    if len(lines) >= 2 and lines[1].startswith("Updated:"):
        lines[1] = f"Updated: {datetime.datetime.now(datetime.timezone.utc).isoformat()}"
        handoff.write_text("\n".join(lines) + "\n", encoding="utf-8")

