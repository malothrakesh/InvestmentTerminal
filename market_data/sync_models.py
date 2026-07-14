"""
Synchronization models.

These models represent the outcome of market data
synchronization operations.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True, frozen=True)
class SynchronizationResult:
    """
    Result of a synchronization operation.
    """

    symbol: str

    created_stock: bool = False

    updated_stock: bool = False

    downloaded_records: int = 0

    inserted_records: int = 0

    skipped_records: int = 0

    started_at: datetime | None = None

    finished_at: datetime | None = None

    elapsed_seconds: float = 0.0

    provider: str | None = None

    success: bool = True

    message: str = ""