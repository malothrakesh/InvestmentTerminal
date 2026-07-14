"""
Repository for Price entity.

Contains persistence logic only.
Business rules belong in the Service Layer.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import desc
from sqlalchemy import select
from sqlalchemy.orm import Session

from database.models import Price
from repositories.base_repository import BaseRepository

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

class PriceRepository(BaseRepository[Price]):
    """
    Repository responsible for Price persistence.
    """

    def __init__(
        self,
        session: Session,
    ) -> None:

        super().__init__(
            session=session,
            model=Price,
        )

    # =====================================================
    # CREATE
    # =====================================================

    def create_price(
        self,
        price: Price,
    ) -> Price:
        """
        Insert a single price record.
        """
        return self.create(price)

    def bulk_insert(
        self,
        prices: list[Price],
    ) -> list[Price]:
        """
        Bulk insert price records.
        """
        return self.bulk_create(prices)

    # =====================================================
    # UPDATE
    # =====================================================

    def update_price(
        self,
        price: Price,
    ) -> Price:
        """
        Update an existing price.
        """
        return self.update(price)

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
        self.delete(price)

    # =====================================================
    # READ
    # =====================================================

    def latest_price(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> Price | None:
        """
        Return latest available candle.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(
                desc(Price.trade_date)
            )
            .limit(1)
        )

        return self.first(stmt)

    def candle_exists_excluding_id(
            self,
            price_id: int,
            stock_id: int,
            trade_date: datetime,
            timeframe: str,
    ) -> bool:
        """
        Check whether another candle already exists.
        """

        stmt = (
            select(Price)
            .where(
                Price.id != price_id,
                Price.stock_id == stock_id,
                Price.trade_date == trade_date,
                Price.timeframe == timeframe,
            )
        )

        return self.first(stmt) is not None

    def get_price(
        self,
        stock_id: int,
        trade_date: datetime,
        timeframe: str = "1D",
    ) -> Price | None:
        """
        Return a single candle.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
                Price.trade_date == trade_date,
                Price.timeframe == timeframe,
            )
        )

        return self.first(stmt)

    def historical_prices(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> list[Price]:
        """
        Return all historical prices.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(
                Price.trade_date
            )
        )

        return self.session.scalars(stmt).all()

    def latest_n_prices(
        self,
        stock_id: int,
        limit: int = 100,
        timeframe: str = "1D",
    ) -> list[Price]:
        """
        Return latest N candles.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(
                desc(Price.trade_date)
            )
            .limit(limit)
        )

        return self.session.scalars(stmt).all()

    def prices_between(
        self,
        stock_id: int,
        start_date: datetime,
        end_date: datetime,
        timeframe: str = "1D",
    ) -> list[Price]:
        """
        Return prices within a date range.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
                Price.trade_date >= start_date,
                Price.trade_date <= end_date,
            )
            .order_by(
                Price.trade_date
            )
        )

        return self.session.scalars(stmt).all()

    # =====================================================
    # EXISTENCE
    # =====================================================

    def candle_exists(
        self,
        stock_id: int,
        trade_date: datetime,
        timeframe: str = "1D",
    ) -> bool:
        """
        Check whether a candle exists.
        """

        return (
            self.get_price(
                stock_id,
                trade_date,
                timeframe,
            )
            is not None
        )

    # =====================================================
    # COUNTS
    # =====================================================

    def total_prices(
        self,
    ) -> int:
        """
        Total number of price records.
        """

        return self.count()

    # =====================================================
    # OHLC QUERIES
    # =====================================================

    def get_ohlc(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> list[tuple[datetime, float, float, float, float]]:
        """
        Return OHLC data ordered by trade date.
        """

        stmt = (
            select(
                Price.trade_date,
                Price.open,
                Price.high,
                Price.low,
                Price.close,
            )
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(Price.trade_date)
        )

        return list(self.session.execute(stmt).all())

    def get_close_series(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> list[tuple[datetime, float]]:
        """
        Return (trade_date, close) series.
        """

        stmt = (
            select(
                Price.trade_date,
                Price.close,
            )
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(Price.trade_date)
        )

        return list(self.session.execute(stmt).all())

    def get_adjusted_close_series(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> list[tuple[datetime, float | None]]:
        """
        Return adjusted close series.
        """

        stmt = (
            select(
                Price.trade_date,
                Price.adjusted_close,
            )
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(Price.trade_date)
        )

        return list(self.session.execute(stmt).all())

    # =====================================================
    # VOLUME
    # =====================================================

    def get_volume_series(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> list[tuple[datetime, int]]:
        """
        Return volume series.
        """

        stmt = (
            select(
                Price.trade_date,
                Price.volume,
            )
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(Price.trade_date)
        )

        return list(self.session.execute(stmt).all())

    # =====================================================
    # DATE HELPERS
    # =====================================================

    def first_available_date(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> datetime | None:
        """
        Return earliest available trade date.
        """

        stmt = (
            select(Price.trade_date)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(Price.trade_date.asc())
            .limit(1)
        )

        return self.session.scalar(stmt)

    def last_available_date(
        self,
        stock_id: int,
        timeframe: str = "1D",
    ) -> datetime | None:
        """
        Return latest available trade date.
        """

        stmt = (
            select(Price.trade_date)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
            .order_by(Price.trade_date.desc())
            .limit(1)
        )

        return self.session.scalar(stmt)

    # =====================================================
    # DELETE HELPERS
    # =====================================================

    def delete_before_date(
        self,
        stock_id: int,
        before_date: datetime,
        timeframe: str = "1D",
    ) -> int:
        """
        Delete all candles before a given date.

        Returns:
            Number of deleted rows.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
                Price.trade_date < before_date,
            )
        )

        rows = self.session.scalars(stmt).all()

        for row in rows:
            self.session.delete(row)

        return len(rows)

    def delete_by_stock(
        self,
        stock_id: int,
    ) -> int:
        """
        Delete all price records for a stock.

        Returns:
            Number of deleted rows.
        """

        stmt = (
            select(Price)
            .where(
                Price.stock_id == stock_id,
            )
        )

        rows = self.session.scalars(stmt).all()

        for row in rows:
            self.session.delete(row)

        return len(rows)

    def existing_trade_dates(
            self,
            stock_id: int,
            timeframe: str,
    ) -> set[datetime]:
        """
        Return existing trade dates.
        """

        stmt = (
            select(Price.trade_date)
            .where(
                Price.stock_id == stock_id,
                Price.timeframe == timeframe,
            )
        )

        return set(self.session.scalars(stmt).all())

