from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.base import Base


TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    future=True,
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


def pytest_configure():
    """
    Create schema before tests.
    """
    Base.metadata.create_all(bind=engine)


def pytest_unconfigure(config):
    """
    Drop schema after tests.
    """
    Base.metadata.drop_all(bind=engine)


import pytest

from market_data.providers.yahoo_provider import YahooProvider


@pytest.fixture(scope="module")
def provider():
    provider = YahooProvider()
    provider.connect()

    yield provider

    provider.disconnect()