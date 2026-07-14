"""
Market data service.

Provides the public API used by the application for all market
data operations.
"""

from __future__ import annotations

from loguru import logger

from market_data.base_provider import BaseMarketDataProvider
from market_data.models import (
    BatchDownloadResult,
    HistoryRequest,
    HistoryResponse,
    MarketDataRecord,
    SearchResult,
    StockMetadata,
)
from market_data.provider_factory import ProviderFactory


class MarketDataService:
    """
    High-level market data service.

    This class delegates all operations to the configured provider
    while isolating the rest of the application from provider
    implementation details.
    """

    def __init__(
            self,
            provider: BaseMarketDataProvider | None = None,
    ) -> None:
        """
        Initialize the service.

        Args:
            provider:
                Optional provider implementation.
                If omitted, the default provider is created.
        """
        self._provider = provider or ProviderFactory.create()

        logger.info(
            "MarketDataService initialized using '{}'.",
            self._provider.provider_name,
        )

    @property
    def provider(self) -> BaseMarketDataProvider:
        """
        Return the active provider.
        """
        return self._provider

    def search_symbol(
        self,
        query: str,
    ) -> list[SearchResult]:
        """
        Search symbols.
        """
        return self._provider.search_symbol(query)

    def get_stock_metadata(
        self,
        symbol: str,
    ) -> StockMetadata:
        """
        Retrieve stock metadata.
        """
        return self._provider.get_stock_metadata(symbol)

    def download_latest(
        self,
        symbol: str,
    ) -> MarketDataRecord:
        """
        Retrieve latest market price.
        """
        return self._provider.download_latest(symbol)

    def download_history(
        self,
        request: HistoryRequest,
    ) -> HistoryResponse:
        """
        Download historical market data.
        """
        return self._provider.download_history(request)

    def download_multiple(
        self,
        symbols: list[str],
    ) -> BatchDownloadResult:
        """
        Download historical data for multiple symbols.
        """
        return self._provider.download_multiple(symbols)

    def health(self) -> bool:
        """
        Check provider health.
        """
        return self._provider.health()

    def shutdown(self) -> None:
        """
        Shutdown the service.
        """
        logger.info("Stopping MarketDataService.")

        self._provider.disconnect()

    def metadata(
        self,
        symbol: str,
    ) -> StockMetadata:
        """
        Retrieve stock metadata.

        This is a business-oriented alias for
        get_stock_metadata() and is intended for
        synchronization workflows.

        Args:
            symbol:
                Stock symbol.

        Returns:
            Stock metadata.
        """
        return self.get_stock_metadata(symbol)