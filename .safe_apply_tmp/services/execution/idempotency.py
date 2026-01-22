# Phase IX/IY: Idempotency

def client_oid(intent_id: str) -> str:
    return f"intent-{intent_id}"
