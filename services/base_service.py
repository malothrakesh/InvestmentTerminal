"""
Generic BaseService.

Implements reusable business-service functionality.

Responsibilities
----------------
* Validation
* Transaction management
* Exception translation
* Logging
* Repository injection
* Generic typing

Business logic belongs in derived services.
"""

from __future__ import annotations

from typing import Generic, TypeVar

from repositories.base_repository import BaseRepository
from repositories.exceptions import (
    DuplicateEntityError as RepoDuplicateEntityError,
)
from repositories.exceptions import (
    EntityNotFoundError as RepoEntityNotFoundError,
)
from repositories.exceptions import (
    RepositoryError,
    RepositoryIntegrityError,
)

from services.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryFailure,
)

from utils.logger import logger

TRepository = TypeVar("TRepository", bound=BaseRepository)


class BaseService(Generic[TRepository]):
    """
    Base class for every application service.
    """

    def __init__(self, repository: TRepository):

        self.repository = repository

        self.logger = logger.bind(
            layer="service",
            service=self.__class__.__name__,
        )

    # -----------------------------------------------------
    # Validation Hooks
    # -----------------------------------------------------

    def before_create(self, entity):
        """Hook executed before create."""

    def after_create(self, entity):
        """Hook executed after create."""

    def before_update(self, entity):
        """Hook executed before update."""

    def after_update(self, entity):
        """Hook executed after update."""

    def before_delete(self, entity):
        """Hook executed before delete."""

    def after_delete(self, entity):
        """Hook executed after delete."""

    # -----------------------------------------------------
    # Transactions
    # -----------------------------------------------------

    def commit(self):

        try:
            self.repository.session.commit()

        except Exception as exc:

            self.repository.session.rollback()

            self.logger.exception("Commit failed.")

            raise RepositoryFailure(str(exc)) from exc

    def rollback(self):

        self.repository.session.rollback()

    def flush(self):

        self.repository.session.flush()

    def refresh(self, entity):

        self.repository.session.refresh(entity)

    # -----------------------------------------------------
    # CRUD helpers
    # -----------------------------------------------------

    def get_by_id(self, entity_id):

        return self.repository.get_by_id(entity_id)

    def get_all(self):

        return self.repository.get_all()

    def delete(self, entity):

        try:

            self.before_delete(entity)

            self.repository.delete(entity)

            self.commit()

            self.after_delete(entity)

            return entity

        except RepositoryError as exc:

            self.rollback()

            raise RepositoryFailure(str(exc)) from exc

    # -----------------------------------------------------
    # Exception Translation
    # -----------------------------------------------------

    def translate(self, exc: Exception):

        if isinstance(exc, RepoDuplicateEntityError):
            raise DuplicateEntityError(str(exc)) from exc

        if isinstance(exc, RepoEntityNotFoundError):
            raise EntityNotFoundError(str(exc)) from exc

        if isinstance(exc, RepositoryIntegrityError):
            raise DuplicateEntityError(str(exc)) from exc

        if isinstance(exc, RepositoryError):
            raise RepositoryFailure(str(exc)) from exc

        raise exc