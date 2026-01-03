"""
Data Tasks - Scheduled data fetching for Alpha Machine

Tasks:
- fetch_market_data_task: Fetch market data for all watchlist stocks
- fetch_sentiment_task: Fetch sentiment data for all watchlist stocks
"""

from celery import shared_task
from typing import Dict, List, Any
import logging
from datetime import datetime

from app.core.database import SessionLocal
from app.models.watchlist import Watchlist
from app.models.market_data import MarketData
from app.models.sentiment_data import SentimentData
from app.services.market_data import market_data_service
from app.services.sentiment_data import sentiment_service
from app.tasks.celery_app import is_market_hours

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    name="app.tasks.data_tasks.fetch_market_data_task",
    max_retries=3,
    default_retry_delay=60,
)
def fetch_market_data_task(self) -> Dict[str, Any]:
    """
    Fetch market data for all active watchlist stocks.

    Runs every 5 minutes during market hours.
    Stores results in the market_data table.

    Returns:
        Dict with success/failure counts and details
    """
    # Skip if outside market hours (optional - can be disabled for testing)
    # if not is_market_hours():
    #     return {"status": "skipped", "reason": "Outside market hours"}

    db = SessionLocal()
    results = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "successful": 0,
        "failed": 0,
        "tickers": [],
    }

    try:
        # Get all active tickers from watchlist
        watchlist = db.query(Watchlist).filter(Watchlist.is_active == True).all()

        if not watchlist:
            results["status"] = "no_tickers"
            return results

        for item in watchlist:
            ticker = item.ticker
            try:
                # Fetch market data
                quote = market_data_service.get_quote(ticker)

                if quote.get("current_price") is not None:
                    # Store in database
                    market_data = MarketData(
                        ticker=ticker,
                        price=quote.get("current_price"),
                        open_price=quote.get("open"),
                        high_price=quote.get("high"),
                        low_price=quote.get("low"),
                        volume=quote.get("volume"),
                        change_percent=quote.get("change_percent"),
                        source=quote.get("source", "unknown"),
                    )
                    db.add(market_data)

                    results["successful"] += 1
                    results["tickers"].append({
                        "ticker": ticker,
                        "price": quote.get("current_price"),
                        "status": "success",
                    })
                else:
                    results["failed"] += 1
                    results["tickers"].append({
                        "ticker": ticker,
                        "status": "no_data",
                    })

            except Exception as e:
                logger.error(f"Failed to fetch market data for {ticker}: {e}")
                results["failed"] += 1
                results["tickers"].append({
                    "ticker": ticker,
                    "status": "error",
                    "error": str(e),
                })

        db.commit()
        results["status"] = "completed"

    except Exception as e:
        logger.error(f"Market data task failed: {e}")
        results["status"] = "error"
        results["error"] = str(e)
        db.rollback()
        raise self.retry(exc=e)

    finally:
        db.close()

    logger.info(
        f"Market data task completed: {results['successful']} success, "
        f"{results['failed']} failed"
    )
    return results


@shared_task(
    bind=True,
    name="app.tasks.data_tasks.fetch_sentiment_task",
    max_retries=3,
    default_retry_delay=120,
)
def fetch_sentiment_task(self) -> Dict[str, Any]:
    """
    Fetch sentiment data for all active watchlist stocks.

    Runs every 30 minutes.
    Aggregates Reddit + News sentiment and stores in sentiment_data table.

    Returns:
        Dict with success/failure counts and details
    """
    db = SessionLocal()
    results = {
        "task_id": self.request.id,
        "timestamp": datetime.utcnow().isoformat(),
        "successful": 0,
        "failed": 0,
        "tickers": [],
    }

    try:
        # Get all active tickers from watchlist
        watchlist = db.query(Watchlist).filter(Watchlist.is_active == True).all()

        if not watchlist:
            results["status"] = "no_tickers"
            return results

        for item in watchlist:
            ticker = item.ticker
            try:
                # Fetch aggregated sentiment
                sentiment = sentiment_service.aggregate_sentiment(ticker)

                if sentiment:
                    # Store in database
                    sentiment_data = SentimentData(
                        ticker=ticker,
                        source="combined",
                        sentiment_score=sentiment.get("combined_sentiment", 0),
                        bullish_count=sentiment.get("bullish_mentions", 0),
                        bearish_count=sentiment.get("bearish_mentions", 0),
                        total_mentions=sentiment.get("total_mentions", 0),
                        confidence=sentiment.get("confidence", 0),
                    )
                    db.add(sentiment_data)

                    results["successful"] += 1
                    results["tickers"].append({
                        "ticker": ticker,
                        "sentiment": sentiment.get("combined_sentiment"),
                        "mentions": sentiment.get("total_mentions", 0),
                        "status": "success",
                    })
                else:
                    results["failed"] += 1
                    results["tickers"].append({
                        "ticker": ticker,
                        "status": "no_data",
                    })

            except Exception as e:
                logger.error(f"Failed to fetch sentiment for {ticker}: {e}")
                results["failed"] += 1
                results["tickers"].append({
                    "ticker": ticker,
                    "status": "error",
                    "error": str(e),
                })

        db.commit()
        results["status"] = "completed"

    except Exception as e:
        logger.error(f"Sentiment task failed: {e}")
        results["status"] = "error"
        results["error"] = str(e)
        db.rollback()
        raise self.retry(exc=e)

    finally:
        db.close()

    logger.info(
        f"Sentiment task completed: {results['successful']} success, "
        f"{results['failed']} failed"
    )
    return results


@shared_task(name="app.tasks.data_tasks.fetch_single_ticker_data")
def fetch_single_ticker_data(ticker: str) -> Dict[str, Any]:
    """
    Fetch all data for a single ticker.

    Can be called on-demand for specific tickers.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Dict with market data and sentiment
    """
    result = {
        "ticker": ticker.upper(),
        "timestamp": datetime.utcnow().isoformat(),
        "market_data": None,
        "sentiment_data": None,
        "status": "success",
    }

    try:
        # Fetch market data
        quote = market_data_service.get_quote(ticker)
        if quote.get("current_price"):
            result["market_data"] = quote

        # Fetch technical indicators
        technical = market_data_service.get_technical_indicators(ticker)
        if technical:
            result["technical_indicators"] = technical

        # Fetch sentiment
        try:
            sentiment = sentiment_service.aggregate_sentiment(ticker)
            result["sentiment_data"] = sentiment
        except Exception as e:
            logger.warning(f"Sentiment fetch failed for {ticker}: {e}")

    except Exception as e:
        logger.error(f"Data fetch failed for {ticker}: {e}")
        result["status"] = "error"
        result["error"] = str(e)

    return result


@shared_task(name="app.tasks.data_tasks.refresh_all_data")
def refresh_all_data() -> Dict[str, Any]:
    """
    Manually trigger a full data refresh for all watchlist tickers.

    Combines market data and sentiment fetching in one task.

    Returns:
        Dict with combined results
    """
    market_result = fetch_market_data_task.delay()
    sentiment_result = fetch_sentiment_task.delay()

    return {
        "status": "tasks_queued",
        "market_task_id": market_result.id,
        "sentiment_task_id": sentiment_result.id,
        "timestamp": datetime.utcnow().isoformat(),
    }
