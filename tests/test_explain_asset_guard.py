"""Offline contract: literal ticker tokens, not substrings or semantic identity."""
import pytest

from dashboard.services.views._shared_signals import _explain_mentions_foreign_asset


@pytest.mark.parametrize("field", ["current_cause", "past_precedent", "future_catalyst"])
def test_ordinary_words_are_not_foreign_tickers(field):
    assert not _explain_mentions_foreign_asset(
        {field: "BTC: whether the method resolves consolidation remains unknown."}, "BTC")


@pytest.mark.parametrize("selected", ["BTC", "ETH", "SOL", "ADA"])
@pytest.mark.parametrize("mentioned", ["BTC", "ETH", "SOL"])
def test_standalone_known_ticker_matrix(selected, mentioned):
    assert _explain_mentions_foreign_asset(
        {"current_cause": f"{mentioned.lower()} demand increased."}, selected) is (mentioned != selected)


@pytest.mark.parametrize("mention", ["$ETH", "(ETH)", "ETH-USD", "ETH/USD", "ETH_USD"])
def test_ticker_punctuation_and_pair_separators_are_recognized(mention):
    assert _explain_mentions_foreign_asset({"current_cause": mention}, "BTC")


def test_unicode_alphanumeric_words_do_not_create_partial_tickers():
    assert not _explain_mentions_foreign_asset({"current_cause": "méthode αETHβ ETH2"}, "BTC")


def test_asset_metadata_does_not_override_wrong_asset_narrative():
    assert _explain_mentions_foreign_asset({"asset": "BTC", "current_cause": "SOL demand increased."}, "BTC")


def test_mixed_asset_policy_is_unchanged_not_semantically_resolved():
    # This remains rejected by the existing contract; deciding when mixed context is valid is separate.
    assert _explain_mentions_foreign_asset({"current_cause": "BTC and ETH share liquidity drivers."}, "BTC")


def test_missing_narrative_and_uninspected_evidence_fields_are_unchanged():
    assert not _explain_mentions_foreign_asset({}, "BTC")
    assert not _explain_mentions_foreign_asset({"evidence": [{"summary": "SOL"}]}, "BTC")
