from backend.app.schemas.connections import ConnectionRecord, ConnectionTestResult


class ConnectionsService:
    def list_exchanges(self) -> dict:
        items = [
            ConnectionRecord(
                id="conn_coinbase_1",
                provider="coinbase",
                label="Main Coinbase",
                environment="live",
                status="connected",
                permissions={"read": True, "trade": False},
                spot_supported=True,
                futures_supported=False,
                last_sync="2026-03-11T13:05:00Z",
                latency_ms=184,
            ).model_dump(),
            ConnectionRecord(
                id="conn_binance_1",
                provider="binance",
                label="Research Binance",
                environment="live",
                status="disabled",
                permissions={"read": False, "trade": False},
                spot_supported=True,
                futures_supported=True,
                last_sync=None,
                latency_ms=None,
            ).model_dump(),
        ]
        return {"items": items}

    def test_exchange(self, provider: str, environment: str) -> dict:
        return ConnectionTestResult(
            success=True,
            permissions={"read": True, "trade": False},
            spot_supported=True,
            futures_supported=False,
            balances_loaded=True,
            latency_ms=184,
            warnings=[],
        ).model_dump()

    def save_exchange(self, provider: str, label: str, environment: str) -> dict:
        return {
            "id": "conn_saved_1",
            "provider": provider,
            "label": label,
            "environment": environment,
            "status": "connected",
        }
