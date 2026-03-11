from __future__ import annotations

from sqlalchemy import select

from shared.db import SessionLocal
from shared.models.documents import Asset

SEED_ASSETS = [
    {"symbol": "BTC", "name": "Bitcoin"},
    {"symbol": "ETH", "name": "Ethereum"},
    {"symbol": "SOL", "name": "Solana"},
]


def main() -> None:
    with SessionLocal() as db:
        inserted = 0
        for a in SEED_ASSETS:
            exists = db.execute(select(Asset).where(Asset.symbol == a["symbol"])).scalar_one_or_none()
            if exists:
                continue
            db.add(Asset(symbol=a["symbol"], name=a["name"], asset_type="crypto", is_active=True))
            inserted += 1
        db.commit()
    print({"status": "ok", "inserted": inserted, "assets": [a["symbol"] for a in SEED_ASSETS]})


if __name__ == "__main__":
    main()
