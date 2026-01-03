"""
Market Data Service
Aggregates market data from multiple sources: Polygon.io, Finnhub, Alpha Vantage
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.config import settings
from app.core.retry import retry_with_backoff, with_fallback
import logging

logger = logging.getLogger(__name__)


def _make_request(
    url: str,
    params: Dict,
    timeout: int = 10,
    max_retries: int = 3,
) -> Optional[requests.Response]:
    """
    Make an HTTP request with retry logic.

    Args:
        url: Request URL
        params: Query parameters
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts

    Returns:
        Response object or None on failure
    """
    delay = 1.0  # Initial delay in seconds

    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=timeout)

            # Handle rate limiting
            if response.status_code == 429:
                if attempt < max_retries - 1:
                    retry_after = int(response.headers.get("Retry-After", delay))
                    logger.warning(
                        f"Rate limited, waiting {retry_after}s "
                        f"(attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(retry_after)
                    delay *= 2
                    continue

            # Handle server errors with retry
            if response.status_code >= 500:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Server error {response.status_code}, "
                        f"retrying in {delay}s (attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(delay)
                    delay *= 2
                    continue

            return response

        except requests.exceptions.Timeout as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Request timeout, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Request timeout after {max_retries} attempts: {e}")
                return None

        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"Connection error, retrying in {delay}s "
                    f"(attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(delay)
                delay *= 2
            else:
                logger.error(f"Connection error after {max_retries} attempts: {e}")
                return None

        except Exception as e:
            logger.error(f"Unexpected request error: {type(e).__name__}: {e}")
            return None

    return None


class MarketDataService:
    """Aggregate market data from multiple sources with fallback logic"""

    def __init__(self):
        self.polygon_base = "https://api.polygon.io"
        self.finnhub_base = "https://finnhub.io/api/v1"
        self.av_base = "https://www.alphavantage.co/query"

    def get_current_price(self, ticker: str) -> Optional[float]:
        """
        Get current price (try Polygon first, fallback to Finnhub)

        Args:
            ticker: Stock ticker symbol (e.g., 'NVDA')

        Returns:
            Current stock price or None if all sources fail
        """
        # Try Polygon first (FREE tier: 5 calls/min)
        price = self._get_price_polygon(ticker)
        if price is not None:
            return price

        # Fallback to Finnhub
        price = self._get_price_finnhub(ticker)
        if price is not None:
            return price

        logger.error(f"All price sources failed for {ticker}")
        return None

    def _get_price_polygon(self, ticker: str) -> Optional[float]:
        """Get price from Polygon.io with retry logic"""
        if not settings.POLYGON_API_KEY:
            logger.warning("Polygon API key not configured")
            return None

        try:
            url = f"{self.polygon_base}/v2/aggs/ticker/{ticker}/prev"
            params = {"apiKey": settings.POLYGON_API_KEY}
            response = _make_request(url, params, timeout=10, max_retries=3)

            if response and response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    price = data["results"][0]["c"]  # close price
                    logger.info(f"Polygon: {ticker} = ${price}")
                    return float(price)
            elif response:
                logger.warning(f"Polygon API error: {response.status_code}")
        except Exception as e:
            logger.warning(f"Polygon failed for {ticker}: {e}")

        return None

    def _get_price_finnhub(self, ticker: str) -> Optional[float]:
        """Get price from Finnhub with retry logic"""
        if not settings.FINNHUB_API_KEY:
            logger.warning("Finnhub API key not configured")
            return None

        try:
            url = f"{self.finnhub_base}/quote"
            params = {"symbol": ticker, "token": settings.FINNHUB_API_KEY}
            response = _make_request(url, params, timeout=10, max_retries=3)

            if response and response.status_code == 200:
                data = response.json()
                price = data.get("c")  # current price
                if price and price > 0:
                    logger.info(f"Finnhub: {ticker} = ${price}")
                    return float(price)
            elif response:
                logger.warning(f"Finnhub API error: {response.status_code}")
        except Exception as e:
            logger.warning(f"Finnhub failed for {ticker}: {e}")

        return None

    def get_historical_data(self, ticker: str, days: int = 30) -> List[Dict]:
        """
        Get historical OHLCV data

        Args:
            ticker: Stock ticker symbol
            days: Number of days of history (default 30)

        Returns:
            List of OHLCV dictionaries sorted by date descending
        """
        # Try Alpha Vantage (FREE tier: 25 calls/day)
        data = self._get_historical_alphavantage(ticker, days)
        if data:
            return data

        # Fallback to Polygon
        data = self._get_historical_polygon(ticker, days)
        if data:
            return data

        logger.error(f"All historical data sources failed for {ticker}")
        return []

    def _get_historical_alphavantage(self, ticker: str, days: int) -> List[Dict]:
        """Get historical data from Alpha Vantage with retry logic"""
        if not settings.ALPHA_VANTAGE_API_KEY:
            logger.warning("Alpha Vantage API key not configured")
            return []

        try:
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": ticker,
                "apikey": settings.ALPHA_VANTAGE_API_KEY,
                "outputsize": "compact",  # last 100 days
            }
            response = _make_request(self.av_base, params, timeout=15, max_retries=3)

            if response and response.status_code == 200:
                data = response.json()

                # Check for API limit message
                if "Note" in data or "Information" in data:
                    logger.warning(
                        f"Alpha Vantage rate limit: {data.get('Note', data.get('Information', ''))}"
                    )
                    return []

                time_series = data.get("Time Series (Daily)", {})

                if not time_series:
                    logger.warning(f"No data from Alpha Vantage for {ticker}")
                    return []

                result = []
                for date_str, values in list(time_series.items())[:days]:
                    result.append(
                        {
                            "date": date_str,
                            "open": float(values["1. open"]),
                            "high": float(values["2. high"]),
                            "low": float(values["3. low"]),
                            "close": float(values["4. close"]),
                            "volume": int(values["5. volume"]),
                            "source": "alphavantage",
                        }
                    )

                logger.info(f"Alpha Vantage: Got {len(result)} days of data for {ticker}")
                return result
        except Exception as e:
            logger.warning(f"Alpha Vantage failed for {ticker}: {e}")

        return []

    def _get_historical_polygon(self, ticker: str, days: int) -> List[Dict]:
        """Get historical data from Polygon with retry logic"""
        if not settings.POLYGON_API_KEY:
            return []

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 5)  # Extra buffer for weekends

            url = f"{self.polygon_base}/v2/aggs/ticker/{ticker}/range/1/day/{start_date.strftime('%Y-%m-%d')}/{end_date.strftime('%Y-%m-%d')}"
            params = {"apiKey": settings.POLYGON_API_KEY, "limit": days}
            response = _make_request(url, params, timeout=15, max_retries=3)

            if response and response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if not results:
                    return []

                result = []
                for bar in results[-days:]:  # Get last N days
                    date_ts = bar["t"] / 1000  # Convert from milliseconds
                    result.append(
                        {
                            "date": datetime.fromtimestamp(date_ts).strftime("%Y-%m-%d"),
                            "open": float(bar["o"]),
                            "high": float(bar["h"]),
                            "low": float(bar["l"]),
                            "close": float(bar["c"]),
                            "volume": int(bar["v"]),
                            "source": "polygon",
                        }
                    )

                logger.info(f"Polygon: Got {len(result)} days of data for {ticker}")
                return sorted(result, key=lambda x: x["date"], reverse=True)
        except Exception as e:
            logger.warning(f"Polygon historical failed for {ticker}: {e}")

        return []

    def get_technical_indicators(self, ticker: str) -> Dict:
        """
        Get technical indicators (RSI, etc.)

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with technical indicators
        """
        indicators = {}

        # Try to get RSI from Alpha Vantage
        rsi = self._get_rsi_alphavantage(ticker)
        if rsi is not None:
            indicators["rsi"] = rsi

        # Calculate simple indicators from historical data if needed
        if "rsi" not in indicators:
            historical = self.get_historical_data(ticker, days=20)
            if historical:
                indicators["rsi"] = self._calculate_rsi(historical)

        # Add price change metrics
        historical = self.get_historical_data(ticker, days=30)
        if historical:
            indicators["price_change_1d"] = self._calculate_price_change(historical, 1)
            indicators["price_change_7d"] = self._calculate_price_change(historical, 7)
            indicators["price_change_30d"] = self._calculate_price_change(historical, 30)
            indicators["volume_trend"] = self._calculate_volume_trend(historical)

        return indicators

    def _get_rsi_alphavantage(self, ticker: str) -> Optional[float]:
        """Get RSI from Alpha Vantage with retry logic"""
        if not settings.ALPHA_VANTAGE_API_KEY:
            return None

        try:
            params = {
                "function": "RSI",
                "symbol": ticker,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close",
                "apikey": settings.ALPHA_VANTAGE_API_KEY,
            }
            response = _make_request(self.av_base, params, timeout=15, max_retries=3)

            if response and response.status_code == 200:
                data = response.json()
                technical = data.get("Technical Analysis: RSI", {})
                if technical:
                    latest_date = list(technical.keys())[0]
                    rsi = float(technical[latest_date]["RSI"])
                    logger.info(f"Alpha Vantage RSI for {ticker}: {rsi}")
                    return rsi
        except Exception as e:
            logger.warning(f"RSI fetch failed for {ticker}: {e}")

        return None

    def _calculate_rsi(self, historical: List[Dict], period: int = 14) -> float:
        """Calculate RSI from historical data"""
        if len(historical) < period + 1:
            return 50.0  # Default neutral RSI

        closes = [d["close"] for d in reversed(historical)]  # Oldest first
        deltas = [closes[i] - closes[i - 1] for i in range(1, len(closes))]

        gains = [d if d > 0 else 0 for d in deltas[-period:]]
        losses = [-d if d < 0 else 0 for d in deltas[-period:]]

        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return round(rsi, 2)

    def _calculate_price_change(self, historical: List[Dict], days: int) -> float:
        """Calculate price change percentage over N days"""
        if len(historical) < days:
            return 0.0

        current = historical[0]["close"]
        past = historical[min(days - 1, len(historical) - 1)]["close"]

        if past == 0:
            return 0.0

        change = ((current - past) / past) * 100
        return round(change, 2)

    def _calculate_volume_trend(self, historical: List[Dict]) -> str:
        """Determine volume trend (increasing/decreasing/neutral)"""
        if len(historical) < 10:
            return "neutral"

        recent_vol = sum(d["volume"] for d in historical[:5]) / 5
        older_vol = sum(d["volume"] for d in historical[5:10]) / 5

        if older_vol == 0:
            return "neutral"

        change = (recent_vol - older_vol) / older_vol

        if change > 0.2:
            return "increasing"
        elif change < -0.2:
            return "decreasing"
        else:
            return "neutral"

    def get_quote(self, ticker: str) -> Dict:
        """
        Get comprehensive quote data for a ticker

        Returns:
            Dictionary with current price, change, volume, etc.
        """
        quote = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "current_price": None,
            "change_percent": None,
            "volume": None,
            "high": None,
            "low": None,
            "open": None,
            "previous_close": None,
        }

        # Get current price
        quote["current_price"] = self.get_current_price(ticker)

        # Get additional quote data from Finnhub
        if settings.FINNHUB_API_KEY:
            try:
                url = f"{self.finnhub_base}/quote"
                params = {"symbol": ticker, "token": settings.FINNHUB_API_KEY}
                response = requests.get(url, params=params, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    quote["high"] = data.get("h")
                    quote["low"] = data.get("l")
                    quote["open"] = data.get("o")
                    quote["previous_close"] = data.get("pc")

                    if data.get("pc") and data.get("c"):
                        change = ((data["c"] - data["pc"]) / data["pc"]) * 100
                        quote["change_percent"] = round(change, 2)
            except Exception as e:
                logger.warning(f"Quote details failed for {ticker}: {e}")

        return quote


# Singleton instance
market_data_service = MarketDataService()
