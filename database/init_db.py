"""
Database initialization.
"""

from database.base import Base
from database.engine import engine

# IMPORTANT: Import models so SQLAlchemy registers them.
import database.models  # noqa: F401


def init_db() -> None:
    """
    Recreate the database schema.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    print("Database schema created successfully.")