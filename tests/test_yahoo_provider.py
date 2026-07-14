"""
Tests for YahooProvider.
"""

from __future__ import annotations

import pytest

from market_data.exceptions import (
    SymbolNotFound,
    UnsupportedTimeframe,
)
from market_data.models import HistoryRequest
from market_data.providers.yahoo_provider import YahooProvider


@pytest.fixture(scope="module")
def provider() -> YahooProvider:
    """
    Create a connected provider instance.
    """
    provider = YahooProvider()
    provider.connect()

    yield provider

    provider.disconnect()


# ---------------------------------------------------------------------
# Provider
# ---------------------------------------------------------------------

def test_provider_name(provider: YahooProvider) -> None:
    assert provider.provider_name == "Yahoo Finance"


def test_health(provider: YahooProvider) -> None:
    assert provider.health() is True


# ---------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------

def test_search_symbol(provider: YahooProvider) -> None:

    results = provider.search_symbol("MSFT")

    assert isinstance(results, list)
    assert len(results) > 0

    assert len(results) >= 1
    assert results[0].symbol == "MSFT"


# ---------------------------------------------------------------------
# Metadata
# ---------------------------------------------------------------------

def test_get_metadata(provider: YahooProvider) -> None:
    metadata = provider.get_stock_metadata("MSFT")

    assert metadata.symbol == "MSFT"
    assert metadata.company_name != ""
    assert metadata.provider == provider.provider_name


# ---------------------------------------------------------------------
# Latest Quote
# ---------------------------------------------------------------------

def test_download_latest(provider: YahooProvider) -> None:
    quote = provider.download_latest("MSFT")

    assert quote.symbol == "MSFT"

    assert quote.open > 0
    assert quote.high > 0
    assert quote.low > 0
    assert quote.close > 0

    assert quote.volume >= 0


# ---------------------------------------------------------------------
# History
# ---------------------------------------------------------------------

def test_download_history(provider: YahooProvider) -> None:
    request = HistoryRequest(
        symbol="MSFT",
        period="1mo",
        timeframe="1d",
    )

    history = provider.download_history(request)

    assert history.symbol == "MSFT"
    assert history.provider == provider.provider_name

    assert len(history.records) > 0


def test_history_record_types(provider: YahooProvider) -> None:
    request = HistoryRequest(
        symbol="AAPL",
        period="5d",
    )

    history = provider.download_history(request)

    record = history.records[0]

    assert isinstance(record.open, float)
    assert isinstance(record.high, float)
    assert isinstance(record.low, float)
    assert isinstance(record.close, float)
    assert isinstance(record.volume, int)


# ---------------------------------------------------------------------
# Batch
# ---------------------------------------------------------------------

def test_download_multiple(provider: YahooProvider) -> None:
    result = provider.download_multiple(
        [
            "MSFT",
            "AAPL",
            "GOOG",
        ]
    )

    assert len(result.successful) == 3
    assert result.failed == {}


# ---------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------

def test_invalid_symbol(provider: YahooProvider) -> None:
    with pytest.raises(SymbolNotFound):
        provider.download_latest(
            "THIS_SYMBOL_DOES_NOT_EXIST_123456"
        )


def test_invalid_timeframe(provider: YahooProvider) -> None:
    request = HistoryRequest(
        symbol="MSFT",
        period="1mo",
        timeframe="17h",
    )

    with pytest.raises(UnsupportedTimeframe):
        provider.download_history(request)


# ---------------------------------------------------------------------
# Supported Values
# ---------------------------------------------------------------------

def test_supported_timeframes(provider: YahooProvider) -> None:
    intervals = provider.supported_timeframes()

    assert "1d" in intervals
    assert "1wk" in intervals
    assert len(intervals) > 0


def test_supported_exchanges(provider: YahooProvider) -> None:
    exchanges = provider.supported_exchanges()

    assert isinstance(exchanges, set)


# ---------------------------------------------------------------------
# Reconnect
# ---------------------------------------------------------------------

def test_reconnect() -> None:
    provider = YahooProvider()

    provider.connect()
    provider.disconnect()
    provider.connect()

    quote = provider.download_latest("MSFT")

    assert quote.close > 0

    provider.disconnect()