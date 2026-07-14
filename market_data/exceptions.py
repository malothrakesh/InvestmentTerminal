"""
Exceptions raised by the Market Data Provider layer.
"""


class ProviderError(Exception):
    """Base provider exception."""


class ConnectionError(ProviderError):
    """Provider connection failure."""


class DownloadError(ProviderError):
    """Download operation failed."""


class SymbolNotFound(DownloadError):
    """Requested symbol was not found."""


class UnsupportedTimeframe(DownloadError):
    """Requested timeframe is unsupported."""


class UnsupportedExchange(DownloadError):
    """Requested exchange is unsupported."""


class InvalidProviderResponse(DownloadError):
    """Provider returned invalid or malformed data."""


class ProviderTimeout(DownloadError):
    """Provider request timed out."""