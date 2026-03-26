"""SQLAlchemy 2.x engine, session factory, and declarative base."""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

# SQLite requires check_same_thread=False for multi-threaded WSGI/ASGI servers
_connect_args = (
    {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
)

engine = create_engine(settings.database_url, connect_args=_connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base for all ORM models."""


def create_db_and_tables() -> None:
    """Create all database tables defined in models (idempotent).

    Must be called once at application startup, after all model modules
    have been imported so their metadata is registered.
    """
    import app.models  # noqa: F401 — registers models with Base.metadata

    Base.metadata.create_all(bind=engine)


def get_db() -> Session:
    """FastAPI dependency: yield a database session, close it on teardown.

    Yields:
        Session: A SQLAlchemy ORM session scoped to the current request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
