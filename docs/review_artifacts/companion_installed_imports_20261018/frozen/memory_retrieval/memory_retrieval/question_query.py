"""Transparent English conversational scaffolding removal, not semantic search."""
import re


PREFIX = re.compile(
    r"^(?:please\s+)?(?:"
    r"(?:what|which)\s+news\s+explains?|"
    r"(?:can|could)\s+you\s+explain|tell\s+me\s+about|show\s+me|explain|"
    r"(?:what|why)\s+(?:is|are|was|were)|how\s+(?:does|did|do|is)|"
    r"what|why|how|which)\s+", re.I)


def question_query(question: str):
    original = question[:2000]
    query = original
    mode = "EXACT_QUERY"
    if ('"' in original or re.search(r"\b(?:OR|AND)\b", original, re.I)
            or re.search(r"\bNOT\b", original)):
        mode = "EXPLICIT_SYNTAX_PRESERVED"
    elif re.search(r"\b(?:no|not|never|without)\b", original, re.I):
        mode = "NEGATION_PRESERVED"
    elif re.search(r"\d", original):
        mode = "NUMERIC_QUERY_PRESERVED"
    elif '-' in original:
        mode = "EXPLICIT_SYNTAX_PRESERVED"
    elif PREFIX.search(original.strip()):
        working = PREFIX.sub("", original.strip(), count=1).rstrip("?.").strip()
        if working and working.lower() != "news":
            query = working
            mode = "CONVERSATIONAL_FILLER_REMOVED"
        else:
            mode = "NO_TOPIC_PRESERVED"
    return {"original": original, "query": query, "mode": mode,
            "method": "english_conversational_scaffolding_v1",
            "semantic_relevance_verified": False,
            "relative_time_interpreted": False}
