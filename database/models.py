from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from database.enums import SecurityType
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Stock(Base):
    """
    Master table containing stock metadata.
    """

    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    symbol: Mapped[str] = mapped_column(
        String(40),
        unique=True,
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    asset_type: Mapped[SecurityType] = mapped_column(
        Enum(SecurityType),
        nullable=False,
        default=SecurityType.EQUITY,
    )

    primary_exchange: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    country: Mapped[str | None] = mapped_column(
        String(2),
        nullable=True,
    )

    isin: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    cusip: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    sedol: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    figi: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    ipo_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    delisted_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    sector: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    industry: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    exchange: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    currency: Mapped[str | None] = mapped_column(
        String(10),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    prices: Mapped[list["Price"]] = relationship(
        back_populates="stock",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Stock(symbol='{self.symbol}')>"


class Price(Base):
    """
    OHLCV price data.
    """

    __tablename__ = "prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    stock_id: Mapped[int] = mapped_column(
        ForeignKey("stocks.id", ondelete="CASCADE"),
        nullable=False,
    )

    trade_date: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    timeframe: Mapped[str] = mapped_column(
        String(10),
        default="1D",
        nullable=False,
        index=True,
    )

    open: Mapped[float] = mapped_column(Float, nullable=False)

    high: Mapped[float] = mapped_column(Float, nullable=False)

    low: Mapped[float] = mapped_column(Float, nullable=False)

    close: Mapped[float] = mapped_column(Float, nullable=False)

    adjusted_close: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    volume: Mapped[int] = mapped_column(
        BigInteger,
        default=0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    stock: Mapped["Stock"] = relationship(
        back_populates="prices",
    )

    __table_args__ = (
        Index(
            "ix_price_lookup",
            "stock_id",
            "timeframe",
            "trade_date",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Price(stock_id={self.stock_id}, "
            f"timeframe='{self.timeframe}', "
            f"trade_date='{self.trade_date}')>"
        )