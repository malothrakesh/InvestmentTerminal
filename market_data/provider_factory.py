"""
Factory responsible for creating market data providers.
"""

from __future__ import annotations

from typing import Type

from loguru import logger

from config import settings
from market_data.base_provider import BaseMarketDataProvider
from market_data.providers.yahoo_provider import YahooProvider


class ProviderFactory:
    """
    Factory for creating market data providers.

    This class centralizes provider registration and
    instantiation so that the remainder of the application
    never depends on concrete provider implementations.
    """

    _PROVIDERS: dict[str, Type[BaseMarketDataProvider]] = {
        "yahoo": YahooProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str | None = None,
    ) -> BaseMarketDataProvider:
        """
        Create a market data provider.

        Args:
            provider_name:
                Optional provider name.
                If omitted, the configured provider is used.

        Returns:
            Initialized provider.

        Raises:
            ValueError:
                If the provider is unsupported.
        """
        provider_key = (
            provider_name
            or settings.MARKET_DATA_PROVIDER
        ).strip().lower()

        provider_class = cls._PROVIDERS.get(provider_key)

        if provider_class is None:
            raise ValueError(
                f"Unsupported market data provider: "
                f"{provider_key}"
            )

        logger.info(
            "Creating market data provider '{}'.",
            provider_key,
        )

        provider = provider_class()
        provider.connect()

        return provider

    @classmethod
    def register(
        cls,
        name: str,
        provider: Type[BaseMarketDataProvider],
    ) -> None:
        """
        Register a provider.

        Args:
            name:
                Provider identifier.

            provider:
                Provider class.
        """
        key = name.strip().lower()

        cls._PROVIDERS[key] = provider

        logger.info(
            "Registered market data provider '{}'.",
            key,
        )

    @classmethod
    def available_providers(
        cls,
    ) -> tuple[str, ...]:
        """
        Return available provider names.
        """
        return tuple(sorted(cls._PROVIDERS.keys()))

    @classmethod
    def is_supported(
        cls,
        provider_name: str,
    ) -> bool:
        """
        Determine whether a provider is supported.
        """
        return (
            provider_name.strip().lower()
            in cls._PROVIDERS
        )