"""
SQLAlchemy Declarative Base.

All ORM models must inherit from Base.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models.
    """

    pass