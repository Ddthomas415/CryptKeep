from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from scripts import paper_state_manifest as manifest


def _read_json(capsys) -> dict:
    return json.loads(capsys.readouterr().out)


def test_create_and_verify_manifest_round_trip(tmp_path: Path, capsys) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "b.jsonl").write_text("b\n", encoding="utf-8")
    (state / "nested").mkdir()
    (state / "nested" / "a.sqlite").write_bytes(b"a")
    out = tmp_path / "ema_cross_default.manifest"

    assert manifest.main(["create", "--state-dir", str(state), "--output", str(out)]) == 0
    created = _read_json(capsys)

    assert created["ok"] is True
    assert created["file_count"] == 2
    assert out.read_text(encoding="utf-8").splitlines() == [
        f"{manifest._sha256(state / 'b.jsonl')}  b.jsonl",
        f"{manifest._sha256(state / 'nested' / 'a.sqlite')}  nested/a.sqlite",
    ]

    assert manifest.main(["verify", "--state-dir", str(state), "--manifest", str(out)]) == 0
    verified = _read_json(capsys)
    assert verified["ok"] is True
    assert verified["missing"] == []
    assert verified["changed"] == []
    assert verified["extra"] == []


def test_verify_manifest_detects_missing_changed_and_extra(tmp_path: Path, capsys) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "changed.txt").write_text("before", encoding="utf-8")
    (state / "missing.txt").write_text("present", encoding="utf-8")
    out = tmp_path / "state.manifest"

    assert manifest.main(["create", "--state-dir", str(state), "--output", str(out)]) == 0
    _read_json(capsys)
    (state / "changed.txt").write_text("after", encoding="utf-8")
    (state / "missing.txt").unlink()
    (state / "extra.txt").write_text("extra", encoding="utf-8")

    assert manifest.main(["verify", "--state-dir", str(state), "--manifest", str(out)]) == 1
    verified = _read_json(capsys)

    assert verified["ok"] is False
    assert verified["missing"] == ["missing.txt"]
    assert verified["changed"] == ["changed.txt"]
    assert verified["extra"] == ["extra.txt"]


def test_create_rejects_manifest_output_inside_state_dir(tmp_path: Path, capsys) -> None:
    state = tmp_path / "state"
    state.mkdir()
    (state / "row.jsonl").write_text("{}\n", encoding="utf-8")

    assert (
        manifest.main(
            [
                "create",
                "--state-dir",
                str(state),
                "--output",
                str(state / "state.manifest"),
            ]
        )
        == 1
    )
    out = _read_json(capsys)
    assert out == {
        "ok": False,
        "action": "create",
        "reason": "manifest_output_inside_state_dir",
    }


def test_verify_rejects_manifest_path_escape(tmp_path: Path, capsys) -> None:
    state = tmp_path / "state"
    state.mkdir()
    bad = tmp_path / "bad.manifest"
    bad.write_text(f"{'0' * 64}  ../escape.txt\n", encoding="utf-8")

    assert manifest.main(["verify", "--state-dir", str(state), "--manifest", str(bad)]) == 1
    out = _read_json(capsys)
    assert out == {
        "ok": False,
        "action": "verify",
        "reason": "manifest_path_invalid",
    }


def test_create_rejects_symlinked_state_files(tmp_path: Path, capsys) -> None:
    state = tmp_path / "state"
    state.mkdir()
    target = tmp_path / "outside.txt"
    target.write_text("outside", encoding="utf-8")
    try:
        os.symlink(target, state / "link.txt")
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"symlink unavailable: {exc}")

    assert (
        manifest.main(
            [
                "create",
                "--state-dir",
                str(state),
                "--output",
                str(tmp_path / "state.manifest"),
            ]
        )
        == 1
    )
    out = _read_json(capsys)
    assert out == {
        "ok": False,
        "action": "create",
        "reason": "state_dir_symlink_not_supported:link.txt",
    }
