from typing import Literal

from pydantic import BaseModel

ModeLiteral = Literal["research_only", "paper", "live_approval", "live_auto"]


class GeneralSettings(BaseModel):
    timezone: str
    default_currency: str
    startup_page: str
    default_mode: ModeLiteral
    watchlist_defaults: list[str]


class NotificationSettings(BaseModel):
    email: bool
    telegram: bool
    discord: bool
    webhook: bool
    price_alerts: bool
    news_alerts: bool
    catalyst_alerts: bool
    risk_alerts: bool
    approval_requests: bool


class AISettings(BaseModel):
    explanation_length: str
    tone: str
    show_evidence: bool
    show_confidence: bool
    include_archives: bool
    include_onchain: bool
    include_social: bool
    allow_hypotheses: bool


class SecuritySettings(BaseModel):
    session_timeout_minutes: int
    secret_masking: bool
    audit_export_allowed: bool


class SettingsPayload(BaseModel):
    general: GeneralSettings
    notifications: NotificationSettings
    ai: AISettings
    security: SecuritySettings

    @classmethod
    def example(cls) -> dict:
        return cls(
            general=GeneralSettings(
                timezone="America/New_York",
                default_currency="USD",
                startup_page="/dashboard",
                default_mode="research_only",
                watchlist_defaults=["BTC", "ETH", "SOL"],
            ),
            notifications=NotificationSettings(
                email=False,
                telegram=True,
                discord=False,
                webhook=False,
                price_alerts=True,
                news_alerts=True,
                catalyst_alerts=True,
                risk_alerts=True,
                approval_requests=True,
            ),
            ai=AISettings(
                explanation_length="normal",
                tone="balanced",
                show_evidence=True,
                show_confidence=True,
                include_archives=True,
                include_onchain=True,
                include_social=False,
                allow_hypotheses=True,
            ),
            security=SecuritySettings(
                session_timeout_minutes=60,
                secret_masking=True,
                audit_export_allowed=True,
            ),
        ).model_dump()


class GeneralSettingsUpdate(BaseModel):
    timezone: str | None = None
    default_currency: str | None = None
    startup_page: str | None = None
    default_mode: ModeLiteral | None = None
    watchlist_defaults: list[str] | None = None


class NotificationSettingsUpdate(BaseModel):
    email: bool | None = None
    telegram: bool | None = None
    discord: bool | None = None
    webhook: bool | None = None
    price_alerts: bool | None = None
    news_alerts: bool | None = None
    catalyst_alerts: bool | None = None
    risk_alerts: bool | None = None
    approval_requests: bool | None = None


class AISettingsUpdate(BaseModel):
    explanation_length: str | None = None
    tone: str | None = None
    show_evidence: bool | None = None
    show_confidence: bool | None = None
    include_archives: bool | None = None
    include_onchain: bool | None = None
    include_social: bool | None = None
    allow_hypotheses: bool | None = None


class SecuritySettingsUpdate(BaseModel):
    session_timeout_minutes: int | None = None
    secret_masking: bool | None = None
    audit_export_allowed: bool | None = None


class SettingsUpdatePayload(BaseModel):
    general: GeneralSettingsUpdate | None = None
    notifications: NotificationSettingsUpdate | None = None
    ai: AISettingsUpdate | None = None
    security: SecuritySettingsUpdate | None = None
