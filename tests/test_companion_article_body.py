"""Article boundaries must not infer assets or timelines from site chrome."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "phase1_research_copilot"))
from parser_normalizer.main import _build_doc, _extract_document_text, _extract_text_and_title


def document(html):
    return _build_doc(url="https://example.test/story", source="fixture", source_type="news",
                      html=html, timeline_hint=None, asset_hint=[], published_at=None,
                      metadata={"operator_note": "preserve", "article_body_boundary_verified": True})


def test_observed_body_excludes_navigation_related_stories_and_ads():
    html = ('<title>Stablecoin survey</title><nav>Bitcoin upcoming unlock</nav>'
            '<main><div data-article-body-start><div class="document-body"><p>Stablecoin adoption survey.</p>'
            '<aside>Bitcoin liquidation</aside><div class="ad-container">Solana launch</div></div>'
            '</div></main><footer>Ethereum historical</footer>')
    doc = document(html)
    assert doc["content_text"] == "Stablecoin adoption survey."
    assert doc["asset_tags"] == []
    assert doc["timeline_tag"] == "present"
    assert doc["raw_html"] == html
    assert doc["metadata"]["operator_note"] == "preserve"
    assert doc["metadata"]["article_body_boundary_verified"] is True


def test_post_body_retains_actual_bitcoin_content():
    doc = document('<title>Bitcoin liquidations</title><div data-testid="post__body">'
                   '<p>Bitcoin liquidation pressure.</p></div><article>Ethereum launch</article>')
    assert doc["asset_tags"] == ["BTC"]
    assert doc["content_text"] == "Bitcoin liquidation pressure."
    assert doc["metadata"]["extraction_method"] == "observed_article_body_v1"


def test_unknown_or_ambiguous_body_retains_fallback_but_never_claims_verified():
    for html in ('<title>Generic</title><p>Bitcoin content</p>',
                 '<div class="document-body">First</div><div class="document-body">Second</div>'):
        doc = document(html)
        assert doc["content_text"]
        assert doc["metadata"]["extraction_method"] == "whole_page_fallback_unverified"
        assert doc["metadata"]["article_body_boundary_verified"] is False


def test_existing_two_value_extraction_interface_is_preserved():
    assert _extract_text_and_title('<title>News</title><div data-testid="post__body">Body</div>') == ("Body", "News")


def test_split_article_sections_do_not_include_disclosure_with_same_class():
    text, _, method = _extract_document_text(
        '<title>Survey</title><main><div data-article-body-start>'
        '<div class="document-body">First section.</div><div class="document-body">Second section.</div>'
        '</div></main><div class="document-body">Bitcoin disclosure.</div>')
    assert text == "First section. Second section."
    assert method == "observed_article_body_v1"


def test_empty_observed_body_is_not_verified():
    doc = document('<title>News</title><div data-testid="post__body"></div><p>Site navigation</p>')
    assert doc["metadata"]["article_body_boundary_verified"] is False
