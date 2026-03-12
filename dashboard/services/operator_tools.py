from __future__ import annotations


def parse_symbol_list(raw: str) -> list[str]:
    items = str(raw or "").replace("\n", ",").split(",")
    out: list[str] = []
    for item in items:
        sym = item.strip()
        if sym:
            out.append(sym)
    return out


def synthetic_ohlcv(count: int, *, start_px: float = 100.0) -> list[list[float]]:
    rows: list[list[float]] = []
    n = max(30, int(count))
    seg = max(10, n // 3)
    prev_close = float(start_px)
    base_ts = 1_700_000_000_000

    for i in range(n):
        if i < seg:
            close_px = start_px - 0.32 * i
        elif i < 2 * seg:
            close_px = start_px - 0.32 * seg + 0.42 * (i - seg)
        else:
            close_px = start_px - 0.32 * seg + 0.42 * seg - 0.36 * (i - 2 * seg)

        # Deterministic spikes force breakout-style edges in synthetic data.
        if i % 17 == 0:
            close_px += 0.8
        elif i % 19 == 0:
            close_px -= 0.8

        open_px = prev_close
        high_px = max(open_px, close_px) + 0.25
        low_px = min(open_px, close_px) - 0.25
        rows.append(
            [float(base_ts + (i * 60_000)), float(open_px), float(high_px), float(low_px), float(close_px), 1.0]
        )
        prev_close = close_px
    return rows
