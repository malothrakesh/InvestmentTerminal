from __future__ import annotations

from enum import Enum


class SecurityType(str, Enum):
    """
    Supported security asset classes.
    """

    EQUITY = "EQUITY"
    ETF = "ETF"
    MUTUAL_FUND = "MUTUAL_FUND"
    INDEX = "INDEX"
    FOREX = "FOREX"
    CRYPTO = "CRYPTO"
    BOND = "BOND"
    FUTURE = "FUTURE"
    OPTION = "OPTION"
    COMMODITY = "COMMODITY"
    ADR = "ADR"
    REIT = "REIT"