from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

SUPPORTED_EXCHANGE_PROVIDERS = ("binance", "coinbase", "kraken", "okx")
PROVIDER_ENVIRONMENTS: dict[str, set[str]] = {
    "binance": {"sandbox", "live"},
    "coinbase": {"sandbox", "live"},
    "kraken": {"sandbox", "live"},
    "okx": {"demo", "live"},
}


class ConnectionPermissions(BaseModel):
    read: bool
    trade: bool


class ConnectionRecord(BaseModel):
    id: str
    provider: str
    label: str
    environment: str
    status: str
    permissions: ConnectionPermissions | dict
    spot_supported: bool | None = None
    futures_supported: bool | None = None
    last_sync: str | None = None
    latency_ms: int | None = None


class ConnectionTestResult(BaseModel):
    success: bool
    permissions: ConnectionPermissions | dict
    spot_supported: bool
    futures_supported: bool
    balances_loaded: bool
    latency_ms: int
    warnings: list[str]


class TestConnectionResponse(ConnectionTestResult):
    pass


class ConnectionCredentialsInput(BaseModel):
    api_key: str = ""
    api_secret: str = ""
    passphrase: str = ""


class ExchangePermissionsInput(BaseModel):
    read_only: bool = True
    allow_live_trading: bool = False


class ExchangeTestRequest(BaseModel):
    provider: Literal["binance", "coinbase", "kraken", "okx"]
    environment: str = "live"
    credentials: ConnectionCredentialsInput

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return str(value).strip().lower()

    @model_validator(mode="after")
    def validate_provider_environment(self):
        allowed = PROVIDER_ENVIRONMENTS[self.provider]
        if self.environment not in allowed:
            raise ValueError(
                f"environment must be one of {sorted(allowed)} for provider '{self.provider}'"
            )
        return self


class ExchangeSaveRequest(BaseModel):
    provider: Literal["binance", "coinbase", "kraken", "okx"]
    label: str = Field(min_length=1, max_length=120)
    environment: str = "live"
    credentials: ConnectionCredentialsInput
    permissions: ExchangePermissionsInput = ExchangePermissionsInput()

    @field_validator("environment", mode="before")
    @classmethod
    def normalize_environment(cls, value: str) -> str:
        return str(value).strip().lower()

    @model_validator(mode="after")
    def validate_provider_environment(self):
        allowed = PROVIDER_ENVIRONMENTS[self.provider]
        if self.environment not in allowed:
            raise ValueError(
                f"environment must be one of {sorted(allowed)} for provider '{self.provider}'"
            )
        return self


class ExchangeConnectionListResponse(BaseModel):
    items: list[ConnectionRecord]


class ExchangeSaveResponse(BaseModel):
    id: str
    provider: str
    label: str
    environment: str
    status: str
