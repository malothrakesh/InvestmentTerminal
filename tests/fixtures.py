import pytest

from repositories.price_repository import PriceRepository
from repositories.stock_repository import StockRepository
from services.price_service import PriceService
from services.stock_service import StockService

from tests.conftest import TestingSessionLocal


@pytest.fixture
def db():

    session = TestingSessionLocal()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def stock_repository(db):

    return StockRepository(db)


@pytest.fixture
def price_repository(db):

    return PriceRepository(db)


@pytest.fixture
def stock_service(stock_repository):

    return StockService(stock_repository)


@pytest.fixture
def price_service(
    price_repository,
    stock_repository,
):

    return PriceService(
        repository=price_repository,
        stock_repository=stock_repository,
    )