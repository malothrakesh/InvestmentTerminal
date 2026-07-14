"""
Generic SQLAlchemy repository.

This module provides a reusable generic repository implementing
common CRUD and transaction operations. Concrete repositories
should inherit from BaseRepository and implement entity-specific
queries only.
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import func, inspect, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from repositories.exceptions import (
    RepositoryError,
    RepositoryIntegrityError,
    RepositoryTransactionError,
)
from utils.logger import logger

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Generic repository for SQLAlchemy ORM models.

    Repositories are responsible only for persistence.
    Business logic belongs in the Service layer.
    """

    def __init__(
        self,
        session: Session,
        model: type[T],
    ) -> None:
        self.session = session
        self.model = model

        self.logger = logger.bind(
            layer="repository",
            repository=self.__class__.__name__,
            model=self.model.__name__,
        )

    # ======================================================
    # CREATE
    # ======================================================

    def create(self, entity: T) -> T:
        """
        Add a new entity to the current session.

        Args:
            entity: ORM entity.

        Returns:
            The added entity.
        """
        try:
            self.session.add(entity)
            self.session.flush()  # Assign PK immediately
            self.session.refresh(entity)

            self.logger.debug("Entity added to session.")

            return entity

        except IntegrityError as exc:
            raise RepositoryIntegrityError(str(exc)) from exc

        except SQLAlchemyError as exc:
            raise RepositoryError(str(exc)) from exc

    def bulk_create(
        self,
        entities: list[T],
    ) -> list[T]:
        """
        Add multiple entities to the current session.
        """
        try:
            self.session.add_all(entities)
            self.session.add_all(entities)

            self.session.flush()

            for entity in entities:
                self.session.refresh(entity)

            self.logger.debug(
                "Bulk added {} entities.",
                len(entities),
            )

            return entities

        except SQLAlchemyError as exc:
            raise RepositoryError(str(exc)) from exc

    # ======================================================
    # READ
    # ======================================================

    def get_by_id(
        self,
        entity_id: Any,
    ) -> T | None:
        """
        Retrieve entity by primary key.
        """
        return self.session.get(self.model, entity_id)

    def get_all(self) -> list[T]:
        """
        Return all entities.
        """
        stmt = select(self.model)

        return self.session.scalars(stmt).all()

    def first(self, stmt):
        """
        Return first scalar result.
        """
        return self.session.scalar(stmt)

    def paginate(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> list[T]:
        """
        Return paginated results.

        Args:
            page: Page number (1-based).
            page_size: Records per page.
        """
        offset = (page - 1) * page_size

        stmt = (
            select(self.model)
            .offset(offset)
            .limit(page_size)
        )

        return self.session.scalars(stmt).all()

    # ======================================================
    # UPDATE
    # ======================================================

    def update(
        self,
        entity: T,
    ) -> T:
        """
        Merge detached entity into current session.
        """
        try:
            merged = self.session.merge(entity)
            self.session.flush()
            self.session.refresh(merged)

            self.logger.debug("Entity merged.")

            return merged

        except SQLAlchemyError as exc:
            raise RepositoryError(str(exc)) from exc

    # ======================================================
    # DELETE
    # ======================================================

    def delete(
        self,
        entity: T,
    ) -> None:
        """
        Delete entity.
        """
        try:
            self.session.delete(entity)

            self.logger.debug("Entity deleted.")

        except SQLAlchemyError as exc:
            raise RepositoryError(str(exc)) from exc

    # ======================================================
    # EXISTS
    # ======================================================

    def exists(
        self,
        entity_id: Any,
    ) -> bool:
        """
        Check whether an entity exists by primary key.
        """
        mapper = inspect(self.model)

        primary_key = mapper.primary_key[0]

        stmt = (
            select(func.count())
            .select_from(self.model)
            .where(primary_key == entity_id)
        )

        count = self.session.scalar(stmt)

        return bool(count)

    # ======================================================
    # COUNT
    # ======================================================

    def count(self) -> int:
        """
        Return total entity count.
        """
        stmt = (
            select(func.count())
            .select_from(self.model)
        )

        value = self.session.scalar(stmt)

        return int(value or 0)

    # ======================================================
    # SESSION OPERATIONS
    # ======================================================

    def flush(self) -> None:
        """
        Flush pending changes.
        """
        self.session.flush()

    def refresh(
        self,
        entity: T,
    ) -> None:
        """
        Refresh entity from database.
        """
        self.session.refresh(entity)

    def merge(
        self,
        entity: T,
    ) -> T:
        """
        Merge entity into session.
        """
        return self.session.merge(entity)

    def detach(
        self,
        entity: T,
    ) -> None:
        """
        Detach entity from session.
        """
        self.session.expunge(entity)

    # ======================================================
    # TRANSACTION CONTROL
    # ======================================================

    def commit(self) -> None:
        """
        Commit current transaction.
        """
        try:
            self.session.commit()

            self.logger.debug("Transaction committed.")

        except SQLAlchemyError as exc:
            self.session.rollback()

            self.logger.exception(
                "Commit failed. Transaction rolled back."
            )

            raise RepositoryTransactionError(str(exc)) from exc

    def rollback(self) -> None:
        """
        Rollback current transaction.
        """
        self.session.rollback()

        self.logger.warning("Transaction rolled back.")

    # ======================================================
    # UTILITIES
    # ======================================================

    def close(self) -> None:
        """
        Close database session.
        """
        self.session.close()

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(model={self.model.__name__})"
        )