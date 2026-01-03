"""
Market Data API Endpoints
Fetch real-time and historical market data
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db
from app.services.market_data import market_data_service

router = APIRouter()


@router.get("/{ticker}")
async def get_market_data(
    ticker: str, days: int = Query(default=30, ge=1, le=365, description="Days of historical data")
):
    """
    Get comprehensive market data for a ticker

    Returns:
    - Current quote (price, change, high, low)
    - Historical OHLCV data
    - Technical indicators (RSI, price changes, volume trend)
    """
    ticker = ticker.upper()

    # Get current quote
    quote = market_data_service.get_quote(ticker)

    if quote.get("current_price") is None:
        raise HTTPException(
            status_code=404,
            detail=f"Could not fetch price data for {ticker}. Check if ticker is valid.",
        )

    # Get historical data
    historical = market_data_service.get_historical_data(ticker, days=days)

    # Get technical indicators
    technical = market_data_service.get_technical_indicators(ticker)

    return {
        "ticker": ticker,
        "quote": quote,
        "historical": historical,
        "technical_indicators": technical,
        "data_points": len(historical),
    }


@router.get("/{ticker}/quote")
async def get_quote(ticker: str):
    """
    Get current quote for a ticker

    Returns real-time price data including:
    - Current price
    - Daily change percentage
    - High/Low/Open
    - Previous close
    """
    ticker = ticker.upper()
    quote = market_data_service.get_quote(ticker)

    if quote.get("current_price") is None:
        raise HTTPException(status_code=404, detail=f"Could not fetch quote for {ticker}")

    return quote


@router.get("/{ticker}/historical")
async def get_historical(ticker: str, days: int = Query(default=30, ge=1, le=365)):
    """
    Get historical OHLCV data for a ticker

    Returns daily bars with:
    - Date, Open, High, Low, Close, Volume
    - Data source (polygon, alphavantage, etc.)
    """
    ticker = ticker.upper()
    historical = market_data_service.get_historical_data(ticker, days=days)

    if not historical:
        raise HTTPException(status_code=404, detail=f"No historical data available for {ticker}")

    return {
        "ticker": ticker,
        "days_requested": days,
        "data_points": len(historical),
        "data": historical,
    }


@router.get("/{ticker}/technical")
async def get_technical_indicators(ticker: str):
    """
    Get technical indicators for a ticker

    Returns:
    - RSI (14-day)
    - Price change (1d, 7d, 30d)
    - Volume trend
    """
    ticker = ticker.upper()
    technical = market_data_service.get_technical_indicators(ticker)

    return {"ticker": ticker, "indicators": technical}


@router.get("/{ticker}/price")
async def get_current_price(ticker: str):
    """
    Get just the current price for a ticker

    Simple endpoint for quick price checks
    """
    ticker = ticker.upper()
    price = market_data_service.get_current_price(ticker)

    if price is None:
        raise HTTPException(status_code=404, detail=f"Could not fetch price for {ticker}")

    return {"ticker": ticker, "price": price}
