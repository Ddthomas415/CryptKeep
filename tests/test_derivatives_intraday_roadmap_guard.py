from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs" / "research" / "derivatives_intraday_roadmap.md"


def _text(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return " ".join(text.split())


def test_derivatives_intraday_roadmap_names_non_authority_boundary() -> None:
    text = _flat(DOC.read_text(encoding="utf-8"))

    required = [
        "Backlog link: `REMAINING_TASKS.md` Active Backlog item 15.",
        "read-only data collection, archived research, and replay",
        "does not authorize derivatives execution",
        "short selling",
        "leverage",
        "margin",
        "live intraday routing",
        "strategy promotion evidence",
        "no real capital",
        "does not add credentials",
        "does not add credentials, dependencies, fetches, storage, campaigns, gates, or execution",
    ]
    missing = [item for item in required if item not in text]
    assert missing == []


def test_derivatives_intraday_roadmap_blocks_execution_until_controls_exist() -> None:
    text = _flat(DOC.read_text(encoding="utf-8"))

    blocked = [
        "Live or capped-live derivatives orders.",
        "Short-side execution, margin, leverage, borrow, or perpetual futures routing.",
        "Paper or shadow derivatives campaigns that model executable positions.",
        "Strategy promotion evidence sourced from derivatives/intraday context",
        "Venue/broker integration that requires private credentials",
        "Any Databento-backed ingestion path that fetches data",
    ]
    assert all(item in text for item in blocked)

    required_proofs = [
        "venue or broker compliance and account-permission decision",
        "contract/symbology metadata",
        "margin model",
        "liquidation-buffer model",
        "funding, borrow, fee, spread, and slippage cost model",
        "reduce-only exit support",
        "fail-closed risk gates",
        "sandbox/testnet lifecycle proof",
        "archive/walk-forward evidence after measured costs",
        "current paper campaign and promotion gate remain unchanged",
    ]
    assert all(item in text for item in required_proofs)


def test_derivatives_intraday_backlog_and_related_docs_link_the_boundary() -> None:
    backlog = _text("REMAINING_TASKS.md")
    crypto_edge = _text("docs/research/crypto_edge_source_decision.md")
    pattern_backlog = _text("docs/research/pattern_strategy_backlog.md")
    databento = _text("docs/research/databento_data_source_rfc.md")
    websocket = _text("docs/architecture/websocket_surface_classification.md")

    assert "docs/research/derivatives_intraday_roadmap.md" in backlog
    assert "read-only derivatives context source" in crypto_edge
    assert "does not enable derivatives execution" in crypto_edge
    assert "short-side variants once derivatives data and risk controls are proven" in pattern_backlog
    assert "Databento" in databento and "No implementation" in databento
    assert "execution change is authorized by this document" in databento
    assert "not automatically" in websocket and "canonical data path" in websocket
