from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_exchange_api_credential_keyring_mutations_stay_centralized() -> None:
    """Exchange API credential writes must stay behind credential_store."""

    scanned_roots = [ROOT / "dashboard", ROOT / "scripts", ROOT / "services"]
    allowed = {
        Path("services/security/credential_store.py"),
    }
    keyring_write_tokens = {
        ".set_password(",
        ".delete_password(",
        "set_password(",
        "delete_password(",
    }
    exchange_credential_tokens = {
        "apiKey",
        "api_secret",
        "apiSecret",
        "passphrase",
    }

    violations: list[str] = []
    for scan_root in scanned_roots:
        for path in sorted(scan_root.rglob("*.py")):
            rel = path.relative_to(ROOT)
            if rel in allowed:
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            if not any(token in text for token in keyring_write_tokens):
                continue
            if any(token in text for token in exchange_credential_tokens):
                violations.append(str(rel))

    assert violations == []
