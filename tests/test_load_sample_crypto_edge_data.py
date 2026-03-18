from __future__ import annotations

import json

from scripts import load_sample_crypto_edge_data as script


def test_load_sample_crypto_edge_data_writes_bundled_rows(tmp_path, monkeypatch, capsys) -> None:
    db_path = tmp_path / "crypto_edges.sqlite"
    monkeypatch.setattr(
        script.sys,
        "argv",
        [
            "load_sample_crypto_edge_data.py",
            "--db-path",
            str(db_path),
            "--print-report",
        ],
    )

    assert script.main() == 0
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["funding_count"] >= 1
    assert out["basis_count"] >= 1
    assert out["quote_count"] >= 1
    assert out["report"]["has_any_data"] is True
    assert out["report"]["research_only"] is True
