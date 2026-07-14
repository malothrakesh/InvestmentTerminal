from __future__ import annotations

from abc import ABC
from abc import abstractmethod

from market_data.models import (
    DownloadResult,
    HistoryRequest,
    HistoryResponse,
    MarketDataRecord,
    SearchResult,
    StockMetadata,
    BatchDownloadResult,
)


class BaseMarketDataProvider(ABC):
    """
    Abstract interface implemented by every market data provider.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Provider identifier.
        """

    @abstractmethod
    def connect(self) -> None:
        """
        Establish provider connection.
        """

    @abstractmethod
    def disconnect(self) -> None:
        """
        Release provider resources.
        """

    @abstractmethod
    def health(self) -> bool:
        """
        Perform provider health check.
        """

    @abstractmethod
    def search_symbol(
        self,
        query: str,
    ) -> list[SearchResult]:
        """
        Search for matching symbols.
        """

    @abstractmethod
    def get_stock_metadata(
        self,
        symbol: str,
    ) -> StockMetadata:
        """
        Retrieve metadata for a symbol.
        """

    @abstractmethod
    def download_history(
        self,
        request: HistoryRequest,
    ) -> HistoryResponse:
        """
        Download historical OHLCV data.
        """

    @abstractmethod
    def download_latest(
        self,
        symbol: str,
    ) -> MarketDataRecord:
        """
        Download latest available price.
        """

    @abstractmethod
    def download_multiple(
        self,
        symbols: list[str],
    ) -> BatchDownloadResult:
        """
        Download multiple symbols.
        """

    @abstractmethod
    def supported_timeframes(self) -> set[str]:
        """
        Supported candle intervals.
        """

    @abstractmethod
    def supported_exchanges(self) -> set[str]:
        """
        Supported exchanges.
        """