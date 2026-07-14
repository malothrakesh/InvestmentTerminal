"""
Tests for PriceService.
"""

from datetime import datetime

import pytest

from services.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    ValidationError,
)


@pytest.fixture
def stock(stock_service):
    return stock_service.create_stock(
        symbol="RELIANCE",
        name="Reliance Industries",
        exchange="NSE",
        currency="INR",
    )


def test_insert_price(price_service, stock):

    price = price_service.insert_price(
        stock_id=stock.id,
        trade_date=datetime(2025, 1, 1),
        timeframe="1D",
        open=100,
        high=110,
        low=95,
        close=105,
        adjusted_close=105,
        volume=1000000,
    )

    assert price.id is not None


def test_duplicate_candle(price_service, stock):

    kwargs = dict(
        stock_id=stock.id,
        trade_date=datetime(2025, 1, 1),
        timeframe="1D",
        open=100,
        high=110,
        low=95,
        close=105,
        adjusted_close=105,
        volume=1000000,
    )

    price_service.insert_price(**kwargs)

    with pytest.raises(DuplicateEntityError):
        price_service.insert_price(**kwargs)


def test_latest_price(price_service, stock):

    price_service.insert_price(
        stock_id=stock.id,
        trade_date=datetime(2025, 1, 1),
        timeframe="1D",
        open=100,
        high=110,
        low=95,
        close=105,
        adjusted_close=105,
        volume=100,
    )

    latest = price_service.latest_price(stock.id)

    assert latest.close == 105


def test_historical_prices(price_service, stock):

    for day in range(1, 4):

        price_service.insert_price(
            stock_id=stock.id,
            trade_date=datetime(2025, 1, day),
            timeframe="1D",
            open=100,
            high=110,
            low=95,
            close=100 + day,
            adjusted_close=100 + day,
            volume=1000,
        )

    prices = price_service.historical_prices(stock.id)

    assert len(prices) == 3


def test_invalid_timeframe(price_service, stock):

    with pytest.raises(ValidationError):

        price_service.insert_price(
            stock_id=stock.id,
            trade_date=datetime(2025, 1, 1),
            timeframe="10D",
            open=100,
            high=110,
            low=95,
            close=100,
            adjusted_close=100,
            volume=1000,
        )


def test_negative_volume(price_service, stock):

    with pytest.raises(ValidationError):

        price_service.insert_price(
            stock_id=stock.id,
            trade_date=datetime(2025, 1, 1),
            timeframe="1D",
            open=100,
            high=110,
            low=95,
            close=100,
            adjusted_close=100,
            volume=-1,
        )


def test_invalid_ohlc(price_service, stock):

    with pytest.raises(ValidationError):

        price_service.insert_price(
            stock_id=stock.id,
            trade_date=datetime(2025, 1, 1),
            timeframe="1D",
            open=100,
            high=90,
            low=80,
            close=95,
            adjusted_close=95,
            volume=1000,
        )


def test_missing_stock(price_service):

    with pytest.raises(EntityNotFoundError):

        price_service.insert_price(
            stock_id=99999,
            trade_date=datetime(2025, 1, 1),
            timeframe="1D",
            open=100,
            high=110,
            low=95,
            close=105,
            adjusted_close=105,
            volume=100,
        )


def test_first_last_available_date(price_service, stock):

    for day in (1, 2, 3):

        price_service.insert_price(
            stock_id=stock.id,
            trade_date=datetime(2025, 1, day),
            timeframe="1D",
            open=100,
            high=110,
            low=95,
            close=100,
            adjusted_close=100,
            volume=1000,
        )

    assert (
        price_service.first_available_date(stock.id)
        == datetime(2025, 1, 1)
    )

    assert (
        price_service.last_available_date(stock.id)
        == datetime(2025, 1, 3)
    )


def test_ohlc_series(price_service, stock):

    price_service.insert_price(
        stock_id=stock.id,
        trade_date=datetime(2025, 1, 1),
        timeframe="1D",
        open=100,
        high=110,
        low=95,
        close=105,
        adjusted_close=105,
        volume=100,
    )

    series = price_service.get_ohlc(stock.id)

    assert len(series) == 1


def test_volume_series(price_service, stock):

    price_service.insert_price(
        stock_id=stock.id,
        trade_date=datetime(2025, 1, 1),
        timeframe="1D",
        open=100,
        high=110,
        low=95,
        close=105,
        adjusted_close=105,
        volume=12345,
    )

    volume = price_service.get_volume_series(stock.id)

    assert volume[0][1] == 12345