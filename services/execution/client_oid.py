# stub

# --- compat shim: expected by services.execution.intent_executor ---
def make_client_oid32(prefix: str = "cbp") -> str:
    """Return a 32-char client order id (hex)."""
    import secrets
    base = secrets.token_hex(16)  # 32 hex chars
    if prefix:
        # keep it compact; ccxt usually accepts any string
        return f"{prefix}-{base}"
    return base
