from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_dashboard_auth_user_storage_boundary_stays_centralized() -> None:
    """User/role mutations must stay behind services.security.user_auth_store.

    The audited store owns the auth keyring service and rollback-on-audit-failure
    behavior. A new dashboard/security source file that writes the same backing
    records directly would bypass that contract.
    """

    scanned_roots = [ROOT / "dashboard", ROOT / "scripts", ROOT / "services"]
    allowed = {
        Path("services/security/user_auth_store.py"),
    }
    forbidden_tokens = {
        '"crypto-bot-pro-auth"',
        '"__users_index__"',
        "_save_user_record(",
        "_save_users_index(",
        "_keyring_set(",
        "_keyring_clear(",
    }

    violations: list[str] = []
    for scan_root in scanned_roots:
        for path in sorted(scan_root.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if rel in allowed:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for token in sorted(forbidden_tokens):
                if token in text:
                    violations.append(f"{rel}:{token}")

    assert violations == []
