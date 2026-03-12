from backend.app.schemas.trading import RecommendationItem


class TradingService:
    def list_recommendations(self) -> dict:
        items = [
            RecommendationItem(
                id="rec_1",
                asset="SOL",
                side="buy",
                strategy="event_momentum",
                confidence=0.74,
                entry_zone="186-188",
                stop="181",
                target_logic="trailing",
                risk_size_pct=1.5,
                mode_compatibility=["paper", "live_approval"],
                approval_required=True,
                status="pending_review",
                execution_disabled=True,
            ).model_dump()
        ]
        return {"items": items}
