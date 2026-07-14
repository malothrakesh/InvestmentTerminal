"""
Database Session Management.
"""

from collections.abc import Generator

from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from .engine import engine


SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session() -> Generator[Session, None, None]:
    """
    Dependency Injection compatible database session.

    Compatible with FastAPI:

        db: Session = Depends(get_session)
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.close()