"""
Database Engine Configuration.
"""

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from config import settings


class DatabaseEngine:
    """
    Creates and manages the SQLAlchemy Engine.

    This design allows future support for PostgreSQL,
    MySQL, and async engines with minimal changes.
    """

    def __init__(self) -> None:

        self._engine: Engine = create_engine(
            settings.SQLALCHEMY_DATABASE_URL,

            echo=settings.DEBUG,

            future=True,

            pool_pre_ping=True,
        )

    @property
    def engine(self) -> Engine:
        """
        Return the SQLAlchemy engine.
        """
        return self._engine


database_engine = DatabaseEngine()

engine = database_engine.engine