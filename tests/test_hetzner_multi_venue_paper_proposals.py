from __future__ import annotations

import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
PROPOSAL = REPO / "configs" / "paper_evidence_campaigns.hetzner.multi_venue_proposed.json"
GATEIO_ACTIVE = REPO / "configs" / "paper_evidence_campaigns.hetzner.gateio_challenger.json"
BINANCE_ACTIVE = REPO / "configs" / "paper_evidence_campaigns.hetzner.binance_challenger.json"
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
        "make status-hetzner-gateio-challenger HETZNER_STATUS_TRANSPORT=ssh",
        "make restore-hetzner-gateio-challenger",
        "make status-hetzner-binance-challenger HETZNER_STATUS_TRANSPORT=ssh",
        "make restore-hetzner-binance-challenger",
        "Do not run the start command from an old checkout",
    ):
        assert needle in text


def test_hetzner_gateio_challenger_manifest_is_isolated_and_single_venue() -> None:
    payload = json.loads(GATEIO_ACTIVE.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    campaigns = payload["campaigns"]
    assert len(campaigns) == 1
    row = campaigns[0]
    assert row["enabled"] is True
    assert row["name"] == "ema_cross_gateio_btcusdt_paper_candidate"
    assert row["session_strategy_id"] == "ema_cross_gateio_btcusdt_paper_candidate"
    assert row["strategy"] == "ema_cross"
    assert row["venue"] == "gateio"
    assert row["symbol"] == "BTC/USDT"
    assert row["signal_source"] == "public_ohlcv_5m"
    assert row["state_dir"] == ".cbp_state_challengers/ema_cross_gateio_btcusdt_daily"
    assert row["state_dir"] != ".cbp_state"
    assert row["session_strategy_id"] != "es_daily_trend_v1"
    assert row["desktop_notify"] is False


def test_hetzner_gateio_challenger_manifest_loads_as_one_campaign() -> None:
    from services.analytics.paper_campaign_recovery import load_campaign_specs

    specs = load_campaign_specs(GATEIO_ACTIVE)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.name == "ema_cross_gateio_btcusdt_paper_candidate"
    assert spec.venue == "gateio"
    assert spec.state_dir.as_posix().endswith(".cbp_state_challengers/ema_cross_gateio_btcusdt_daily")


def test_hetzner_binance_challenger_manifest_is_guarded_isolated_and_single_venue() -> None:
    payload = json.loads(BINANCE_ACTIVE.read_text(encoding="utf-8"))

    assert payload["schema_version"] == 1
    campaigns = payload["campaigns"]
    assert len(campaigns) == 1
    row = campaigns[0]
    assert row["enabled"] is True
    assert row["name"] == "ema_cross_binance_btcusdt_paper_candidate"
    assert row["session_strategy_id"] == "ema_cross_binance_btcusdt_paper_candidate"
    assert row["strategy"] == "ema_cross"
    assert row["venue"] == "binance"
    assert row["symbol"] == "BTC/USDT"
    assert row["signal_source"] == "public_ohlcv_5m"
    assert row["state_dir"] == ".cbp_state_challengers/ema_cross_binance_btcusdt_daily"
    assert row["state_dir"] != ".cbp_state"
    assert row["session_strategy_id"] != "es_daily_trend_v1"
    assert row["desktop_notify"] is False


def test_hetzner_binance_challenger_manifest_loads_as_one_campaign() -> None:
    from services.analytics.paper_campaign_recovery import load_campaign_specs

    specs = load_campaign_specs(BINANCE_ACTIVE)

    assert len(specs) == 1
    spec = specs[0]
    assert spec.name == "ema_cross_binance_btcusdt_paper_candidate"
    assert spec.venue == "binance"
    assert spec.state_dir.as_posix().endswith(".cbp_state_challengers/ema_cross_binance_btcusdt_daily")
