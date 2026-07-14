"""
Factory for market data providers.
"""

from __future__ import annotations

from market_data.base_provider import BaseMarketDataProvider
from market_data.providers.yahoo_provider import YahooMarketDataProvider


class ProviderFactory:
    """
    Creates market data provider instances.
    """

    DEFAULT_PROVIDER = "yahoo"

    _providers: dict[str, type[BaseMarketDataProvider]] = {
        "yahoo": YahooMarketDataProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str | None = None,
    ) -> BaseMarketDataProvider:
        """
        Create a provider instance.

        Args:
            provider_name:
                Provider identifier.
                Defaults to the configured default provider.

        Returns:
            Provider instance.

        Raises:
            ValueError:
                If the provider is unsupported.
        """
        name = (provider_name or cls.DEFAULT_PROVIDER).lower()

        provider_cls = cls._providers.get(name)

        if provider_cls is None:
            raise ValueError(f"Unsupported provider '{name}'.")

        return provider_cls()

    @classmethod
    def register(
        cls,
        name: str,
        provider_cls: type[BaseMarketDataProvider],
    ) -> None:
        """
        Register a provider.
        """
        cls._providers[name.lower()] = provider_cls

    @classmethod
    def available_providers(cls) -> tuple[str, ...]:
        """
        Return supported providers.
        """
        return tuple(sorted(cls._providers))