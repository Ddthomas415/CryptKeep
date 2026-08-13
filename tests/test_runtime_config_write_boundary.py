from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_runtime_user_yaml_writes_stay_behind_config_editor() -> None:
    """Runtime user.yaml mutation must stay behind services.admin.config_editor.

    The central helper owns metadata-only runtime_config_save audit events and
    rollback-on-audit-write-failure behavior. A new source file that writes the
    same runtime config file directly would bypass that contract.
    """

    scanned_roots = [ROOT / "dashboard", ROOT / "scripts", ROOT / "services"]
    allowed = {
        Path("services/admin/config_editor.py"),
    }
    forbidden_runtime_write_tokens = {
        'CONFIG_PATH.open("w"',
        "CONFIG_PATH.open('w'",
        "CONFIG_PATH.write_bytes(",
        "CONFIG_PATH.write_text(",
        "CONFIG_PATH.unlink(",
        "BACKUP_PATH.write_bytes(",
        "BACKUP_PATH.write_text(",
    }

    violations: list[str] = []
    for scan_root in scanned_roots:
        for path in sorted(scan_root.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if rel in allowed:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in sorted(forbidden_runtime_write_tokens):
                if token in text:
                    violations.append(f"{rel}:{token}")

    assert violations == []
