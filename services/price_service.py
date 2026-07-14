"""
Business service for Price.

Contains all business rules related to market price data.

Repositories are responsible only for persistence.
"""

from __future__ import annotations

from datetime import datetime
from typing import Iterable

from database.models import Price
from repositories.exceptions import (
    RepositoryError,
    RepositoryIntegrityError,
    RepositoryTransactionError,
)
from repositories.price_repository import PriceRepository
from repositories.stock_repository import StockRepository
from market_data.models import HistoryRequest
from market_data.service import MarketDataService

from services.base_service import BaseService
from services.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryFailure,
    ValidationError,
)


class PriceService(BaseService[PriceRepository]):
    """
    Business service responsible for market price operations.
    """

    SUPPORTED_TIMEFRAMES = {
        "1M",
        "5M",
        "15M",
        "30M",
        "1H",
        "4H",
        "1D",
        "1W",
        "1MO",
    }

    def __init__(
        self,
        repository: PriceRepository,
        stock_repository: StockRepository,
    ) -> None:

        super().__init__(repository)

        self.stock_repository = stock_repository

    # =====================================================
    # CREATE
    # =====================================================

    def insert_price(
        self,
        *,
        stock_id: int,
        trade_date: datetime,
        timeframe: str,
        open: float,
        high: float,
        low: float,
        close: float,
        adjusted_close: float | None = None,
        volume: int = 0,
    ) -> Price:
        """
        Insert a single OHLC candle.
        """

        timeframe = timeframe.upper()

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)
        self._validate_trade_date(trade_date)

        self._validate_ohlc(
            open,
            high,
            low,
            close,
        )

        self._validate_volume(volume)

        self._validate_duplicate(
            stock_id,
            trade_date,
            timeframe,
        )

        price = Price(
            stock_id=stock_id,
            trade_date=trade_date,
            timeframe=timeframe,
            open=open,
            high=high,
            low=low,
            close=close,
            adjusted_close=adjusted_close,
            volume=volume,
        )

        try:

            self.before_create(price)

            price = self.repository.create_price(price)

            self.commit()

            self.after_create(price)

            self.logger.info(
                "Inserted candle for stock {}.",
                stock_id,
            )

            return price

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Failed inserting price."
            )

            self.translate(exc)

    # =====================================================
    # BULK INSERT
    # =====================================================

    def bulk_insert_prices(
        self,
        prices: Iterable[Price],
    ) -> list[Price]:
        """
        Insert multiple candles in a single transaction.
        """

        validated: list[Price] = []

        for candle in prices:

            self._validate_stock(
                candle.stock_id
            )

            self._validate_timeframe(
                candle.timeframe
            )

            self._validate_trade_date(
                candle.trade_date
            )

            self._validate_ohlc(
                candle.open,
                candle.high,
                candle.low,
                candle.close,
            )

            self._validate_volume(
                candle.volume
            )

            self._validate_duplicate(
                candle.stock_id,
                candle.trade_date,
                candle.timeframe,
            )

            validated.append(candle)

        try:

            self.repository.bulk_insert(
                validated
            )

            self.commit()

            self.logger.info(
                "Inserted {} candles.",
                len(validated),
            )

            return validated

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Bulk insert failed."
            )

            self.translate(exc)

    # =====================================================
    # UPDATE
    # =====================================================

    def update_price(self, price_id: int, price: Price):
        """
        Update an existing candle.
        """

        self._validate_stock(
            price.stock_id
        )

        self._validate_timeframe(
            price.timeframe
        )

        self._validate_trade_date(
            price.trade_date
        )

        self._validate_ohlc(
            price.open,
            price.high,
            price.low,
            price.close,
        )

        self._validate_volume(
            price.volume
        )

        try:

            updated = self.repository.update_price(
                price
            )

            self.commit()

            self.logger.info(
                "Updated price id={}.",
                updated.id,
            )

            return updated

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Failed updating price."
            )

            self.translate(exc)

    # =====================================================
    # DELETE
    # =====================================================

    def delete_price(
        self,
        price: Price,
    ) -> None:
        """
        Delete a price record.
        """

        try:

            self.before_delete(price)

            self.repository.delete_price(
                price
            )

            self.commit()

            self.after_delete(price)

            self.logger.info(
                "Deleted price id={}.",
                price.id,
            )

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Failed deleting price."
            )

            self.translate(exc)

    # =====================================================
    # READ
    # =====================================================

    def latest_price(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> Price:

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        price = self.repository.latest_price(
            stock_id,
            timeframe,
        )

        if price is None:

            raise EntityNotFoundError(
                "Latest price not found."
            )

        return price

    def synchronize_history(
        self,
        market_data_service: MarketDataService,
        stock_id: int,
        symbol: str,
        timeframe: str = "1D",
        period: str = "1y",
    ) -> int:
        """
        Synchronize historical prices for a stock.

        Only candles not already present in the database
        are inserted.

        Args:
            market_data_service:
                Market data service.

            stock_id:
                Local stock identifier.

            symbol:
                Market symbol.

            timeframe:
                Candle interval.

            period:
                Yahoo download period.

        Returns:
            Number of inserted candles.
        """
        timeframe = timeframe.upper()

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        latest = self.repository.last_available_date(
            stock_id,
            timeframe,
        )

        request = HistoryRequest(
            symbol=symbol,
            timeframe=timeframe,
            period=period,
        )

        if latest is not None:
            request.start_date = latest + timedelta(days=1)

        history = market_data_service.download_history(
            request
        )

        if not history.records:
            return 0

        existing = self.repository.existing_trade_dates(
            stock_id,
            timeframe,
        )

        prices: list[Price] = []

        for record in history.records:

            if record.trade_date in existing:
                continue

            prices.append(
                Price(
                    stock_id=stock_id,
                    trade_date=record.trade_date,
                    timeframe=timeframe,
                    open=record.open,
                    high=record.high,
                    low=record.low,
                    close=record.close,
                    adjusted_close=record.adjusted_close,
                    volume=record.volume,
                )
            )

        if not prices:
            return 0

        self.bulk_insert_prices(prices)

        return len(prices)
    def historical_prices(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> list[Price]:

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.historical_prices(
            stock_id,
            timeframe,
        )

    def latest_n_prices(
        self,
        stock_id: int,
        limit: int = 100,
        timeframe: str = "1D",
    ) -> list[Price]:

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        if limit <= 0:
            raise ValidationError(
                "Limit must be greater than zero."
            )

        return self.repository.latest_n_prices(
            stock_id,
            limit,
            timeframe,
        )

    def prices_between(
        self,
        stock_id: int,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1D",
    ) -> list[Price]:

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        if start_date > end_date:
            raise ValidationError(
                "Start date cannot be after end date."
            )

        return self.repository.prices_between(
            stock_id,
            start_date,
            end_date,
            timeframe,
        )

    # =====================================================
    # SERIES
    # =====================================================

    def get_ohlc(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ):

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.get_ohlc(
            stock_id,
            timeframe,
        )

    def get_close_series(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ):

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.get_close_series(
            stock_id,
            timeframe,
        )

    def get_adjusted_close_series(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ):

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.get_adjusted_close_series(
            stock_id,
            timeframe,
        )

    def get_volume_series(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ):

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.get_volume_series(
            stock_id,
            timeframe,
        )

    # =====================================================
    # DATE HELPERS
    # =====================================================

    def first_available_date(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ):

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.first_available_date(
            stock_id,
            timeframe,
        )

    def last_available_date(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ):

        self._validate_stock(stock_id)
        self._validate_timeframe(timeframe)

        return self.repository.last_available_date(
            stock_id,
            timeframe,
        )

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_stock(
        self,
        stock_id: int,
    ) -> None:
        """
        Validate that the stock exists.
        """

        if not self.stock_repository.exists(stock_id):
            raise EntityNotFoundError(
                f"Stock id={stock_id} does not exist."
            )

    def _validate_timeframe(
        self,
        timeframe: str,
    ) -> None:
        """
        Validate supported timeframe.
        """

        timeframe = timeframe.upper()

        if timeframe not in self.SUPPORTED_TIMEFRAMES:
            raise ValidationError(
                f"Unsupported timeframe '{timeframe}'."
            )

    def _validate_trade_date(
        self,
        trade_date: datetime,
    ) -> None:
        """
        Validate trade date.
        """

        if trade_date is None:
            raise ValidationError(
                "Trade date is required."
            )

    def _validate_volume(
        self,
        volume: int,
    ) -> None:
        """
        Validate trading volume.
        """

        if volume < 0:
            raise ValidationError(
                "Volume cannot be negative."
            )

    def _validate_ohlc(
        self,
        open_price: float,
        high: float,
        low: float,
        close: float,
    ) -> None:
        """
        Validate OHLC values.
        """

        values = (
            open_price,
            high,
            low,
            close,
        )

        if any(v < 0 for v in values):
            raise ValidationError(
                "Prices cannot be negative."
            )

        if high < open_price:
            raise ValidationError(
                "High must be greater than or equal to Open."
            )

        if high < close:
            raise ValidationError(
                "High must be greater than or equal to Close."
            )

        if high < low:
            raise ValidationError(
                "High must be greater than or equal to Low."
            )

        if low > open_price:
            raise ValidationError(
                "Low must be less than or equal to Open."
            )

        if low > close:
            raise ValidationError(
                "Low must be less than or equal to Close."
            )

    def _validate_duplicate(
        self,
        stock_id: int,
        trade_date: datetime,
        timeframe: str,
    ) -> None:
        """
        Prevent duplicate candles.
        """

        if self.repository.candle_exists(
            stock_id,
            trade_date,
            timeframe,
        ):
            raise DuplicateEntityError(
                "Price candle already exists."
            )

    # =====================================================
    # SERVICE HOOKS
    # =====================================================

    def before_create(
        self,
        entity: Price,
    ) -> None:
        self.logger.debug(
            "Before inserting candle {} {}.",
            entity.stock_id,
            entity.trade_date,
        )

    def after_create(
        self,
        entity: Price,
    ) -> None:
        self.logger.debug(
            "After inserting candle {} {}.",
            entity.stock_id,
            entity.trade_date,
        )

    def before_delete(
        self,
        entity: Price,
    ) -> None:
        self.logger.debug(
            "Before deleting candle {}.",
            entity.id,
        )

    def after_delete(
        self,
        entity: Price,
    ) -> None:
        self.logger.debug(
            "After deleting candle {}.",
            entity.id,
        )

    def before_update(
        self,
        entity: Price,
    ) -> None:
        self.logger.debug(
            "Before updating candle {}.",
            entity.id,
        )

    def after_update(
        self,
        entity: Price,
    ) -> None:
        self.logger.debug(
            "After updating candle {}.",
            entity.id,
        )