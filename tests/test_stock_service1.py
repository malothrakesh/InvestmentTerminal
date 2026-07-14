"""
Tests for StockService.
"""

import pytest

from services.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)


def test_create_stock(stock_service):

    stock = stock_service.create_stock(
        symbol="RELIANCE",
        name="Reliance Industries",
        sector="Energy",
        industry="Oil & Gas",
        exchange="NSE",
        currency="INR",
    )

    assert stock.id is not None
    assert stock.symbol == "RELIANCE"


def test_duplicate_stock(stock_service):

    stock_service.create_stock(
        symbol="TCS",
        name="TCS",
    )

    with pytest.raises(DuplicateEntityError):

        stock_service.create_stock(
            symbol="TCS",
            name="Duplicate",
        )


def test_invalid_symbol(stock_service):

    with pytest.raises(ValidationError):

        stock_service.create_stock(
            symbol="@@@",
            name="ABC",
        )


def test_blank_name(stock_service):

    with pytest.raises(ValidationError):

        stock_service.create_stock(
            symbol="ABC",
            name="   ",
        )


def test_get_by_symbol(stock_service):

    stock_service.create_stock(
        symbol="INFY",
        name="Infosys",
    )

    stock = stock_service.get_stock_by_symbol(
        "INFY"
    )

    assert stock.name == "Infosys"


def test_search(stock_service):

    stock_service.create_stock(
        symbol="SBIN",
        name="State Bank of India",
    )

    results = stock_service.search_stocks(
        "State"
    )

    assert len(results) == 1


def test_update(stock_service):

    stock = stock_service.create_stock(
        symbol="HDFC",
        name="Housing",
    )

    updated = stock_service.update_stock(
        stock.id,
        name="HDFC Bank",
    )

    assert updated.name == "HDFC Bank"


def test_delete(stock_service):

    stock = stock_service.create_stock(
        symbol="IOC",
        name="Indian Oil",
    )

    stock_service.delete_stock(
        stock.id
    )

    with pytest.raises(EntityNotFoundError):

        stock_service.get_stock_by_symbol(
            "IOC"
        )


def test_total(stock_service):

    stock_service.create_stock(
        symbol="LT",
        name="Larsen",
    )

    stock_service.create_stock(
        symbol="ITC",
        name="ITC",
    )

    assert stock_service.total_stocks() >= 2