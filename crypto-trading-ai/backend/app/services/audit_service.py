from backend.app.schemas.audit import AuditEvent


class AuditService:
    def list_events(self, page: int = 1, page_size: int = 20) -> tuple[dict, dict]:
        items = [
            AuditEvent(
                id="audit_1",
                timestamp="2026-03-11T13:00:12Z",
                service="orchestrator",
                action="explain_asset",
                result="success",
                request_id="req_123",
                details="Generated explanation for SOL",
            ).model_dump(),
            AuditEvent(
                id="audit_2",
                timestamp="2026-03-11T13:02:12Z",
                service="risk_engine",
                action="evaluate_trade",
                result="blocked",
                request_id="req_124",
                details="Execution disabled in research mode",
            ).model_dump(),
        ]

        meta = {
            "page": page,
            "page_size": page_size,
            "total": len(items),
        }
        return {"items": items}, meta
