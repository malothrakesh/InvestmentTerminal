"""
Custom database exceptions.
"""


class DatabaseError(Exception):
    """
    Base database exception.
    """

    pass


class DatabaseConnectionError(DatabaseError):
    """
    Raised when a database connection cannot be established.
    """

    pass


class DatabaseInitializationError(DatabaseError):
    """
    Raised when database initialization fails.
    """

    pass


class DatabaseHealthCheckError(DatabaseError):
    """
    Raised when database health check fails.
    """

    pass