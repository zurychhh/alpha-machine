"""
Input Validation & Sanitization
Utility functions and Pydantic models for validating user input
"""

import re
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
import logging

logger = logging.getLogger(__name__)


# Valid stock ticker pattern (1-5 uppercase letters)
TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}$")

# Common invalid "tickers" to filter out
INVALID_TICKERS = {
    "I",
    "A",
    "AN",
    "THE",
    "AND",
    "OR",
    "BUT",
    "FOR",
    "TO",
    "OF",
    "IN",
    "IT",
    "IS",
    "BE",
    "AS",
    "AT",
    "SO",
    "WE",
    "HE",
    "BY",
    "ON",
    "DO",
    "IF",
    "ME",
    "MY",
    "UP",
    "AM",
    "PM",
    "GO",
    "NO",
    "US",
    "OK",
    "ALL",
    "NEW",
    "NOW",
    "OLD",
    "SEE",
    "WAY",
    "WHO",
    "DAY",
    "GET",
    "HAS",
    "HIM",
    "HOW",
    "ITS",
    "LET",
    "MAY",
    "PUT",
    "SAY",
    "SHE",
    "TOO",
    "USE",
    "CEO",
    "CFO",
    "IPO",
    "API",
    "ETF",
    "CEO",
    "CTO",
    "FAQ",
    "USA",
    "NYSE",
    "EDIT",
}


def validate_ticker(ticker: str) -> Optional[str]:
    """
    Validate and sanitize a stock ticker symbol.

    Args:
        ticker: Raw ticker input

    Returns:
        Sanitized ticker or None if invalid
    """
    if not ticker:
        return None

    # Uppercase and strip whitespace
    sanitized = ticker.strip().upper()

    # Remove $ prefix if present
    if sanitized.startswith("$"):
        sanitized = sanitized[1:]

    # Check pattern
    if not TICKER_PATTERN.match(sanitized):
        logger.debug(f"Invalid ticker format: {ticker}")
        return None

    # Check against invalid list
    if sanitized in INVALID_TICKERS:
        logger.debug(f"Ticker in exclusion list: {ticker}")
        return None

    return sanitized


def validate_tickers(tickers: List[str]) -> List[str]:
    """
    Validate a list of tickers, filtering out invalid ones.

    Args:
        tickers: List of raw ticker inputs

    Returns:
        List of validated tickers
    """
    validated = []
    for ticker in tickers:
        valid = validate_ticker(ticker)
        if valid and valid not in validated:
            validated.append(valid)
    return validated


class TickerInput(BaseModel):
    """Validated ticker input model"""

    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=5)

    @field_validator("ticker")
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        sanitized = validate_ticker(v)
        if sanitized is None:
            raise ValueError(f"Invalid ticker symbol: {v}")
        return sanitized


class TickerListInput(BaseModel):
    """Validated list of tickers input model"""

    tickers: List[str] = Field(..., min_length=1, max_length=50)

    @field_validator("tickers")
    @classmethod
    def validate_ticker_list(cls, v: List[str]) -> List[str]:
        validated = validate_tickers(v)
        if not validated:
            raise ValueError("No valid tickers provided")
        return validated


class AnalysisRequest(BaseModel):
    """Request model for comprehensive analysis"""

    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., description="Stock ticker symbol")
    include_sentiment: bool = Field(default=True, description="Include sentiment analysis")
    include_technical: bool = Field(default=True, description="Include technical indicators")
    days_history: int = Field(default=30, ge=1, le=365, description="Days of history")

    @field_validator("ticker")
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        sanitized = validate_ticker(v)
        if sanitized is None:
            raise ValueError(f"Invalid ticker symbol: {v}")
        return sanitized


class DateRangeInput(BaseModel):
    """Validated date range input"""

    start_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    end_date: Optional[str] = Field(None, pattern=r"^\d{4}-\d{2}-\d{2}$")
    days: int = Field(default=30, ge=1, le=365)

    @field_validator("end_date")
    @classmethod
    def validate_date_order(cls, v: Optional[str], info) -> Optional[str]:
        start = info.data.get("start_date")
        if start and v:
            if v < start:
                raise ValueError("end_date must be after start_date")
        return v


