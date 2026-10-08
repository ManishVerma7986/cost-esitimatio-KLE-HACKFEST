"""Database engine and session factory.

Uses SQLAlchemy 2.0 style with proper connection pooling.
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings


def _build_engine():
    settings = get_settings()
    url = settings.database_url
    if url.startswith("sqlite"):
        if "///" in url and not url.startswith("sqlite:///:memory:"):
            db_path = url.split("///")[-1]
            from pathlib import Path
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        return create_engine(
            url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    return create_engine(
        url,
        pool_pre_ping=True,  # Detect stale connections
        pool_size=5,
        max_overflow=10,
        echo=False,  # Never log SQL in production (may contain sensitive data)
    )


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:  # type: ignore[misc]
    """Yield a database session; close on exit.

    Usage as a FastAPI dependency::

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db  # type: ignore[misc]
    finally:
        db.close()
