from pydantic import BaseModel


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


class ExchangeTestRequest(BaseModel):
    provider: str
    environment: str = "live"
    credentials: ConnectionCredentialsInput


class ExchangeSaveRequest(BaseModel):
    provider: str
    label: str
    environment: str = "live"
    credentials: ConnectionCredentialsInput
    permissions: dict = {"read_only": True, "allow_live_trading": False}


class ExchangeConnectionListResponse(BaseModel):
    items: list[ConnectionRecord]


class ExchangeSaveResponse(BaseModel):
    id: str
    provider: str
    label: str
    environment: str
    status: str
