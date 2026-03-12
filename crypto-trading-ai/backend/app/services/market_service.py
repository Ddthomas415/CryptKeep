from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.app.schemas.market import MarketCandle, MarketCandlesResponse, MarketSnapshot


class MarketService:
    _SNAPSHOT_TEMPLATES = {
        "BTC": {
            "last_price": 90555.25,
            "bid": 90550.0,
            "ask": 90560.5,
            "volume_24h": 38500000000.0,
        },
        "ETH": {
            "last_price": 4431.8,
            "bid": 4429.7,
            "ask": 4433.1,
            "volume_24h": 17600000000.0,
        },
        "SOL": {
            "last_price": 187.42,
            "bid": 187.3,
            "ask": 187.54,
            "volume_24h": 2950000000.0,
        },
    }

    _SERIES_MULTIPLIERS = {
        "BTC": [0.972, 0.978, 0.983, 0.989, 0.994, 0.998, 1.002, 1.0],
        "ETH": [0.968, 0.975, 0.981, 0.987, 0.993, 0.999, 1.004, 1.0],
        "SOL": [0.955, 0.963, 0.974, 0.982, 0.991, 1.004, 1.012, 1.0],
    }

    _ANCHOR_TIME = datetime(2026, 3, 12, 0, 0, tzinfo=UTC)

    def get_snapshot(self, asset: str, exchange: str = "coinbase") -> dict:
        asset_symbol = str(asset or "BTC").strip().upper() or "BTC"
        exchange_name = str(exchange or "coinbase").strip().lower() or "coinbase"
        template = dict(self._SNAPSHOT_TEMPLATES.get(asset_symbol, self._build_generic_snapshot(asset_symbol)))
        spread = round(max(float(template["ask"]) - float(template["bid"]), 0.0), 2)
        return MarketSnapshot(
            asset=asset_symbol,
            exchange=exchange_name,
            last_price=float(template["last_price"]),
            bid=float(template["bid"]),
            ask=float(template["ask"]),
            spread=spread,
            volume_24h=float(template["volume_24h"]),
            timestamp=self._ANCHOR_TIME.isoformat().replace("+00:00", "Z"),
        ).model_dump()

    def get_candles(
        self,
        asset: str,
        exchange: str = "coinbase",
        interval: str = "1h",
        limit: int = 24,
    ) -> dict:
        snapshot = self.get_snapshot(asset=asset, exchange=exchange)
        asset_symbol = str(snapshot["asset"])
        exchange_name = str(snapshot["exchange"])
        candle_limit = max(2, min(int(limit or 24), 240))
        step = self._interval_delta(interval)
        multipliers = self._SERIES_MULTIPLIERS.get(asset_symbol, self._generic_series_multipliers(asset_symbol))
        base_price = float(snapshot["last_price"])

        closes = self._build_close_series(base_price=base_price, multipliers=multipliers, limit=candle_limit)
        candles: list[dict] = []
        for idx, close_price in enumerate(closes):
            previous_close = closes[idx - 1] if idx > 0 else round(close_price * 0.996, 2)
            high_price = round(max(previous_close, close_price) * 1.002, 2)
            low_price = round(min(previous_close, close_price) * 0.998, 2)
            ts = self._ANCHOR_TIME - step * (candle_limit - idx - 1)
            candles.append(
                MarketCandle(
                    timestamp=ts.isoformat().replace("+00:00", "Z"),
                    open=round(previous_close, 2),
                    high=high_price,
                    low=low_price,
                    close=round(close_price, 2),
                    volume=round((snapshot["volume_24h"] / 24.0) * (1.0 + (idx / max(candle_limit, 1)) * 0.12), 2),
                ).model_dump()
            )

        return MarketCandlesResponse(
            asset=asset_symbol,
            exchange=exchange_name,
            interval=str(interval or "1h"),
            candles=candles,
        ).model_dump()

    def _build_generic_snapshot(self, asset_symbol: str) -> dict[str, float]:
        base = max(25.0, 100.0 + float(sum(ord(char) for char in asset_symbol) % 175))
        return {
            "last_price": round(base, 2),
            "bid": round(base - 0.18, 2),
            "ask": round(base + 0.18, 2),
            "volume_24h": round(base * 1250000.0, 2),
        }

    def _generic_series_multipliers(self, asset_symbol: str) -> list[float]:
        drift = (sum(ord(char) for char in asset_symbol) % 6) / 1000.0
        return [0.972 + drift, 0.979 + drift, 0.986 + drift, 0.992 + drift, 0.997 + drift, 1.003 + drift, 1.009 + drift, 1.0]

    def _build_close_series(self, *, base_price: float, multipliers: list[float], limit: int) -> list[float]:
        if limit <= len(multipliers):
            selected = multipliers[-limit:]
        else:
            pad = [multipliers[0]] * (limit - len(multipliers))
            selected = [*pad, *multipliers]
        closes = [round(base_price * factor, 2) for factor in selected]
        closes[-1] = round(base_price, 2)
        return closes

    def _interval_delta(self, interval: str) -> timedelta:
        normalized = str(interval or "1h").strip().lower()
        mapping = {
            "1m": timedelta(minutes=1),
            "5m": timedelta(minutes=5),
            "15m": timedelta(minutes=15),
            "1h": timedelta(hours=1),
            "4h": timedelta(hours=4),
            "1d": timedelta(days=1),
        }
        return mapping.get(normalized, timedelta(hours=1))
