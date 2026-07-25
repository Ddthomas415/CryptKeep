from __future__ import annotations

from pathlib import Path


REPO = Path(__file__).resolve().parents[1]

MUST_KEEP = {
    "promotion evidence JSONL",
    "strategy decision records",
    "work-log entries",
    "gate output checkpoints",
    "trade journal databases",
    "shadow would-be-fill evidence",
    "archive dataset manifests and hashes",
    "deployment/migration proof packets",
}

MAY_ROTATE = {
    "debug logs",
    "transient status files",
    "dashboard cache artifacts",
    "old local notification reports",
    "temporary preflight outputs",
}

MUST_NOT_KEEP = {
    "API secrets",
    "raw private keys",
    "exchange account tokens",
    "unredacted credential prompts",
    "sensitive provider responses not needed for evidence",
}

PRUNE_REQUIREMENTS = {
    "artifact family",
    "retention cutoff",
    "backup status",
    "dry-run output",
    "operator approval",
}

SERVER_BASELINE = {
    "repo filesystem free space: at least 2 GiB",
    "repo filesystem free inodes: at least 10,000",
    "backup directory: `/srv/cryptkeep/backups`",
    "UTC/NTP sync",
    "backup age",
    "last restore-test",
}


def _text(path: str) -> str:
    return (REPO / path).read_text(encoding="utf-8")


def _normalized(path: str) -> str:
    return " ".join(_text(path).split())


def test_retention_policy_preserves_keep_rotate_and_forbidden_families() -> None:
    text = _text("docs/RETENTION_POLICY.md")

    assert "default to keep evidence artifacts indefinitely" in text
    for item in MUST_KEEP:
        assert item in text
    for item in MAY_ROTATE:
        assert item in text
    for item in MUST_NOT_KEEP:
        assert item in text
    assert "treat it as a security incident" in text


def test_retention_policy_preserves_pruning_safety_contract() -> None:
    text = _text("docs/RETENTION_POLICY.md")

    assert "No pruning command should delete canonical evidence by glob alone." in text
    for requirement in PRUNE_REQUIREMENTS:
        assert requirement in text


def test_retention_policy_preserves_server_threshold_baseline() -> None:
    text = _normalized("docs/RETENTION_POLICY.md")

    assert "`docs/HETZNER_PAPER_HOST.md`" in text
    assert (REPO / "docs/HETZNER_PAPER_HOST.md").is_file()
    for item in SERVER_BASELINE:
        assert item in text
    assert "not capped-live launch proof" in text
    assert "fresh backup/restore drill" in text
