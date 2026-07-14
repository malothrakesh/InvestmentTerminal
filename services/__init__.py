"""
Service layer.

The Service layer contains business rules and application workflows.

Repositories should never be accessed directly outside this layer.
"""

from .base_service import BaseService
from .exceptions import (
    BusinessRuleViolation,
    DuplicateEntityError,
   EntityNotFoundError,
    RepositoryFailure,
    ServiceError,
    ValidationError,
)

__all__ = [
    "BaseService",
    "ServiceError",
    "ValidationError",
    "DuplicateEntityError",
    "EntityNotFoundError",
    "BusinessRuleViolation",
    "RepositoryFailure",
]