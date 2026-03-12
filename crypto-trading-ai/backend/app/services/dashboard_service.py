from backend.app.schemas.dashboard import DashboardSummary


class DashboardService:
    def get_summary(self) -> dict:
        return DashboardSummary.example()
