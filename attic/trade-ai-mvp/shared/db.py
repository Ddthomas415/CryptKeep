from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from shared.config import get_settings
from shared.logging import get_logger


class Base(DeclarativeBase):
    pass


_settings = get_settings("db")
_logger = get_logger("db", _settings.log_level)

engine = create_engine(_settings.sqlalchemy_database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as exc:
        _logger.warning("db_connectivity_failed", extra={"context": {"error": str(exc)}})
        return False
