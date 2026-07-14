"""
Database health check utilities.
"""

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from .engine import engine
from .exceptions import DatabaseHealthCheckError


def check_database_connection() -> bool:
    """
    Verify that the configured database is reachable.

    Returns:
        bool: True if healthy.

    Raises:
        DatabaseHealthCheckError
    """

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return True

    except SQLAlchemyError as exc:
        raise DatabaseHealthCheckError(
            "Database health check failed."
        ) from exc