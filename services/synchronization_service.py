"""
Application service responsible for market data synchronization.
"""

from __future__ import annotations

from loguru import logger

from market_data.service import MarketDataService
from services.price_service import PriceService
from services.stock_service import StockService

from datetime import datetime

from market_data.sync_models import SynchronizationResult
from services.exceptions import EntityNotFoundError


class SynchronizationService:
    """
    Coordinates synchronization between the market
    data provider and local database.

    This service contains workflow orchestration only.

    Business rules belong in StockService and PriceService.
    """

    def __init__(
        self,
        stock_service: StockService,
        price_service: PriceService,
        market_data_service: MarketDataService,
    ) -> None:
        self._stock_service = stock_service
        self._price_service = price_service
        self._market_data_service = market_data_service

        logger.info(
            "SynchronizationService initialized."
        )

    def synchronize_symbol(
        self,
        symbol: str,
        *,
        period: str = "1y",
        timeframe: str = "1D",
    ) -> SynchronizationResult:
        """
        Synchronize a single stock and its historical prices.

        The workflow performs:

        1. Synchronize stock metadata.
        2. Synchronize historical prices.
        3. Return a synchronization summary.

        Args:
            symbol:
                Stock symbol.

            period:
                History period.

            timeframe:
                Candle interval.

        Returns:
            SynchronizationResult.
        """
        started = datetime.utcnow()

        logger.info(
            "Synchronizing '{}'.",
            symbol,
        )

        created = False
        updated = False

        try:
            #
            # Does the stock already exist?
            #
            try:
                existing = self._stock_service.get_stock_by_symbol(
                    symbol
                )

                stock_before = (
                    existing.name,
                    existing.sector,
                    existing.industry,
                    existing.exchange,
                    existing.currency,
                )

            except EntityNotFoundError:

                existing = None
                stock_before = None

            #
            # Synchronize metadata.
            #
            stock = self._stock_service.synchronize_stock(
                self._market_data_service,
                symbol,
            )

            if existing is None:

                created = True

            else:

                stock_after = (
                    stock.name,
                    stock.sector,
                    stock.industry,
                    stock.exchange,
                    stock.currency,
                )

                updated = stock_before != stock_after

            #
            # Synchronize history.
            #
            inserted = self._price_service.synchronize_history(
                market_data_service=self._market_data_service,
                stock_id=stock.id,
                symbol=stock.symbol,
                timeframe=timeframe,
                period=period,
            )

            finished = datetime.utcnow()

            return SynchronizationResult(
                symbol=stock.symbol,
                created_stock=created,
                updated_stock=updated,
                downloaded_records=inserted,
                inserted_records=inserted,
                skipped_records=0,
                started_at=started,
                finished_at=finished,
                elapsed_seconds=(
                    finished - started
                ).total_seconds(),
                provider=self._market_data_service.provider.provider_name,
                success=True,
                message="Synchronization completed successfully.",
            )

        except Exception as exc:

            finished = datetime.utcnow()

            logger.exception(
                "Synchronization failed for '{}'.",
                symbol,
            )

            return SynchronizationResult(
                symbol=symbol,
                started_at=started,
                finished_at=finished,
                elapsed_seconds=(
                    finished - started
                ).total_seconds(),
                provider=self._market_data_service.provider.provider_name,
                success=False,
                message=str(exc),
            )

    def synchronize_symbols(
        self,
        symbols: list[str],
        *,
        period: str = "1y",
        timeframe: str = "1D",
        continue_on_error: bool = True,
    ) -> list[SynchronizationResult]:
        """
        Synchronize multiple symbols.

        Args:
            symbols:
                Symbols to synchronize.

            period:
                Historical period.

            timeframe:
                Candle interval.

            continue_on_error:
                Continue processing remaining symbols if one fails.

        Returns:
            List of synchronization results.
        """
        if not symbols:
            return []

        logger.info(
            "Starting synchronization for {} symbols.",
            len(symbols),
        )

        results: list[SynchronizationResult] = []

        for symbol in symbols:

            try:

                result = self.synchronize_symbol(
                    symbol=symbol,
                    period=period,
                    timeframe=timeframe,
                )

                results.append(result)

            except Exception:

                logger.exception(
                    "Synchronization failed for '{}'.",
                    symbol,
                )

                if not continue_on_error:
                    raise

        logger.info(
            "Completed synchronization of {} symbols.",
            len(results),
        )

        return results

    def synchronization_summary(
        self,
        results: list[SynchronizationResult],
    ) -> dict[str, int]:
        """
        Build a summary for a synchronization batch.

        Args:
            results:
                Synchronization results.

        Returns:
            Summary statistics.
        """
        successful = sum(
            1
            for result in results
            if result.success
        )

        failed = len(results) - successful

        created = sum(
            1
            for result in results
            if result.created_stock
        )

        updated = sum(
            1
            for result in results
            if result.updated_stock
        )

        downloaded = sum(
            result.downloaded_records
            for result in results
        )

        inserted = sum(
            result.inserted_records
            for result in results
        )

        skipped = sum(
            result.skipped_records
            for result in results
        )

        return {
            "symbols": len(results),
            "successful": successful,
            "failed": failed,
            "created": created,
            "updated": updated,
            "downloaded": downloaded,
            "inserted": inserted,
            "skipped": skipped,
        }

    