import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "phase1_research_copilot"))
from memory_retrieval.question_query import question_query


@pytest.mark.parametrize("original, expected, mode", [
    ("What news explains Bitcoin liquidations?", "Bitcoin liquidations", "CONVERSATIONAL_FILLER_REMOVED"),
    ("Please explain Bitcoin liquidations.", "Bitcoin liquidations", "CONVERSATIONAL_FILLER_REMOVED"),
    ("What is Bitcoin regulation?", "Bitcoin regulation", "CONVERSATIONAL_FILLER_REMOVED"),
    ("Bitcoin news", "Bitcoin news", "EXACT_QUERY"),
    ("Bitcoin OR Ethereum", "Bitcoin OR Ethereum", "EXPLICIT_SYNTAX_PRESERVED"),
    ("What Bitcoin or Ethereum news?", "What Bitcoin or Ethereum news?", "EXPLICIT_SYNTAX_PRESERVED"),
    ('"Bitcoin liquidations" -Ethereum', '"Bitcoin liquidations" -Ethereum', "EXPLICIT_SYNTAX_PRESERVED"),
    ("Explain Bitcoin not recovering", "Explain Bitcoin not recovering", "NEGATION_PRESERVED"),
    ("What happened to Bitcoin on 2026-10-01?", "What happened to Bitcoin on 2026-10-01?", "NUMERIC_QUERY_PRESERVED"),
    ("What news?", "What news?", "NO_TOPIC_PRESERVED"),
    ("zzzzzzunmatched", "zzzzzzunmatched", "EXACT_QUERY"),
    ("What is fake news about Bitcoin?", "fake news about Bitcoin", "CONVERSATIONAL_FILLER_REMOVED"),
    ("What is CAN?", "CAN", "CONVERSATIONAL_FILLER_REMOVED"),
    ("What explains Bitcoin - Ethereum?", "What explains Bitcoin - Ethereum?", "EXPLICIT_SYNTAX_PRESERVED"),
    ("Explain Bitcoin news about Ethereum", "Bitcoin news about Ethereum", "CONVERSATIONAL_FILLER_REMOVED"),
])
def test_fixed_query_contract(original, expected, mode):
    result = question_query(original)
    assert result["original"] == original
    assert result["query"] == expected
    assert result["mode"] == mode
    assert result["semantic_relevance_verified"] is False
    assert result["relative_time_interpreted"] is False


def test_queries_remain_bounded_and_temporal_words_not_silently_removed():
    result = question_query("What news explains Bitcoin today?")
    assert result["query"] == "Bitcoin today"
    assert len(question_query("a" * 3000)["query"]) == 2000