class WatchlistItem(BaseModel):
    """Input model for adding a stock to watchlist"""

    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=5)
    company_name: Optional[str] = Field(None, max_length=200)
    sector: Optional[str] = Field(None, max_length=100)
    tier: int = Field(default=3, ge=1, le=5, description="Priority tier 1-5")
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator("ticker")
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        sanitized = validate_ticker(v)
        if sanitized is None:
            raise ValueError(f"Invalid ticker symbol: {v}")
        return sanitized

    @field_validator("company_name", "sector", "notes")
    @classmethod
    def sanitize_text(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        # Remove potentially dangerous characters
        sanitized = re.sub(r'[<>"\']', "", v)
        return sanitized.strip()


class SignalRequest(BaseModel):
    """Request model for generating a trading signal"""

    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., description="Stock ticker symbol")
    force_refresh: bool = Field(default=False, description="Force data refresh")

    @field_validator("ticker")
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        sanitized = validate_ticker(v)
        if sanitized is None:
            raise ValueError(f"Invalid ticker symbol: {v}")
        return sanitized


class PortfolioPositionInput(BaseModel):
    """Input model for portfolio position"""

    model_config = ConfigDict(str_strip_whitespace=True)

    ticker: str = Field(..., min_length=1, max_length=5)
    shares: float = Field(..., gt=0, description="Number of shares")
    entry_price: float = Field(..., gt=0, description="Entry price per share")
    stop_loss: Optional[float] = Field(None, gt=0, description="Stop loss price")
    take_profit: Optional[float] = Field(None, gt=0, description="Take profit price")

    @field_validator("ticker")
    @classmethod
    def validate_ticker_format(cls, v: str) -> str:
        sanitized = validate_ticker(v)
        if sanitized is None:
            raise ValueError(f"Invalid ticker symbol: {v}")
        return sanitized

    @field_validator("stop_loss")
    @classmethod
    def validate_stop_loss(cls, v: Optional[float], info) -> Optional[float]:
        entry = info.data.get("entry_price")
        if v is not None and entry is not None and v >= entry:
            raise ValueError("stop_loss must be less than entry_price for long positions")
        return v

    @field_validator("take_profit")
    @classmethod
    def validate_take_profit(cls, v: Optional[float], info) -> Optional[float]:
        entry = info.data.get("entry_price")
        if v is not None and entry is not None and v <= entry:
            raise ValueError("take_profit must be greater than entry_price for long positions")
        return v


def sanitize_text_input(text: Optional[str], max_length: int = 1000) -> Optional[str]:
    """
    Sanitize text input to prevent XSS and injection attacks.

    Args:
        text: Raw text input
        max_length: Maximum allowed length

    Returns:
        Sanitized text or None
    """
    if text is None:
        return None

    # Strip whitespace
    sanitized = text.strip()

    # Truncate to max length
    sanitized = sanitized[:max_length]

    # Remove potentially dangerous characters
    sanitized = re.sub(r'[<>"\']', "", sanitized)

    # Remove control characters
    sanitized = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", sanitized)

    return sanitized if sanitized else None


def sanitize_numeric_input(
    value: Optional[float],
    min_val: Optional[float] = None,
    max_val: Optional[float] = None,
    default: Optional[float] = None,
) -> Optional[float]:
    """
    Sanitize and validate numeric input.

    Args:
        value: Raw numeric value
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        default: Default value if input is None

    Returns:
        Validated number or default
    """
    if value is None:
        return default

    if min_val is not None and value < min_val:
        logger.warning(f"Value {value} below minimum {min_val}, using minimum")
        return min_val

    if max_val is not None and value > max_val:
        logger.warning(f"Value {value} above maximum {max_val}, using maximum")
        return max_val

    return value
