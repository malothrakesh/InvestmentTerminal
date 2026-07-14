"""
Application bootstrap.
"""

from database.health import check_database_connection
from database.init_db import initialize_database
from database.seed import seed_database

from utils import logger


def startup() -> None:
    """
    Initialize the application.
    """

    logger.info("Starting Institutional Investing Terminal...")

    initialize_database()

    check_database_connection()

    seed_database()

    logger.success("Application initialized successfully.")