"""
Service layer exceptions.

Repositories raise persistence exceptions.

Services translate them into domain-friendly exceptions.
"""


class ServiceError(Exception):
    """Base Service exception."""


class ValidationError(ServiceError):
    """Raised when validation fails."""


class DuplicateEntityError(ServiceError):
    """Raised when entity already exists."""


class EntityNotFoundError(ServiceError):
    """Raised when entity cannot be found."""


class BusinessRuleViolation(ServiceError):
    """Raised when business rules are violated."""


class RepositoryFailure(ServiceError):
    """Raised when repository operations fail."""