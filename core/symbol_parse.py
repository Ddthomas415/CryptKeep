from __future__ import annotations

_KNOWN_QUOTES = ("USDT", "USDC", "USD", "BTC", "ETH", "EUR", "GBP")


def split_symbol(symbol: str) -> tuple[str, str]:
    text = str(symbol or "").strip().upper()
    if not text:
        return "", ""

    normalized = text.replace("/", "-").replace("_", "-")
    while "--" in normalized:
        normalized = normalized.replace("--", "-")

    if "-" in normalized:
        base, quote = normalized.split("-", 1)
        return base.strip(), quote.strip()

    for quote in _KNOWN_QUOTES:
        if normalized.endswith(quote) and len(normalized) > len(quote):
            return normalized[: -len(quote)], quote
    return normalized, ""
