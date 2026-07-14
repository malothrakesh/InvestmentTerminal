"""
Yahoo Finance market data provider.

This module implements the BaseMarketDataProvider interface using
Yahoo Finance via the yfinance package.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

import requests
import yfinance as yf
from loguru import logger
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import quote
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

from config import settings
from market_data.base_provider import BaseMarketDataProvider
from market_data.exceptions import (
    ConnectionError,
    DownloadError,
    InvalidProviderResponse,
    ProviderTimeout,
    SymbolNotFound,
    UnsupportedTimeframe,
)
from market_data.models import (
    BatchDownloadResult,
    DownloadResult,
    HistoryRequest,
    HistoryResponse,
    MarketDataRecord,
    SearchResult,
    StockMetadata,
)

_INTERVAL_MAP = {
    "1D": "1d",
    "5D": "5d",
    "1W": "1wk",
    "1M": "1mo",
    "3M": "3mo",
    "1H": "1h",
    "60M": "60m",
    "30M": "30m",
    "15M": "15m",
    "5M": "5m",
    "2M": "2m",
    "1MINS": "1m",
}



class YahooProvider(BaseMarketDataProvider):
    """
    Yahoo Finance implementation of the market data provider.

    This provider converts all Yahoo Finance responses into
    provider-independent domain models.
    """

    _SUPPORTED_TIMEFRAMES: set[str] = {
        "1m",
        "2m",
        "5m",
        "15m",
        "30m",
        "60m",
        "90m",
        "1h",
        "1d",
        "5d",
        "1wk",
        "1mo",
        "3mo",
    }

    def __init__(self) -> None:
        """Initialize the Yahoo provider."""
        self._session: requests.Session | None = None
        self._connected = False

    @property
    def provider_name(self) -> str:
        """Return provider name."""
        return "Yahoo Finance"

    ####################################################################
    # Connection
    ####################################################################

    def connect(self) -> None:
        """
        Initialize HTTP session.
        """
        if self._connected:
            return

        retry = Retry(
            total=settings.MARKET_DATA_RETRY_COUNT,
            connect=settings.MARKET_DATA_RETRY_COUNT,
            read=settings.MARKET_DATA_RETRY_COUNT,
            backoff_factor=0.5,
            status_forcelist=(
                429,
                500,
                502,
                503,
                504,
            ),
            allowed_methods=frozenset({"GET"}),
            raise_on_status=False,
        )

        adapter = HTTPAdapter(max_retries=retry)

        session = requests.Session()

        session.mount(
            "https://",
            adapter,
        )

        session.mount(
            "http://",
            adapter,
        )

        self._session = session
        self._connected = True

        logger.info(
            "{} connected.",
            self.provider_name,
        )

    def disconnect(self) -> None:
        """
        Close provider resources.
        """
        if self._session is not None:
            self._session.close()

        self._session = None
        self._connected = False

        logger.info(
            "{} disconnected.",
            self.provider_name,
        )

    ####################################################################
    # Internal helpers
    ####################################################################

    def _require_connection(self) -> None:
        """
        Ensure provider is connected.
        """
        if not self._connected:
            self.connect()

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """
        Normalize ticker symbol.
        """
        symbol = symbol.strip().upper()

        if not symbol:
            raise SymbolNotFound(
                "Ticker symbol cannot be empty."
            )

        return symbol

    def _search_symbols(
            self,
            query: str,
    ) -> list[dict[str, Any]]:
        """
        Search Yahoo Finance symbols.

        Args:
            query:
                Search query.

        Returns:
            Raw Yahoo search results.
        """
        self._require_connection()

        url = (
            "https://query2.finance.yahoo.com/v1/finance/search"
            f"?q={quote(query)}"
            "&quotesCount=20"
            "&newsCount=0"
        )

        response = self._session.get(
            url,
            timeout=settings.MARKET_DATA_TIMEOUT,
        )

        response.raise_for_status()

        payload = response.json()

        return payload.get("quotes", [])

    @staticmethod
    def _safe_float(value: Any) -> float | None:
        """
        Safely convert value to float.
        """
        if value is None:
            return None

        try:
            if value != value:
                return None

            return float(value)

        except Exception:
            return None

    @staticmethod
    def _safe_int(value: Any) -> int:
        """
        Safely convert value to integer.
        """
        if value is None:
            return 0

        try:
            if value != value:
                return 0

            return int(value)

        except Exception:
            return 0

    @staticmethod
    def _ensure_datetime(value: Any) -> datetime:
        """
        Convert pandas timestamp into UTC datetime.
        """
        if isinstance(value, datetime):
            dt = value
        else:
            dt = value.to_pydatetime()

        if dt.tzinfo is None:
            return dt.replace(tzinfo=UTC)

        return dt.astimezone(UTC)

    def _ticker(
        self,
        symbol: str,
    ) -> yf.Ticker:
        """
        Create Yahoo ticker object.
        """
        self._require_connection()

        return yf.Ticker(symbol)

    def _translate_exception(
        self,
        symbol: str,
        exc: Exception,
    ) -> None:
        """
        Translate provider exceptions.
        """
        logger.exception(
            "Yahoo Finance request failed for {}",
            symbol,
        )

        if isinstance(exc, requests.exceptions.Timeout):
            raise ProviderTimeout(
                f"Timeout downloading '{symbol}'."
            ) from exc

        if isinstance(
            exc,
            requests.exceptions.ConnectionError,
        ):
            raise ConnectionError(
                f"Connection failed for '{symbol}'."
            ) from exc

        message = str(exc).lower()

        if (
            "no timezone found" in message
            or "404" in message
            or "not found" in message
        ):
            raise SymbolNotFound(symbol) from exc

        import traceback

        traceback.print_exc()

        raise

    ####################################################################
    # Conversion helpers
    ####################################################################

    def _history_to_records(
        self,
        dataframe: Any,
        symbol: str,
        timeframe: str,
    ) -> list[MarketDataRecord]:
        """
        Convert a Yahoo Finance DataFrame into MarketDataRecord objects.

        Args:
            dataframe:
                DataFrame returned by yfinance.

            symbol:
                Stock ticker.

            timeframe:
                Candle interval.

        Returns:
            List of MarketDataRecord objects.

        Raises:
            InvalidProviderResponse:
                If the returned data cannot be parsed.
        """
        records: list[MarketDataRecord] = []

        if dataframe is None or dataframe.empty:
            return records

        try:
            for trade_date, row in dataframe.iterrows():
                records.append(
                    MarketDataRecord(
                        symbol=symbol,
                        trade_date=self._ensure_datetime(trade_date),
                        open=self._safe_float(row.get("Open")) or 0.0,
                        high=self._safe_float(row.get("High")) or 0.0,
                        low=self._safe_float(row.get("Low")) or 0.0,
                        close=self._safe_float(row.get("Close")) or 0.0,
                        adjusted_close=self._safe_float(
                            row.get(
                                "Adj Close",
                                row.get("Close"),
                            )
                        ),
                        volume=self._safe_int(
                            row.get("Volume")
                        ),
                        timeframe=timeframe,
                        provider=self.provider_name,
                    )
                )

            return records

        except Exception as exc:
            raise InvalidProviderResponse(
                "Unable to convert Yahoo Finance response."
            ) from exc

    @staticmethod
    def _safe_string(value: Any) -> str | None:
        """
        Safely convert provider values to strings.
        """

        if value is None:
            return None

        text = str(value).strip()

        return text or None



    def _build_metadata(
        self,
        symbol: str,
        info: dict[str, Any],
    ) -> StockMetadata:
        """
        Convert Yahoo Finance metadata into StockMetadata.
        """

        quote_type = (
            self._safe_string(info.get("quoteType"))
            or "EQUITY"
        ).upper()

        return StockMetadata(
            symbol=symbol,

            company_name=(
                self._safe_string(info.get("longName"))
                or self._safe_string(info.get("shortName"))
                or symbol
            ),

            asset_type=quote_type,

            exchange=self._safe_string(
                info.get("exchange")
            ),

            primary_exchange=self._safe_string(
                info.get("fullExchangeName")
            ),

            currency=self._safe_string(
                info.get("currency")
            ),

            country=self._safe_string(
                info.get("country")
            ),

            sector=self._safe_string(
                info.get("sector")
            ),

            industry=self._safe_string(
                info.get("industry")
            ),

            timezone=(
                self._safe_string(info.get("timeZoneFullName"))
                or self._safe_string(
                    info.get("exchangeTimezoneName")
                )
            ),

            is_active=True,

            provider=self.provider_name,
        )



    ####################################################################
    # Interface implementation
    ####################################################################


    def health(self) -> bool:
        """
        Check whether the provider is operational.
        """
        try:
            self.download_history(
                HistoryRequest(
                    symbol="MSFT",
                    period="5d",
                    timeframe="1d",
                )
            )
            return True

        except Exception:
            logger.exception("Yahoo Finance health check failed.")
            return False


    def search_symbol(
        self,
        query: str,
    ) -> list[SearchResult]:
        """
        Search for matching ticker symbols.

        Args:
            query:
                Search text.

        Returns:
            List of matching symbols.
        """
        query = query.strip()

        if not query:
            return []

        self._require_connection()

        logger.info(
            "Searching Yahoo Finance for '{}'.",
            query,
        )

        try:
            quotes = self._search_symbols(query)

            results: list[SearchResult] = []

            for quote in quotes:
                symbol = quote.get("symbol")

                if not symbol:
                    continue

                results.append(
                    SearchResult(
                        symbol=symbol,
                        name=quote.get("shortname")
                             or quote.get("longname")
                             or symbol,
                        exchange=quote.get("exchange"),
                        currency=quote.get("currency"),
                    )
                )

            return results

        except requests.exceptions.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                logger.warning(
                    "Yahoo search API rate limited. Falling back to direct symbol lookup."
                )

                try:
                    metadata = self.get_stock_metadata(query.upper())

                    return [
                        SearchResult(
                            symbol=metadata.symbol,
                            name=metadata.company_name,
                            exchange=metadata.exchange,
                            currency=metadata.currency,
                        )
                    ]

                except Exception:
                    return []

            raise DownloadError(
                "Yahoo Finance symbol search failed."
            ) from exc

        except Exception as exc:
            raise DownloadError(
                "Yahoo Finance symbol search failed."
            ) from exc

    def get_stock_metadata(
        self,
        symbol: str,
    ) -> StockMetadata:
        """
        Retrieve metadata for a stock.

        Args:
            symbol:
                Stock ticker.

        Returns:
            StockMetadata.
        """
        symbol = self._normalize_symbol(symbol)

        logger.info(
            "Retrieving metadata for {}.",
            symbol,
        )

        try:
            ticker = self._ticker(symbol)

            info = ticker.info

            if not info:
                raise SymbolNotFound(symbol)

            metadata = self._build_metadata(
                symbol=symbol,
                info=info,
            )

            logger.debug(
                "Metadata retrieved for {}.",
                symbol,
            )

            return metadata

        except Exception as exc:
            self._translate_exception(symbol, exc)

    def download_history(
        self,
        request: HistoryRequest,
    ) -> HistoryResponse:
        """
        Download historical OHLCV data.

        Args:
            request:
                History download request.

        Returns:
            Historical market data.

        Raises:
            UnsupportedTimeframe:
                If the requested timeframe is unsupported.
        """
        symbol = self._normalize_symbol(request.symbol)


        timeframe = _INTERVAL_MAP.get(request.timeframe.upper())

        if timeframe is None:
            raise UnsupportedTimeframe(f"Unsupported timeframe '{request.timeframe}'."
            )

        if timeframe not in self._SUPPORTED_TIMEFRAMES:
            raise UnsupportedTimeframe(
                f"Unsupported timeframe '{request.timeframe}'."
            )

        logger.info(
            "Downloading history for {} ({})",
            symbol,
            timeframe,
        )

        start_time = time.perf_counter()

        try:
            ticker = self._ticker(symbol)

            dataframe = ticker.history(
                start=request.start_date,
                end=request.end_date,
                period=request.period,
                interval=timeframe,
                auto_adjust=request.adjusted,
                actions=False,
                prepost=False,
            )

            if dataframe.empty:
                raise SymbolNotFound(symbol)

            records = self._history_to_records(
                dataframe=dataframe,
                symbol=symbol,
                timeframe=request.timeframe,
            )

            elapsed = time.perf_counter() - start_time

            logger.info(
                "Downloaded {} candles for {} in {:.2f}s",
                len(records),
                symbol,
                elapsed,
            )

            return HistoryResponse(
                symbol=symbol,
                records=records,
                provider=self.provider_name,
            )

        except Exception as exc:
            self._translate_exception(symbol, exc)

    def download_latest(
        self,
        symbol: str,
    ) -> MarketDataRecord:
        """
        Download the latest available market price.

        Args:
            symbol:
                Stock ticker.

        Returns:
            Latest MarketDataRecord.
        """
        request = HistoryRequest(
            symbol=symbol,
            period="5d",
            timeframe="1d",
            adjusted=True,
        )

        response = self.download_history(request)

        if not response.records:
            raise SymbolNotFound(symbol)

        return response.records[-1]

    def download_multiple(
        self,
        symbols: list[str],
    ) -> BatchDownloadResult:
        """
        Download historical data for multiple symbols.

        Args:
            symbols:
                Symbols to download.

        Returns:
            BatchDownloadResult.
        """
        successful: list[HistoryResponse] = []
        failed: dict[str, str] = {}

        max_workers = min(8, len(symbols))

        with ThreadPoolExecutor(
                max_workers=max_workers,
        ) as executor:

            futures = {
                executor.submit(
                    self.download_history,
                    HistoryRequest(
                        symbol=symbol,
                        period="1mo",
                        timeframe="1d",
                        adjusted=True,
                    ),
                ): symbol
                for symbol in symbols
            }

            for future in as_completed(futures):

                symbol = futures[future]

                try:

                    successful.append(
                        future.result()
                    )

                except Exception as exc:

                    failed[symbol] = str(exc)

                    logger.warning(
                        "{} failed: {}",
                        symbol,
                        exc,
                    )

        return BatchDownloadResult(
            provider=self.provider_name,
            successful=successful,
            failed=failed,
        )

    def supported_timeframes(self) -> set[str]:
        """
        Return supported Yahoo Finance intervals.

        Returns:
            Supported timeframe strings.
        """
        return set(self._SUPPORTED_TIMEFRAMES)

    def supported_exchanges(self) -> set[str]:
        """
        Return supported exchanges.

        Yahoo Finance supports thousands of exchanges worldwide,
        therefore exchange filtering is not enforced by the provider.

        Returns:
            Empty set.
        """
        return set()