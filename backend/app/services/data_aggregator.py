"""
Data Aggregator Service
Combines market data and sentiment data for comprehensive analysis
"""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.services.market_data import market_data_service
from app.services.sentiment_data import sentiment_service
from app.models.market_data import MarketData
from app.models.sentiment_data import SentimentData
from app.models.watchlist import Watchlist
import logging

logger = logging.getLogger(__name__)


class DataAggregatorService:
    """Aggregate all data sources for a ticker"""

    def get_comprehensive_analysis(self, ticker: str, db: Optional[Session] = None) -> Dict:
        """
        Get comprehensive data package for a ticker

        Combines:
        - Current price and quote data
        - Historical price data (30 days)
        - Technical indicators (RSI, price changes)
        - Reddit sentiment
        - News sentiment

        Args:
            ticker: Stock ticker symbol
            db: Optional database session for caching

        Returns:
            Dictionary with all aggregated data
        """
        logger.info(f"Aggregating comprehensive data for {ticker}")

        # Fetch all data sources
        quote = market_data_service.get_quote(ticker)
        historical = market_data_service.get_historical_data(ticker, days=30)
        technical = market_data_service.get_technical_indicators(ticker)
        sentiment = sentiment_service.aggregate_sentiment(ticker)

        # Calculate additional metrics
        analysis = {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "quote": quote,
            "historical_summary": self._summarize_historical(historical),
            "technical_indicators": technical,
            "sentiment": sentiment,
            "overall_outlook": self._calculate_overall_outlook(technical, sentiment),
        }

        # Cache to database if session provided
        if db:
            self._cache_market_data(db, ticker, historical)
            self._cache_sentiment_data(db, ticker, sentiment)

        return analysis

    def _summarize_historical(self, historical: List[Dict]) -> Dict:
        """Create summary of historical data"""
        if not historical:
            return {"data_points": 0, "source": None, "date_range": None}

        return {
            "data_points": len(historical),
            "source": historical[0].get("source", "unknown"),
            "date_range": {
                "start": historical[-1].get("date") if historical else None,
                "end": historical[0].get("date") if historical else None,
            },
            "latest": (
                {
                    "date": historical[0].get("date"),
                    "close": historical[0].get("close"),
                    "volume": historical[0].get("volume"),
                }
                if historical
                else None
            ),
            "avg_volume": (
                sum(d.get("volume", 0) for d in historical) / len(historical) if historical else 0
            ),
            "high_30d": max(d.get("high", 0) for d in historical) if historical else 0,
            "low_30d": min(d.get("low", float("inf")) for d in historical) if historical else 0,
        }

    def _calculate_overall_outlook(self, technical: Dict, sentiment: Dict) -> Dict:
        """
        Calculate overall outlook based on technical and sentiment

        Returns outlook score and recommendation
        """
        scores = []

        # RSI contribution (-1 to +1)
        rsi = technical.get("rsi", 50)
        if rsi < 30:
            rsi_score = 1.0  # Oversold = bullish
        elif rsi > 70:
            rsi_score = -1.0  # Overbought = bearish
        else:
            rsi_score = (50 - rsi) / 50 * 0.5  # Neutral zone
        scores.append(("rsi", rsi_score, 0.3))  # 30% weight

        # Price momentum contribution (-1 to +1)
        price_7d = technical.get("price_change_7d", 0)
        momentum_score = max(min(price_7d / 10, 1), -1)  # Cap at +-10% = +-1
        scores.append(("momentum", momentum_score, 0.2))  # 20% weight

        # Volume trend contribution
        volume_trend = technical.get("volume_trend", "neutral")
        if volume_trend == "increasing":
            volume_score = 0.3
        elif volume_trend == "decreasing":
            volume_score = -0.3
        else:
            volume_score = 0
        scores.append(("volume", volume_score, 0.1))  # 10% weight

        # Sentiment contribution (-1 to +1)
        sentiment_score = sentiment.get("combined_sentiment", 0)
        scores.append(("sentiment", sentiment_score, 0.4))  # 40% weight

        # Calculate weighted average
        total_weight = sum(s[2] for s in scores)
        weighted_sum = sum(s[1] * s[2] for s in scores)
        overall_score = weighted_sum / total_weight if total_weight > 0 else 0

        # Determine recommendation
        if overall_score > 0.3:
            recommendation = "BULLISH"
        elif overall_score > 0.1:
            recommendation = "SLIGHTLY_BULLISH"
        elif overall_score < -0.3:
            recommendation = "BEARISH"
        elif overall_score < -0.1:
            recommendation = "SLIGHTLY_BEARISH"
        else:
            recommendation = "NEUTRAL"

        return {
            "score": round(overall_score, 3),
            "recommendation": recommendation,
            "factors": {
                "rsi": {
                    "value": rsi,
                    "interpretation": (
                        "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral"
                    ),
                },
                "momentum_7d": {
                    "value": f"{price_7d:.1f}%",
                    "trend": "up" if price_7d > 0 else "down" if price_7d < 0 else "flat",
                },
                "volume_trend": volume_trend,
                "sentiment": {
                    "score": sentiment_score,
                    "label": sentiment.get("sentiment_label", "unknown"),
                },
            },
        }

    def _cache_market_data(self, db: Session, ticker: str, historical: List[Dict]):
        """Cache historical market data to database"""
        try:
            for data_point in historical[:10]:  # Cache last 10 days
                existing = (
                    db.query(MarketData)
                    .filter(
                        MarketData.ticker == ticker,
                        MarketData.timestamp == data_point.get("date"),
                        MarketData.source == data_point.get("source"),
                    )
                    .first()
                )

                if not existing:
                    market_record = MarketData(
                        ticker=ticker,
                        timestamp=data_point.get("date"),
                        open=data_point.get("open"),
                        high=data_point.get("high"),
                        low=data_point.get("low"),
                        close=data_point.get("close"),
                        volume=data_point.get("volume"),
                        source=data_point.get("source"),
                    )
                    db.add(market_record)

            db.commit()
            logger.info(f"Cached market data for {ticker}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cache market data for {ticker}: {e}")

    def _cache_sentiment_data(self, db: Session, ticker: str, sentiment: Dict):
        """Cache sentiment data to database"""
        try:
            # Cache Reddit sentiment
            reddit_data = sentiment.get("reddit", {})
            if reddit_data.get("mentions", 0) > 0:
                reddit_record = SentimentData(
                    ticker=ticker,
                    source="reddit",
                    sentiment_score=reddit_data.get("sentiment_score"),
                    mention_count=reddit_data.get("mentions"),
                    raw_data=reddit_data,
                )
                db.add(reddit_record)

            # Cache news sentiment
            news_data = sentiment.get("news", {})
            if news_data.get("article_count", 0) > 0:
                news_record = SentimentData(
                    ticker=ticker,
                    source="news",
                    sentiment_score=news_data.get("sentiment_score"),
                    mention_count=news_data.get("article_count"),
                    raw_data=news_data,
                )
                db.add(news_record)

            db.commit()
            logger.info(f"Cached sentiment data for {ticker}")
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to cache sentiment data for {ticker}: {e}")

    def get_watchlist_with_data(self, db: Session) -> List[Dict]:
        """
        Get all watchlist stocks with latest cached data

        Args:
            db: Database session

        Returns:
            List of watchlist items with latest prices and sentiment
        """
        watchlist = db.query(Watchlist).filter(Watchlist.active == True).all()

        results = []
        for stock in watchlist:
            # Get latest cached market data
            latest_market = (
                db.query(MarketData)
                .filter(MarketData.ticker == stock.ticker)
                .order_by(desc(MarketData.timestamp))
                .first()
            )

            # Get latest cached sentiment
            latest_sentiment = (
                db.query(SentimentData)
                .filter(SentimentData.ticker == stock.ticker)
                .order_by(desc(SentimentData.timestamp))
                .first()
            )

            results.append(
                {
                    "ticker": stock.ticker,
                    "company_name": stock.company_name,
                    "sector": stock.sector,
                    "tier": stock.tier,
                    "latest_price": float(latest_market.close) if latest_market else None,
                    "price_source": latest_market.source if latest_market else None,
                    "price_timestamp": (
                        latest_market.timestamp.isoformat() if latest_market else None
                    ),
                    "sentiment_score": (
                        float(latest_sentiment.sentiment_score) if latest_sentiment else None
                    ),
                    "sentiment_source": latest_sentiment.source if latest_sentiment else None,
                }
            )

        return results

    def refresh_all_data(self, db: Session) -> Dict:
        """
        Refresh data for all active watchlist stocks

        Args:
            db: Database session

        Returns:
            Summary of refresh operation
        """
        watchlist = db.query(Watchlist).filter(Watchlist.active == True).all()

        results = {"refreshed": 0, "failed": 0, "tickers": []}

        for stock in watchlist:
            try:
                self.get_comprehensive_analysis(stock.ticker, db)
                results["refreshed"] += 1
                results["tickers"].append({"ticker": stock.ticker, "status": "success"})
                logger.info(f"Refreshed data for {stock.ticker}")
            except Exception as e:
                results["failed"] += 1
                results["tickers"].append(
                    {"ticker": stock.ticker, "status": "failed", "error": str(e)}
                )
                logger.error(f"Failed to refresh {stock.ticker}: {e}")

        return results


# Singleton instance
data_aggregator = DataAggregatorService()
