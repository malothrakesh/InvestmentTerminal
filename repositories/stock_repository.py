"""
Repository for Stock entity.
"""

from __future__ import annotations

from sqlalchemy import func
from sqlalchemy import or_
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from database.models import Stock
from repositories.base_repository import BaseRepository
from database.enums import SecurityType


class StockRepository(BaseRepository[Stock]):
    """
    Repository responsible for Stock persistence.

    This repository contains ONLY database queries.

    Business logic must be implemented in the Service Layer.
    """

    def __init__(
        self,
        session: Session,
    ) -> None:

        super().__init__(
            session=session,
            model=Stock,
        )

    # =====================================================
    # CREATE
    # =====================================================

    def create_stock(
        self,
        stock: Stock,
    ) -> Stock:
        """
        Persist a Stock entity.
        """
        return self.create(stock)

    # =====================================================
    # READ
    # =====================================================

    def get_by_symbol(
        self,
        symbol: str,
    ) -> Stock | None:
        """
        Retrieve a stock by symbol.
        """
        stmt = (
            select(Stock)
            .where(
                func.upper(Stock.symbol) == symbol.upper()
            )
        )

        return self.first(stmt)

    def get_all_stocks(
        self,
    ) -> list[Stock]:
        """
        Return all stocks ordered by symbol.
        """
        stmt = (
            select(Stock)
            .order_by(Stock.symbol)
        )

        return self.session.scalars(stmt).all()

    def get_with_prices(
        self,
        stock_id: int,
    ) -> Stock | None:
        """
        Retrieve stock with all related prices.
        """

        stmt = (
            select(Stock)
            .options(
                selectinload(
                    Stock.prices
                )
            )
            .where(
                Stock.id == stock_id
            )
        )

        return self.first(stmt)


    def search_stocks(
        self,
        keyword: str,
        limit: int = 50,
    ) -> list[Stock]:
        """
        Search stocks by symbol or name.
        """

        keyword = keyword.strip()

        stmt = (
            select(Stock)
            .where(
                or_(
                    Stock.symbol.ilike(f"%{keyword}%"),
                    Stock.name.ilike(f"%{keyword}%"),
                    Stock.isin.ilike(f"%{keyword}%"),
                    Stock.figi.ilike(f"%{keyword}%"),
                )
            )
            .order_by(
                Stock.symbol
            )
            .limit(limit)
        )

        return self.session.scalars(stmt).all()

    def filter_by_sector(
        self,
        sector: str,
    ) -> list[Stock]:
        """
        Retrieve stocks by sector.
        """

        stmt = (
            select(Stock)
            .where(
                Stock.sector == sector
            )
            .order_by(
                Stock.symbol
            )
        )

        return self.session.scalars(stmt).all()

    def filter_by_industry(
        self,
        industry: str,
    ) -> list[Stock]:
        """
        Retrieve stocks by industry.
        """

        stmt = (
            select(Stock)
            .where(
                Stock.industry == industry
            )
            .order_by(
                Stock.symbol
            )
        )

        return self.session.scalars(stmt).all()

    def get_by_exchange(
        self,
        exchange: str,
    ) -> list[Stock]:
        """
        Retrieve stocks by exchange.
        """

        stmt = (
            select(Stock)
            .where(
                Stock.exchange == exchange
            )
            .order_by(
                Stock.symbol
            )
        )

        return self.session.scalars(stmt).all()

    def get_by_symbols(
        self,
        symbols: list[str],
    ) -> list[Stock]:
        """
        Retrieve multiple stocks by symbols.
        """

        normalized = [
            s.upper()
            for s in symbols
        ]

        stmt = (
            select(Stock)
            .where(
                func.upper(
                    Stock.symbol
                ).in_(normalized)
            )
            .order_by(
                Stock.symbol
            )
        )

        return self.session.scalars(stmt).all()

    # =====================================================
    # HELPERS
    # =====================================================

    def _get_by_identifier(
        self,
        field,
        value: str,
    ) -> Stock | None:
        """
        Retrieve a stock by a unique security identifier.
        """

        if not value:
            return None

        stmt = (
            select(Stock)
            .where(field == value.upper())
        )

        return self.first(stmt)

    def symbol_exists(
        self,
        symbol: str,
    ) -> bool:
        """
        Check whether symbol exists.
        """

        return (
            self.get_by_symbol(symbol)
            is not None
        )

    def get_by_isin(
        self,
        isin: str,
    ) -> Stock | None:
        """
        Retrieve a stock by ISIN.
        """

        return self._get_by_identifier(
            Stock.isin,
            isin,
        )


    def get_by_figi(
        self,
        figi: str,
    ) -> Stock | None:
        """
        Retrieve a stock by FIGI.
        """

        return self._get_by_identifier(
            Stock.figi,
            figi,
        )


    def get_by_cusip(
        self,
        cusip: str,
    ) -> Stock | None:
        """
        Retrieve a stock by CUSIP.
        """

        return self._get_by_identifier(
            Stock.cusip,
            cusip,
        )


    def get_by_sedol(
        self,
        sedol: str,
    ) -> Stock | None:
        """
        Retrieve a stock by SEDOL.
        """

        return self._get_by_identifier(
            Stock.sedol,
            sedol,
        )

    def symbol_exists_excluding_id(
            self,
            symbol: str,
            stock_id: int,
    ) -> bool:
        """
        Check whether a symbol exists excluding the given stock.
        """

        if not symbol:
            return False

        stmt = (
            select(Stock)
            .where(
                func.upper(Stock.symbol) == symbol.upper(),
                Stock.id != stock_id,
            )
        )

        return self.first(stmt) is not None

    def total_stocks(
        self,
    ) -> int:
        """
        Return total number of stocks.
        """

        return self.count()

    def get_by_asset_type(
        self,
        asset_type: SecurityType,
    ) -> list[Stock]:
        """
        Retrieve securities by asset type.
        """

        stmt = (
            select(Stock)
            .where(
                Stock.asset_type == asset_type,
            )
            .order_by(
                Stock.symbol,
            )
        )

        return self.session.scalars(stmt).all()


    def get_by_country(
        self,
        country: str,
    ) -> list[Stock]:
        """
        Retrieve securities by country.
        """

        stmt = (
            select(Stock)
            .where(
                func.upper(Stock.country) == country.upper(),
            )
            .order_by(
                Stock.symbol,
            )
        )

        return self.session.scalars(stmt).all()