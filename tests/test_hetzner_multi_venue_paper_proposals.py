from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROPOSAL = REPO / "configs" / "paper_evidence_campaigns.hetzner.multi_venue_proposed.json"
DOC = REPO / "docs" / "strategies" / "hetzner_multi_venue_paper_research_proposals.md"


def _proposal() -> dict:
    return json.loads(PROPOSAL.read_text(encoding="utf-8"))


def test_hetzner_multi_venue_proposals_are_disabled_and_isolated() -> None:
    payload = _proposal()

    assert payload["schema_version"] == 1
    campaigns = payload["campaigns"]
    assert {row["venue"] for row in campaigns} == {"gateio", "binance"}
    assert {row["symbol"] for row in campaigns} == {"BTC/USDT"}
    assert {row["signal_source"] for row in campaigns} == {"public_ohlcv_5m"}

    for row in campaigns:
        assert row["enabled"] is False
        assert row["desktop_notify"] is False
        assert row["state_dir"].startswith(".cbp_state_challengers/")
        assert row["state_dir"] != ".cbp_state"
        assert row["session_strategy_id"] != "es_daily_trend_v1"
        assert row["strategy"] == "ema_cross"


def test_hetzner_multi_venue_proposals_do_not_embed_live_or_secret_controls() -> None:
    text = PROPOSAL.read_text(encoding="utf-8")

    forbidden = (
        "api_key",
        "apiKey",
        "secret",
        "password",
        "live_enabled",
        "executor_mode",
        "order_submission",
        "CBP_EXECUTION_ARMED",
    )
    for needle in forbidden:
        assert needle not in text


def test_hetzner_multi_venue_proposal_doc_pins_preflight_and_boundaries() -> None:
    text = " ".join(DOC.read_text(encoding="utf-8").split())

    for needle in (
        "proposal only; not an active campaign manifest",
        "check_ohlcv_preflight.py --venue gateio --symbol BTC/USDT --signal-source public_ohlcv_5m",
        "CBP_VENUE=binance CBP_ALLOW_BINANCE=1",
        "check_ohlcv_preflight.py --venue binance --symbol BTC/USDT --signal-source public_ohlcv_5m",
        "must not count toward the canonical `es_daily_trend_v1` promotion gate",
        "No exchange credentials, live routing, order submission, host package install",
    ):
        assert needle in text
