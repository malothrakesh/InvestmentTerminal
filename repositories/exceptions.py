"""
Repository layer exceptions.
"""


class RepositoryError(Exception):
    """Base repository exception."""


class EntityNotFoundError(RepositoryError):
    """Requested entity does not exist."""


class DuplicateEntityError(RepositoryError):
    """Duplicate entity exists."""


class RepositoryIntegrityError(RepositoryError):
    """Database integrity error."""


class RepositoryTransactionError(RepositoryError):
    """Transaction failed."""