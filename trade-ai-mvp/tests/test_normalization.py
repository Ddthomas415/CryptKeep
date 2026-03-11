from services.parser_normalizer.parsers.tagger import (
    compute_content_hash,
    extract_asset_tags,
    infer_timeline_tag,
)


def test_timeline_tag_rules():
    assert infer_timeline_tag("A governance vote will happen next week") == "future"
    assert infer_timeline_tag("Historical roadmap was delayed last year") == "past"
    assert infer_timeline_tag("Current market activity increases") == "present"


def test_asset_tag_extraction():
    tags = extract_asset_tags("SOL and BTC moved while ETH stayed flat")
    assert "SOL" in tags
    assert "BTC" in tags
    assert "ETH" in tags


def test_content_hash_stable():
    h1 = compute_content_hash("title", "url", "text")
    h2 = compute_content_hash("title", "url", "text")
    assert h1 == h2
    assert len(h1) == 64
