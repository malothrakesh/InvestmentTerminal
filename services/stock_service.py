"""
Business service for Stock.

This module contains all business rules related to Stock entities.

Repositories are responsible only for persistence.
"""

from __future__ import annotations

import re

from database.models import Stock
from repositories.exceptions import (
    RepositoryError,
    RepositoryIntegrityError,
    RepositoryTransactionError,
)
from repositories.stock_repository import StockRepository

from services.base_service import BaseService
from market_data.service import MarketDataService
from services.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    RepositoryFailure,
    ValidationError,
)


class StockService(BaseService[StockRepository]):
    """
    Business service responsible for Stock operations.
    """

    SYMBOL_PATTERN = re.compile(
        r"^[A-Z][A-Z0-9._\-]{0,39}$"
    )

    def __init__(
        self,
        repository: StockRepository,
    ) -> None:
        super().__init__(repository)

    # ==========================================================
    # CREATE
    # ==========================================================

    def create_stock(
        self,
        *,
        symbol: str,
        name: str,
        sector: str | None = None,
        industry: str | None = None,
        exchange: str | None = None,
        currency: str | None = None,
        asset_type: SecurityType = SecurityType.EQUITY,
        primary_exchange: str | None = None,
        country: str | None = None,
        isin: str | None = None,
        cusip: str | None = None,
        sedol: str | None = None,
        figi: str | None = None,
        is_active: bool = True,
        ipo_date: date | None = None,
        delisted_date: date | None = None,
    ) -> Stock:
        """
        Create a new stock.
        """

        symbol = self._normalize_symbol(symbol)

        self._validate_symbol(symbol)
        self._validate_name(name)
        self._validate_duplicate(symbol)

        stock = Stock(
            symbol=symbol,
            name=name.strip(),
            sector=sector,
            industry=industry,
            exchange=exchange,
            currency=currency,
        )

        try:

            self.before_create(stock)

            stock = self.repository.create_stock(stock)

            self.commit()

            self.after_create(stock)

            self.logger.info(
                "Created stock '{}'.",
                stock.symbol,
            )

            return stock

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Failed creating stock '{}'.",
                symbol,
            )

            raise RepositoryFailure(str(exc)) from exc

    # ==========================================================
    # UPDATE
    # ==========================================================

    def update_stock(
        self,
        stock_id: int,
        *,
        symbol: str | None = None,
        name: str | None = None,
        sector: str | None = None,
        industry: str | None = None,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> Stock:
        """
        Update stock.
        """

        stock = self.get_stock(stock_id)

        if symbol is not None:

            symbol = self._normalize_symbol(symbol)

            self._validate_symbol(symbol)

            if (
                symbol != stock.symbol
                and self.repository.symbol_exists(symbol)
            ):
                raise DuplicateEntityError(
                    f"Stock '{symbol}' already exists."
                )

            stock.symbol = symbol
        if name is not None:

            self._validate_name(name)

            stock.name = name.strip()

        if sector is not None:
            stock.sector = sector

        if industry is not None:
            stock.industry = industry

        if exchange is not None:
            stock.exchange = exchange

        if currency is not None:
            stock.currency = currency

        try:

            self.before_update(stock)

            stock = self.repository.update(stock)

            self.commit()

            self.after_update(stock)

            self.logger.info(
                "Updated stock '{}'.",
                stock.symbol,
            )

            return stock

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Failed updating stock '{}'.",
                stock.symbol,
            )

            raise RepositoryFailure(str(exc)) from exc

    # ==========================================================
    # DELETE
    # ==========================================================

    def delete_stock(
        self,
        stock_id: int,
    ) -> None:
        """
        Delete stock.
        """

        stock = self.get_stock(stock_id)

        try:

            self.before_delete(stock)

            self.repository.delete(stock)

            self.commit()

            self.after_delete(stock)

            self.logger.info(
                "Deleted stock '{}'.",
                stock.symbol,
            )

        except (
            RepositoryIntegrityError,
            RepositoryTransactionError,
            RepositoryError,
        ) as exc:

            self.rollback()

            self.logger.exception(
                "Failed deleting stock '{}'.",
                stock.symbol,
            )

            raise RepositoryFailure(str(exc)) from exc

    # ==========================================================
    # GET
    # ==========================================================

    def get_stock(
        self,
        stock_id: int,
    ) -> Stock:

        stock = self.repository.get_by_id(stock_id)

        if stock is None:
            raise EntityNotFoundError(
                f"Stock id={stock_id} not found."
            )

        return stock

    def get_stock_by_symbol(
        self,
        symbol: str,
    ) -> Stock:

        symbol = self._normalize_symbol(symbol)

        stock = self.repository.get_by_symbol(symbol)

        if stock is None:
            raise EntityNotFoundError(
                f"Stock '{symbol}' not found."
            )

        return stock

    def synchronize_stock(
        self,
        market_data_service: MarketDataService,
        symbol: str,
    ) -> Stock:
        """
        Synchronize a stock with the market data provider.

        If the stock does not exist locally it will be created.
        If it already exists, changed metadata will be updated.

        Args:
            market_data_service:
                Market data service.

            symbol:
                Stock symbol.

        Returns:
            Synchronized Stock entity.
        """
        symbol = self._normalize_symbol(symbol)

        metadata = market_data_service.metadata(symbol)

        try:
            stock = self.get_stock_by_symbol(symbol)

        except EntityNotFoundError:

            stock = Stock(
                symbol=metadata.symbol,
                name=metadata.company_name,
                asset_type=metadata.asset_type,
                exchange=metadata.exchange,
                primary_exchange=metadata.primary_exchange,
                currency=metadata.currency,
                country=metadata.country,
                sector=metadata.sector,
                industry=metadata.industry,
                is_active=metadata.is_active,
            )

            try:
                self.before_create(stock)

                stock = self.repository.create_stock(stock)

                self.commit()

                self.after_create(stock)

                return stock

            except (
                    RepositoryIntegrityError,
                    RepositoryTransactionError,
                    RepositoryError,
            ) as exc:

                self.rollback()

                raise RepositoryFailure(str(exc)) from exc

        changed = (
                stock.name != metadata.company_name
                or stock.asset_type != metadata.asset_type
                or stock.exchange != metadata.exchange
                or stock.primary_exchange != metadata.primary_exchange
                or stock.currency != metadata.currency
                or stock.country != metadata.country
                or stock.sector != metadata.sector
                or stock.industry != metadata.industry
                or stock.is_active != metadata.is_active
        )

        if not changed:
            return stock

        stock.name = metadata.company_name
        stock.asset_type = metadata.asset_type
        stock.exchange = metadata.exchange
        stock.primary_exchange = metadata.primary_exchange
        stock.currency = metadata.currency
        stock.country = metadata.country
        stock.sector = metadata.sector
        stock.industry = metadata.industry
        stock.is_active = metadata.is_active

        try:
            self.before_update(stock)

            stock = self.repository.update(stock)

            self.commit()

            self.after_update(stock)

            return stock

        except (
                RepositoryIntegrityError,
                RepositoryTransactionError,
                RepositoryError,
        ) as exc:

            self.rollback()

            raise RepositoryFailure(str(exc)) from exc

    def get_all_stocks(self) -> list[Stock]:
        """
        Retrieve all stocks ordered by symbol.
        """
        return self.repository.get_all_stocks()

    def search_stocks(
        self,
        keyword: str,
        limit: int = 50,
    ) -> list[Stock]:
        """
        Search stocks by symbol or company name.
        """

        keyword = keyword.strip()

        if not keyword:
            raise ValidationError(
                "Search keyword cannot be empty."
            )

        return self.repository.search_stocks(
            keyword=keyword,
            limit=limit,
        )

    def filter_by_sector(
        self,
        sector: str,
    ) -> list[Stock]:
        """
        Retrieve stocks belonging to a sector.
        """

        sector = sector.strip()

        if not sector:
            raise ValidationError(
                "Sector cannot be empty."
            )

        return self.repository.filter_by_sector(
            sector
        )

    def filter_by_industry(
        self,
        industry: str,
    ) -> list[Stock]:
        """
        Retrieve stocks belonging to an industry.
        """

        industry = industry.strip()

        if not industry:
            raise ValidationError(
                "Industry cannot be empty."
            )

        return self.repository.filter_by_industry(
            industry
        )

    def get_by_exchange(
        self,
        exchange: str,
    ) -> list[Stock]:
        """
        Retrieve stocks by exchange.
        """

        exchange = exchange.strip().upper()

        if not exchange:
            raise ValidationError(
                "Exchange cannot be empty."
            )

        return self.repository.get_by_exchange(
            exchange
        )

    def get_multiple(
        self,
        symbols: list[str],
    ) -> list[Stock]:
        """
        Retrieve multiple stocks by symbols.
        """

        if not symbols:
            return []

        normalized = [
            self._normalize_symbol(symbol)
            for symbol in symbols
        ]

        return self.repository.get_by_symbols(
            normalized
        )

    def total_stocks(self) -> int:
        """
        Return total number of stocks.
        """

        return self.repository.total_stocks()

    # =====================================================
    # VALIDATION
    # =====================================================

    def _validate_symbol(
        self,
        symbol: str,
    ) -> None:
        """
        Validate stock symbol.
        """

        if not symbol:
            raise ValidationError(
                "Symbol cannot be empty."
            )

        if not self.SYMBOL_PATTERN.fullmatch(symbol):
            raise ValidationError(
                f"Invalid stock symbol '{symbol}'."
            )

    def _validate_name(
        self,
        name: str,
    ) -> None:
        """
        Validate company name.
        """

        if not name:
            raise ValidationError(
                "Company name cannot be empty."
            )

        if not name.strip():
            raise ValidationError(
                "Company name cannot be blank."
            )
        if len(name.strip()) < 2:
            raise ValidationError(
                "Company name is too short."
            )

    def _validate_duplicate(
            self,
            symbol: str,
    ) -> None:
        """
        Prevent duplicate stock symbols during creation.
        """

        if self.repository.symbol_exists(symbol):
            raise DuplicateEntityError(
                f"Stock '{symbol}' already exists."
            )

    # =====================================================
    # NORMALIZATION
    # =====================================================

    @staticmethod
    def _normalize_symbol(
        symbol: str,
    ) -> str:
        """
        Normalize stock symbol.

        Example:
            reliance  -> RELIANCE
            tcs.ns    -> TCS.NS
        """

        return symbol.strip().replace(" ", "").upper()


    # =====================================================
    # SERVICE HOOKS
    # =====================================================

    def before_create(
        self,
        entity: Stock,
    ) -> None:
        self.logger.debug(
            "Before create '{}'.",
            entity.symbol,
        )

    def after_create(
        self,
        entity: Stock,
    ) -> None:
        self.logger.debug(
            "After create '{}'.",
            entity.symbol,
        )

    def before_update(
        self,
        entity: Stock,
    ) -> None:
        self.logger.debug(
            "Before update '{}'.",
            entity.symbol,
        )

    def after_update(
        self,
        entity: Stock,
    ) -> None:
        self.logger.debug(
            "After update '{}'.",
            entity.symbol,
        )

    def before_delete(
        self,
        entity: Stock,
    ) -> None:
        self.logger.debug(
            "Before delete '{}'.",
            entity.symbol,
        )

    def after_delete(
        self,
        entity: Stock,
    ) -> None:
        self.logger.debug(
            "After delete '{}'.",
            entity.symbol,
        )