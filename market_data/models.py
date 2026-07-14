from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(slots=True)
class MarketDataRecord:
    """
    Provider-independent OHLCV record.
    """

    symbol: str
    trade_date: datetime

    open: float
    high: float
    low: float
    close: float

    adjusted_close: float | None = None
    volume: int = 0

    timeframe: str = "1D"

    provider: str = ""


@dataclass(slots=True)
class StockMetadata:
    """
    Provider-independent security metadata.
    """

    symbol: str

    company_name: str

    asset_type: str = "EQUITY"

    exchange: str | None = None

    primary_exchange: str | None = None

    currency: str | None = None

    country: str | None = None

    sector: str | None = None

    industry: str | None = None

    timezone: str | None = None

    is_active: bool = True

    provider: str = ""

    
@dataclass(slots=True)
class SearchResult:
    """
    Symbol search result.
    """

    symbol: str

    name: str

    exchange: str | None = None

    currency: str | None = None


@dataclass(slots=True)
class HistoryRequest:
    """
    Request describing a historical download.
    """

    symbol: str

    start_date: datetime | None = None

    end_date: datetime | None = None

    period: str | None = None

    timeframe: str = "1D"

    adjusted: bool = True

    def __post_init__(self):
        using_period = self.period is not None
        using_dates = (
                self.start_date is not None
                or self.end_date is not None
        )

        if using_period and using_dates:
            raise ValueError(
                "Specify either period OR date range."
            )


@dataclass(slots=True)
class HistoryResponse:
    """
    Historical download response.
    """

    symbol: str

    records: list[MarketDataRecord] = field(default_factory=list)

    provider: str = ""

    downloaded_at: datetime = field(default_factory=datetime.utcnow)


@dataclass(slots=True)
class DownloadResult:
    """
    Generic provider download result.
    """

    success: bool

    provider: str

    message: str = ""

    data: Any = None

    record_count: int = 0

    duration_seconds: float = 0.0

@dataclass(slots=True)
class BatchDownloadResult:
    """
    Result of downloading multiple symbols.
    """

    provider: str

    successful: list[HistoryResponse]

    failed: dict[str, str]

    downloaded_at: datetime = field(default_factory=datetime.utcnow)